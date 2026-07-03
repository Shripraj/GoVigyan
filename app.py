import os
import json
from datetime import datetime
from io import BytesIO

from flask import (
    Flask, render_template, redirect, url_for, session,
    request, jsonify, send_file, flash, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import numpy as np
import cv2
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
# Try importing TensorFlow
try:
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except Exception:
    load_model = None
    TF_AVAILABLE = False


# ---------------------------------------------------------------
# BASIC CONFIG
# ---------------------------------------------------------------
BASE_DIR = os.path.abspath(os.getcwd())
app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("GOVIGYAN_SECRET")

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "Flask SECRET_KEY is missing. "
        "Please set GOVIGYAN_SECRET as an environment variable."
    )
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    BASE_DIR, "instance", "govigyan.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload folders
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB

os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "detection"), exist_ok=True)
os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "research"), exist_ok=True)


# ---------------------------------------------------------------
# GOOGLE OAUTH CONFIG
# ---------------------------------------------------------------
app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET")

if not app.config["GOOGLE_CLIENT_ID"] or not app.config["GOOGLE_CLIENT_SECRET"]:
    raise RuntimeError(
        "Google OAuth credentials are missing. "
        "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
    )

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_selection"
oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# ---------------------------------------------------------------
# JINJA FILTER
# ---------------------------------------------------------------
def jinja_from_json(s):
    try:
        if not s:
            return []
        if isinstance(s, (list, dict)):
            return s
        return json.loads(s)
    except Exception:
        return []

app.jinja_env.filters["from_json"] = jinja_from_json


# ---------------------------------------------------------------
# DATABASE MODELS
# ---------------------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    password_hash = db.Column(db.String(255), nullable=True)
    user_type = db.Column(db.String(50), default="normal")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detections = db.relationship("Detection", backref="user", lazy=True, cascade="all, delete-orphan")
    researches = db.relationship("Research", backref="user", lazy=True, cascade="all, delete-orphan")
    inventories = db.relationship("Inventory", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, pw)


class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_path = db.Column(db.String(400))
    breed_name = db.Column(db.String(150))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Research(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(300))
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    status = db.Column(db.String(50), default="pending")
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    breed_name = db.Column(db.String(150))
    milk_capacity = db.Column(db.Float, default=0.0)
    daily_records = db.Column(db.Text, default="[]")  # JSON list


# ---------------------------------------------------------------
# MODEL & LABEL LOADING
# ---------------------------------------------------------------
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATHS_TO_TRY = [
    os.path.join(MODEL_DIR, "breed_model.keras"),
    os.path.join(MODEL_DIR, "breed_model.h5"),
    os.path.join(MODEL_DIR, "model.keras"),
    os.path.join(MODEL_DIR, "model.h5"),
]

LABELS_PATH = os.path.join(MODEL_DIR, "class_names.json")

model = None
INV_LABELS = {}
INPUT_SIZE = 160
CLASS_COUNT = 0


def load_model_safe():
    """Safely load model + labels without crashing."""
    global model, INV_LABELS, CLASS_COUNT

    # Load labels safely (handles A/B/C formats)
    INV_LABELS.clear()

    if os.path.exists(LABELS_PATH):
        try:
            with open(LABELS_PATH, "r", encoding="utf-8") as f:
                labels = json.load(f)

            if isinstance(labels, list):
                # Format C: list of names
                INV_LABELS.update({i: labels[i] for i in range(len(labels))})

            elif isinstance(labels, dict):
                # Try format A or B
                new_map = {}
                for k, v in labels.items():
                    try:
                        # format A: {"0": "Holstein", ...}
                        new_map[int(k)] = v
                    except:
                        try:
                            # format B: {"Holstein": 0, ...}
                            new_map[int(v)] = k
                        except:
                            pass
                INV_LABELS.update(new_map)

        except Exception as e:
            print("Label load error:", e)

    CLASS_COUNT = len(INV_LABELS)

    # Load model
    if TF_AVAILABLE:
        for path in MODEL_PATHS_TO_TRY:
            if os.path.exists(path):
                try:
                    model = load_model(path, compile=False)
                    print("MODEL LOADED:", path)
                    return
                except Exception as e:
                    print("Failed loading", path, e)

    print("⚠ Model NOT loaded.")


