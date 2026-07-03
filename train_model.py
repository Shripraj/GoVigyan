import os
import json
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# --------------------------------------------
# CONFIG
# --------------------------------------------
DATASET_DIR = "dataset"
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")

MODEL_DIR = "model"
os.makedirs(MODEL_DIR, exist_ok=True)

IMG_SIZE = 160
BATCH = 32
EPOCHS = 35

# --------------------------------------------
# DATA GENERATORS
# --------------------------------------------
train_gen = ImageDataGenerator(
    rescale=1/255.0,
    rotation_range=25,
    zoom_range=0.25,
    width_shift_range=0.25,
    height_shift_range=0.25,
    shear_range=0.15,
    horizontal_flip=True,
    fill_mode="nearest"
)

val_gen = ImageDataGenerator(rescale=1/255.0)

train_data = train_gen.flow_from_directory(
    TRAIN_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH,
    class_mode="categorical"
)

val_data = val_gen.flow_from_directory(
    VAL_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH,
    class_mode="categorical"
)

# Save class labels
labels = train_data.class_indices
with open(os.path.join(MODEL_DIR, "class_names.json"), "w") as f:
    json.dump(labels, f, indent=2)

print("Class mapping:", labels)

# --------------------------------------------
# MODEL
# --------------------------------------------
base = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)

# Freeze first 100 layers
for layer in base.layers[:100]:
    layer.trainable = False
for layer in base.layers[100:]:
    layer.trainable = True

x = base.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.4)(x)
x = Dense(256, activation="relu")(x)
x = Dropout(0.4)(x)
preds = Dense(len(labels), activation="softmax")(x)

model = Model(inputs=base.input, outputs=preds)

model.compile(
    optimizer=Adam(1e-4),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# --------------------------------------------
# CALLBACKS
# --------------------------------------------
callbacks = [
    EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
    ModelCheckpoint(os.path.join(MODEL_DIR, "best_model.h5"),
                    monitor="val_loss",
                    save_best_only=True)
]

# --------------------------------------------
# TRAIN
# --------------------------------------------
model.fit(
    train_data,
    validation_data=val_data,
    epochs=EPOCHS,
    callbacks=callbacks
)

# --------------------------------------------
# SAVE FINAL MODEL
# --------------------------------------------
model.save(os.path.join(MODEL_DIR, "breed_model.h5"))
print("Model saved successfully!")