load_model_safe()
# ---------------------------------------------------------------
# BREED INFO (FULL + CLEANED)
# ---------------------------------------------------------------
BREED_INFO = {
    "Ayrshire cattle": {
        "description": "A high-quality dairy cattle breed known for consistent milk yield.",
        "origin": "Scotland",
        "avg_milk_production": 6000,
        "characteristics": "Red & white coat, hardy, efficient grazer",
        "can be breeded with": "Holstein Friesian (for higher yield),Brown Swiss (for milk quality + strength)"
    },
    "Brown Swiss cattle": {
        "description": "One of the oldest dairy cattle breeds with very high milk quality.",
        "origin": "Switzerland",
        "avg_milk_production": 7000,
        "characteristics": "Brown coat, strong frame, calm temperament"
    },
    "Chhattisgarhi": {
        "description": "Indigenous cattle breed adapted to hot and humid climates.",
        "origin": "Chhattisgarh, India",
        "avg_milk_production": 350,
        "characteristics": "Medium build, hardy, drought tolerant"
    },
    "Holstein Friesian cattle": {
        "description": "World’s highest milk-producing dairy breed.",
        "origin": "Netherlands",
        "avg_milk_production": 8000,
        "characteristics": "Black and white coat, large frame"
    },
    "Jaffarabadi": {
        "description": "A large, heavy buffalo breed known for high milk yield.",
        "origin": "Gujarat, India",
        "avg_milk_production": 2500,
        "characteristics": "Massive body, strong horns, robust"
    },
    "Jersey cattle": {
        "description": "Famous dairy breed known for very high butterfat percentage.",
        "origin": "Jersey (Channel Islands)",
        "avg_milk_production": 4500,
        "characteristics": "Fawn coat, docile, heat tolerant"
    },
    "Red Dane cattle": {
        "description": "A dairy breed known for strong health and good milk yield.",
        "origin": "Denmark",
        "avg_milk_production": 5500,
        "characteristics": "Red coat, sturdy build"
    },
    "banni": {
        "description": "A hardy Indian buffalo breed famous for drought resistance.",
        "origin": "Kutch, Gujarat",
        "avg_milk_production": 2500,
        "characteristics": "Black, robust, heat tolerant"
    },
    "bargur": {
        "description": "A draught cattle breed used for farming in hilly regions.",
        "origin": "Tamil Nadu, India",
        "avg_milk_production": 400,
        "characteristics": "Reddish-brown, fast, active"
    },
    "bhadwari": {
        "description": "Buffalo breed known for high butterfat percentage in milk.",
        "origin": "Uttar Pradesh & Madhya Pradesh",
        "avg_milk_production": 1800,
        "characteristics": "Copper brown, compact body"
    },
    "chilika": {
        "description": "Indigenous cattle breed found near Chilika Lake.",
        "origin": "Odisha, India",
        "avg_milk_production": 350,
        "characteristics": "Small, hardy, adapted to wetland areas"
    },
    "gojri": {
        "description": "Buffalo breed raised by the Gujjar community.",
        "origin": "Jammu & Kashmir / Himachal",
        "avg_milk_production": 2000,
        "characteristics": "Strong, adapted to hilly terrain"
    },
    "kalahandi": {
        "description": "Native cattle breed from tribal regions.",
        "origin": "Odisha, India",
        "avg_milk_production": 300,
        "characteristics": "Small body, hardy, disease resistant"
    },
    "luit": {
        "description": "A regional cattle breed found near the Brahmaputra valley.",
        "origin": "Assam, India",
        "avg_milk_production": 300,
        "characteristics": "Small to medium size, heat tolerant"
    },
    "marathwada": {
        "description": "Multipurpose breed adapted to dry climatic conditions.",
        "origin": "Maharashtra, India",
        "avg_milk_production": 400,
        "characteristics": "Hardy, strong, agricultural use"
    },
    "mehsana": {
        "description": "A major Indian buffalo breed with excellent milk yield.",
        "origin": "Gujarat, India",
        "avg_milk_production": 2200,
        "characteristics": "Long face, strong build"
    },
    "murrah": {
        "description": "India’s highest milk-yielding buffalo breed.",
        "origin": "Haryana & Punjab",
        "avg_milk_production": 2700,
        "characteristics": "Jet black, curled horns, compact body"
    },
    "nagpuri": {
        "description": "Heat-tolerant buffalo breed from the Vidarbha region.",
        "origin": "Maharashtra, India",
        "avg_milk_production": 1500,
        "characteristics": "Straight horns, adapted to extreme heat"
    },
    "nili-ravi": {
        "description": "High-yielding buffalo breed also called 'Black Gold'.",
        "origin": "Punjab (India & Pakistan)",
        "avg_milk_production": 2500,
        "characteristics": "Dark color, strong frame"
    },
    "pandharpuri": {
        "description": "Buffalo breed with unique long, twisted horns.",
        "origin": "Maharashtra, India",
        "avg_milk_production": 1500,
        "characteristics": "Very long horns, good adaptability"
    },
    "surti": {
        "description": "Medium-yield buffalo breed known for gentle nature.",
        "origin": "Gujarat, India",
        "avg_milk_production": 1800,
        "characteristics": "Sickle-shaped horns, compact"
    },
    "toda": {
        "description": "Rare cattle breed from Nilgiri hills raised by Toda tribe.",
        "origin": "Tamil Nadu, India",
        "avg_milk_production": 300,
        "characteristics": "Distinctive markings, small & hardy"
    }
}


# ---------------------------------------------------------------
# IMAGE PREPROCESSING
# ---------------------------------------------------------------
def preprocess_for_model(image_path):
    if not os.path.exists(image_path):
        return None

    img = cv2.imread(image_path)
    if img is None:
        return None

    try:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
        img = img.astype("float32") / 255.0
        return np.expand_dims(img, axis=0)

    except Exception as e:
        app.logger.error("Preprocess error: %s", e)
        return None
# ---------------------------
# UNKNOWN IMAGE DETECTION (Reject non-cattle images)
# ---------------------------
def is_cow_or_buffalo_image(image_path):
    """
    Detects whether the image contains a large quadruped animal shape.
    Prevents random predictions for non-cattle images.
    """
    img = cv2.imread(image_path)
    if img is None:
        return False

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    # Edge detection
    edges = cv2.Canny(blur, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = gray.shape[:2]
    min_area = (h * w) * 0.10  # object must be at least 10% of the total area

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        x, y, w_box, h_box = cv2.boundingRect(c)
        aspect = w_box / h_box

        # Cows/Buffaloes have aspect ratio between 1–3
        if 0.6 < aspect < 3.5:
            return True

    return False


# ---------------------------------------------------------------
# PREDICTION
# ---------------------------------------------------------------
def predict_breed_local(image_path, top_k=3):
    UNKNOWN_THRESHOLD = 0.60  # Confidence below this = UNKNOWN

    if model is None or not INV_LABELS:
        return {"breed": "Model not loaded", "confidence": 0.0, "top": []}

    inp = preprocess_for_model(image_path)
    if inp is None:
        return {"breed": "Invalid Image", "confidence": 0.0, "top": []}

    try:
        preds = model.predict(inp)[0]
        preds = np.asarray(preds, dtype=float)

        # Sort highest → lowest confidence
        top_idxs = preds.argsort()[-top_k:][::-1]
        top_list = [(INV_LABELS[i], float(preds[i])) for i in top_idxs]

        best_idx = top_idxs[0]
        best_name = INV_LABELS.get(int(best_idx), "Unknown")
        best_conf = float(preds[best_idx])

        # -----------------------------
        # STRONG UNKNOWN DETECTION
        # -----------------------------

        # 1. Low confidence → UNKNOWN
        if best_conf < UNKNOWN_THRESHOLD:
            return {
                "breed": "Unknown",
                "confidence": best_conf,
                "top": top_list
            }

        # 2. Labels like "other", "invalid"
        if best_name.lower() in ("other", "invalid", "background"):
            return {
                "breed": "Unknown",
                "confidence": best_conf,
                "top": top_list
            }

        return {
            "breed": best_name,
            "confidence": best_conf,
            "top": top_list
        }

    except Exception as e:
        app.logger.error("Prediction error: %s", e)
        return {"breed": "Error", "confidence": 0.0, "top": []}

# ---------------------------------------------------------------
# LOGIN MANAGER
# ---------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None


# ---------------------------------------------------------------
# AUTH ROUTES (LOGIN / SIGNUP / GOOGLE)
# ---------------------------------------------------------------

# Ensure endpoint "login" exists (templates use url_for('login'))
@app.route("/login", endpoint="login")
def login():
    return redirect(url_for("login_selection"))


@app.route("/login-selection")
def login_selection():
    return render_template("login_selection.html")


@app.route("/login-normal")
def login_normal_page():
    return render_template("login_normal.html")


@app.route("/login-research")
def login_research_page():
    return render_template("login_research.html")


@app.route("/login-admin")
def login_admin_page():
    return render_template("login_admin.html")


@app.route("/admin-auth", methods=["POST"])
def admin_auth():
    return redirect(url_for("google_admin_login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name")
    email = request.form.get("email", "").lower()
    password = request.form.get("password")
    user_type = request.form.get("user_type", "normal")

    if not name or not email or not password:
        flash("Fill all fields", "warning")
        return redirect(url_for("signup"))

    if User.query.filter_by(email=email).first():
        flash("Email already exists", "danger")
        return redirect(url_for("login_selection"))

    if user_type == "admin" and email != "admin email id":
        flash("Admin signup restricted", "danger")
        return redirect(url_for("signup"))

    user = User(name=name, email=email, user_type=user_type)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    login_user(user)
    return redirect(url_for("dashboard"))


@app.route("/login-normal-auth", methods=["POST"])
def login_normal_auth():
    email = request.form.get("email", "").lower()
    password = request.form.get("password")

    user = User.query.filter_by(email=email, user_type="normal").first()

    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for("normal_dashboard"))

    flash("Invalid login", "danger")
    return redirect(url_for("login_normal_page"))


@app.route("/login-research-auth", methods=["POST"])
def login_research_auth():
    email = request.form.get("email", "").lower()
    password = request.form.get("password")

    user = User.query.filter_by(email=email, user_type="research").first()

    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for("research_dashboard"))

    flash("Invalid login", "danger")
    return redirect(url_for("login_research_page"))
# ---------------------------------------------------------------
# GOOGLE LOGIN (Normal Users)
# ---------------------------------------------------------------
@app.route("/google-login")
def google_login():
    next_type = request.args.get("next", "normal")
    session["google_next"] = next_type

    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/callback")
def google_callback():
    try:
        token = google.authorize_access_token()
        info = token.get("userinfo") or token

        email = (info.get("email") or "").lower()
        name = info.get("name") or (email.split("@")[0] if email else "Google User")

        if not email:
            flash("Google login failed", "danger")
            return redirect(url_for("login_selection"))

        # prevent researchers/admin logging incorrectly
        if email == "patilshridhar1301@gmail.com":
            flash("Use Admin Login button", "warning")
            return redirect(url_for("login_selection"))

        user = User.query.filter_by(email=email).first()

        # First-time login
        if not user:
            requested_type = session.pop("google_next", None)

            if requested_type not in ("normal", "research"):
                # ask user to pick type
                session["pending_user"] = {"email": email, "name": name}
                return redirect(url_for("select_user_type"))

            user = User(email=email, name=name, user_type=requested_type)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash("Logged in successfully!", "success")
        return redirect(url_for("dashboard"))

    except Exception as e:
        app.logger.error("Google login error: %s", e)
        flash("Google login error", "danger")
        return redirect(url_for("login_selection"))


# ---------------------------------------------------------------
# GOOGLE LOGIN (ADMIN)
# ---------------------------------------------------------------
@app.route("/google-admin-login")
def google_admin_login():
    redirect_uri = url_for("google_admin_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/google-admin-callback")
def google_admin_callback():
    try:
        token = google.authorize_access_token()
        info = token.get("userinfo") or token

        email = (info.get("email") or "").lower()
        name = info.get("name") or "Admin"

        if email != "patilshridhar1301@gmail.com":
            flash("Not authorized as admin", "danger")
            return redirect(url_for("login_selection"))

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, name=name, user_type="admin")
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash("Admin logged in", "success")
        return redirect(url_for("admin_dashboard"))

    except Exception as e:
        app.logger.error("Admin login error: %s", e)
        flash("Admin login failed", "danger")
        return redirect(url_for("login_selection"))


# ---------------------------------------------------------------
# SELECT USER TYPE (Google First Login)
# ---------------------------------------------------------------
@app.route("/select-user-type", methods=["GET", "POST"])
def select_user_type():
    pending = session.get("pending_user")
    if not pending:
        return redirect(url_for("login_selection"))

    if request.method == "GET":
        return render_template("select_user_type.html", pending=pending)

    chosen = request.form.get("user_type", "normal")
    data = session.pop("pending_user")

    if chosen == "admin" and data["email"] != "patilshridhar1301@gmail.com":
        chosen = "normal"  # safety fallback

    user = User(email=data["email"], name=data["name"], user_type=chosen)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out!", "info")
    return redirect(url_for("login_selection"))


# ---------------------------------------------------------------
# MAIN DASHBOARD ROUTING
# ---------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.user_type == "admin":
        return redirect(url_for("admin_dashboard"))
    if current_user.user_type == "research":
        return redirect(url_for("research_dashboard"))
    return redirect(url_for("normal_dashboard"))


@app.route("/normal-dashboard")
@login_required
def normal_dashboard():
    return render_template("normal_dashboard.html")


@app.route("/research-dashboard")
@login_required
def research_dashboard():
    return render_template("research_dashboard.html")


@app.route("/admin-dashboard")
@login_required
def admin_dashboard():
    if current_user.user_type != "admin":
        return redirect(url_for("dashboard"))

    users = User.query.all()
    pending = Research.query.filter_by(status="pending").order_by(Research.uploaded_at.desc()).all()

    return render_template("admin_dashboard.html", users=users, pending_research=pending)


# ---------------------------------------------------------------
# BREED DETECTION PAGES
# ---------------------------------------------------------------
@app.route("/breed-detection")
@login_required
def breed_detection():
    return render_template("breed_detection.html")


@app.route("/detect-breed", methods=["POST"])
@login_required
def detect_breed():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}")
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], "detection", filename)
    file.save(save_path)

    result = predict_breed_local(save_path)

    breed = result.get("breed")
    confidence = float(result.get("confidence", 0))
    top_preds = result.get("top", [])

    # Save history
    det = Detection(
        user_id=current_user.id,
        image_path=save_path,
        breed_name=breed,
        confidence=confidence,
    )
    db.session.add(det)
    db.session.commit()

    info = BREED_INFO.get(breed, {})
    return jsonify({
        "breed": breed,
        "confidence": confidence,
        "info": info,
        "top": top_preds
    })
# ---------------------------------------------------------------
# DETECTION HISTORY
# ---------------------------------------------------------------
@app.route("/detection-history")
@login_required
def detection_history():
    detections = Detection.query.filter_by(
        user_id=current_user.id
    ).order_by(Detection.timestamp.desc()).all()

    return render_template("detection_history.html", detections=detections)


@app.route("/delete-detection/<int:det_id>", methods=["POST"])
@login_required
def delete_detection(det_id):
    d = Detection.query.get_or_404(det_id)

    if d.user_id != current_user.id and current_user.user_type != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        if d.image_path and os.path.exists(d.image_path):
            os.remove(d.image_path)
    except:
        pass

    db.session.delete(d)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/delete-all-detections", methods=["POST"])
@login_required
def delete_all_detections():
    detections = Detection.query.filter_by(user_id=current_user.id).all()
    for d in detections:
        try:
            if d.image_path and os.path.exists(d.image_path):
                os.remove(d.image_path)
        except:
            pass
        db.session.delete(d)

    db.session.commit()
    return jsonify({"success": True})


# ---------------------------------------------------------------
# UPLOAD RESEARCH
# ---------------------------------------------------------------
@app.route("/upload-research")
@login_required
def upload_research_page():
    if current_user.user_type != "research":
        return redirect(url_for("dashboard"))
    return render_template("upload_research.html")


@app.route("/upload-research", methods=["POST"])
@login_required
def upload_research():
    if current_user.user_type != "research":
        return jsonify({"error": "Unauthorized"}), 403

    title = request.form.get("title")
    description = request.form.get("description")
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(
        f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    )
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], "research", filename)
    file.save(save_path)

    r = Research(
        user_id=current_user.id,
        title=title,
        description=description,
        file_path=save_path,
        status="pending",
    )
    db.session.add(r)
    db.session.commit()

    return jsonify({"success": True})


# ---------------------------------------------------------------
# RESEARCH HISTORY
# ---------------------------------------------------------------
@app.route("/research-history")
@login_required
def research_history():
    if current_user.user_type != "research":
        return redirect(url_for("dashboard"))

    researches = Research.query.filter_by(
        user_id=current_user.id
    ).order_by(Research.uploaded_at.desc()).all()

    return render_template("research_history.html", researches=researches)


# ---------------------------------------------------------------
# RESEARCH APPROVAL (ADMIN)
# ---------------------------------------------------------------
@app.route("/approve-research/<int:rid>", methods=["POST"])
@login_required
def approve_research(rid):
    if current_user.user_type != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    r = Research.query.get_or_404(rid)
    r.status = "approved"
    r.approved_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/reject-research/<int:rid>", methods=["POST"])
@login_required
def reject_research(rid):
    if current_user.user_type != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    r = Research.query.get_or_404(rid)
    r.status = "rejected"
    db.session.commit()
    return jsonify({"success": True})


@app.route("/delete-research/<int:rid>", methods=["POST"])
@login_required
def delete_research(rid):
    r = Research.query.get_or_404(rid)

    if r.user_id != current_user.id and current_user.user_type != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        if r.file_path and os.path.exists(r.file_path):
            os.remove(r.file_path)
    except:
        pass

    db.session.delete(r)
    db.session.commit()

    return jsonify({"success": True})


@app.route("/view-approved-research")
@login_required
def view_approved_research():
    approved = Research.query.filter_by(status="approved").order_by(
        Research.approved_at.desc()
    ).all()

    return render_template("approved_research.html", researches=approved)


# ---------------------------------------------------------------
# INVENTORY MANAGEMENT
# ---------------------------------------------------------------
@app.route("/inventory", endpoint="inventory_page")
@login_required
def inventory_page():
    if current_user.user_type != "research":
        return redirect(url_for("dashboard"))

    invs = Inventory.query.filter_by(user_id=current_user.id).all()
    records_map = {}

    for inv in invs:
        try:
            records_map[inv.id] = json.loads(inv.daily_records or "[]")
        except:
            records_map[inv.id] = []

    return render_template(
        "inventory.html",
        inventories=invs,
        records_map=records_map
    )


@app.route("/add-inventory", methods=["POST"])
@login_required
def add_inventory():
    if current_user.user_type != "research":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)
    breed_name = data.get("breed_name")
    milk_capacity = float(data.get("milk_capacity", 0.0))

    inv = Inventory(
        user_id=current_user.id,
        breed_name=breed_name,
        milk_capacity=milk_capacity,
        daily_records=json.dumps([])
    )

    db.session.add(inv)
    db.session.commit()

    return jsonify({"success": True, "id": inv.id})


@app.route("/add-daily-milk/<int:inv_id>", methods=["POST"])
@login_required
def add_daily_milk(inv_id):
    inv = Inventory.query.get_or_404(inv_id)

    if inv.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)
    milk = float(data.get("milk_produced", 0.0))

    records = json.loads(inv.daily_records or "[]")
    records.append({
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "milk_produced": milk
    })
    inv.daily_records = json.dumps(records)
    db.session.commit()

    total = sum(r["milk_produced"] for r in records)
    avg = total / len(records) if records else 0
    util = (avg / inv.milk_capacity * 100) if inv.milk_capacity else 0

    return jsonify({
        "success": True,
        "analysis": {
            "total_records": len(records),
            "total_milk": total,
            "average_milk": avg,
            "capacity_utilization": util
        }
    })


@app.route("/delete-inventory/<int:inv_id>", methods=["POST"])
@login_required
def delete_inventory(inv_id):
    inv = Inventory.query.get_or_404(inv_id)

    if inv.user_id != current_user.id and current_user.user_type != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(inv)
    db.session.commit()

    return jsonify({"success": True})
# ---------------------------------------------------------------
# DOWNLOAD INVENTORY (Excel)
# ---------------------------------------------------------------
@app.route("/download-inventory", endpoint="download_inventory")
@login_required
def download_inventory():
    if current_user.user_type != "research":
        return jsonify({"error": "Unauthorized"}), 403

    rows = []
    invs = Inventory.query.filter_by(user_id=current_user.id).all()

    for inv in invs:
        recs = json.loads(inv.daily_records or "[]")
        for r in recs:
            rows.append({
                "Breed": inv.breed_name,
                "Capacity": inv.milk_capacity,
                "Date": r["date"],
                "Milk": r["milk_produced"]
            })

    df = pd.DataFrame(rows)
    out = BytesIO()

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventory")

    out.seek(0)
    return send_file(out, as_attachment=True, download_name="inventory.xlsx")


# ---------------------------------------------------------------
# ADMIN — DELETE USER
# ---------------------------------------------------------------
@app.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.user_type != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get_or_404(user_id)

    if user.email == "patilshridhar1301@gmail.com":
        return jsonify({"error": "Cannot delete main admin"}), 403

    db.session.delete(user)
    db.session.commit()

    return jsonify({"success": True})


# ---------------------------------------------------------------
# BREED INFO PAGE
# ---------------------------------------------------------------
@app.route("/breed-info")
@login_required
def breed_info_page():
    return render_template("breed_info.html", breeds=BREED_INFO)


@app.route("/breed-info/<breed>")
@login_required
def breed_info(breed):
    info = BREED_INFO.get(
        breed,
        {
            "description": "No info available.",
            "origin": "",
            "avg_milk_production": 0,
            "characteristics": "",
        },
    )

    return render_template(
        "breed_info.html",
        breed=breed,
        info=info
    )


# ---------------------------------------------------------------
# SERVE UPLOADED FILES
# ---------------------------------------------------------------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---------------------------------------------------------------
# ADMIN TOOL — RELOAD MODEL AT RUNTIME
# ---------------------------------------------------------------
@app.route("/reload-model", methods=["POST"])
@login_required
def reload_model():
    if current_user.user_type != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    load_model_safe()

    return jsonify({
        "success": True,
        "loaded": model is not None,
        "classes": len(INV_LABELS)
    })


# ---------------------------------------------------------------
# STARTUP — CREATE DB AND RUN APP
# ---------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
