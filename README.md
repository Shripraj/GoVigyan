<<<<<<< HEAD
[//]: # (# GoVigyan)

[//]: # ()
[//]: # (A comprehensive Flask-based web application for cattle and buffalo breed detection using AI, with features for research management and livestock inventory tracking.)

[//]: # ()
[//]: # (## Features)

[//]: # ()
[//]: # (### For Normal Users)

[//]: # (- 🐄 AI-powered breed detection for cattle and buffalo)

[//]: # (- 📊 View detection history)

[//]: # (- 📚 Access comprehensive breed information database)

[//]: # (- 📄 Browse approved research papers)

[//]: # ()
[//]: # (### For Research Users)

[//]: # (- All Normal User features plus:)

[//]: # (- 📤 Upload research papers for admin approval)

[//]: # (- 📦 Manage livestock inventory &#40;up to 100 breeds&#41;)

[//]: # (- 📈 Track daily milk production with analytics)

[//]: # (- 📥 Export inventory data to Excel)

[//]: # ()
[//]: # (### For Administrators)

[//]: # (- 👥 Manage user accounts)

[//]: # (- ✅ Approve/reject research submissions)

[//]: # (- 🗑️ Delete users &#40;except protected admin&#41;)

[//]: # (- 📊 Monitor system activity)

[//]: # ()
[//]: # (## Supported Breeds)

[//]: # ()
[//]: # (- Holstein &#40;Cattle&#41;)

[//]: # (- Jersey &#40;Cattle&#41;)

[//]: # (- Gir &#40;Cattle&#41;)

[//]: # (- Sahiwal &#40;Cattle&#41;)

[//]: # (- Murrah &#40;Buffalo&#41;)

[//]: # ()
[//]: # (## Installation)

[//]: # ()
[//]: # (### Prerequisites)

[//]: # (- Python 3.8 or higher)

[//]: # (- pip package manager)

[//]: # (- Google Cloud account &#40;for OAuth&#41;)

[//]: # ()
[//]: # (### Step 1: Clone/Download the Project)

[//]: # ()
[//]: # (```bash)

[//]: # (# Create project directory)

[//]: # (mkdir cattle-breed-detection)

[//]: # (cd cattle-breed-detection)

[//]: # (```)

[//]: # ()
[//]: # (### Step 2: Install Dependencies)

[//]: # ()
[//]: # (```bash)

[//]: # (pip install -r requirements.txt)

[//]: # (```)

[//]: # ()
[//]: # (### Step 3: Set Up Google OAuth)

[//]: # ()
[//]: # (1. Go to [Google Cloud Console]&#40;https://console.cloud.google.com/&#41;)

[//]: # (2. Create a new project or select existing one)

[//]: # (3. Enable Google+ API)

[//]: # (4. Navigate to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID")

[//]: # (5. Set Application type to "Web application")

[//]: # (6. Add Authorized redirect URIs:)

[//]: # (   - `http://localhost:5000/callback`)

[//]: # (   - `http://127.0.0.1:5000/callback`)

[//]: # (7. Copy your Client ID and Client Secret)

[//]: # (8. Open `app.py` and replace:)

[//]: # (   ```python)

[//]: # (   app.config['GOOGLE_CLIENT_ID'] = 'YOUR_GOOGLE_CLIENT_ID_HERE')

[//]: # (   app.config['GOOGLE_CLIENT_SECRET'] = 'YOUR_GOOGLE_CLIENT_SECRET_HERE')

[//]: # (   ```)

[//]: # ()
[//]: # (### Step 4: Project Structure)

[//]: # ()
[//]: # (Ensure your project has the following structure:)

[//]: # ()
[//]: # (```)

[//]: # (cattle-breed-detection/)

[//]: # (├── app.py)

[//]: # (├── requirements.txt)

[//]: # (├── README.md)

[//]: # (├── uploads/)

[//]: # (│   ├── detection/)

[//]: # (│   └── research/)

[//]: # (└── templates/)

[//]: # (    ├── base.html)

[//]: # (    ├── index.html)

[//]: # (    ├── login.html)

[//]: # (    ├── select_user_type.html)

[//]: # (    ├── normal_dashboard.html)

[//]: # (    ├── research_dashboard.html)

[//]: # (    ├── admin_dashboard.html)

[//]: # (    ├── breed_detection.html)

[//]: # (    ├── detection_history.html)

[//]: # (    ├── breed_info.html)

[//]: # (    ├── inventory.html)

[//]: # (    ├── upload_research.html)

[//]: # (    ├── research_history.html)

[//]: # (    └── approved_research.html)

[//]: # (```)

[//]: # ()
[//]: # (### Step 5: Run the Application)

[//]: # ()
[//]: # (```bash)

[//]: # (python app.py)

[//]: # (```)

[//]: # ()
[//]: # (The application will be available at: `http://localhost:5000`)

[//]: # ()
[//]: # (## Usage)

[//]: # ()
[//]: # (### First Time Login)

[//]: # ()
[//]: # (1. Visit `http://localhost:5000`)

[//]: # (2. Click "Start Breed Detection")

[//]: # (3. Sign in with Google)

[//]: # (4. Select your account type:)

[//]: # (   - **Normal User**: For basic breed detection)

[//]: # (   - **Research & Inventory**: For research and livestock management)

[//]: # ()
[//]: # (### Admin Access)

[//]: # ()
[//]: # (The email `patilshridhar1301@gmail.com` is automatically granted admin privileges.)

[//]: # ()
[//]: # (### Breed Detection)

[//]: # ()
[//]: # (1. Navigate to "Breed Detection" from dashboard)

[//]: # (2. Upload an image of cattle or buffalo)

[//]: # (3. Click "Detect Breed")

[//]: # (4. View breed information and confidence score)

[//]: # ()
[//]: # (### Inventory Management &#40;Research Users Only&#41;)

[//]: # ()
[//]: # (1. Go to "Inventory Management")

[//]: # (2. Click "Add Breed" and enter:)

[//]: # (   - Breed name)

[//]: # (   - Milk capacity)

[//]: # (3. Add daily milk production records)

[//]: # (4. View analytics automatically)

[//]: # (5. Download data as Excel file)

[//]: # ()
[//]: # (### Research Upload &#40;Research Users Only&#41;)

[//]: # ()
[//]: # (1. Navigate to "Upload Research")

[//]: # (2. Fill in title and description)

[//]: # (3. Upload PDF/DOC/DOCX file)

[//]: # (4. Submit for admin approval)

[//]: # ()
[//]: # (### Admin Functions)

[//]: # ()
[//]: # (1. View all registered users in "Users" tab)

[//]: # (2. Review pending research in "Pending Research" tab)

[//]: # (3. Approve or reject submissions)

[//]: # (4. Delete user accounts &#40;except protected admin&#41;)

[//]: # ()
[//]: # (## Database)

[//]: # ()
[//]: # (The application uses SQLite database &#40;`cattle_breed.db`&#41; which is created automatically on first run.)

[//]: # ()
[//]: # (### Database Models)

[//]: # ()
[//]: # (- **User**: User accounts and authentication)

[//]: # (- **Detection**: Breed detection history)

[//]: # (- **Inventory**: Livestock inventory records)

[//]: # (- **Research**: Research paper submissions)

[//]: # (- **BreedInfo**: Breed information database)

[//]: # ()
[//]: # (## Integrating Your ML Model)

[//]: # ()
[//]: # (The current implementation uses a mock detection function. To integrate your trained model:)

[//]: # ()
[//]: # (1. Train your model on cattle/buffalo breeds)

[//]: # (2. Save the model &#40;e.g., `model.h5`&#41;)

[//]: # (3. Replace the `mock_detect_breed&#40;&#41;` function in `app.py`:)

[//]: # ()
[//]: # (```python)

[//]: # (def detect_breed_with_model&#40;image_path&#41;:)

[//]: # (    # Load your trained model)

[//]: # (    model = keras.models.load_model&#40;'path/to/your/model.h5'&#41;)

[//]: # (    )
[//]: # (    # Preprocess image)

[//]: # (    img = Image.open&#40;image_path&#41;)

[//]: # (    img = img.resize&#40;&#40;224, 224&#41;&#41;)

[//]: # (    img_array = np.array&#40;img&#41; / 255.0)

[//]: # (    img_array = np.expand_dims&#40;img_array, axis=0&#41;)

[//]: # (    )
[//]: # (    # Predict)

[//]: # (    predictions = model.predict&#40;img_array&#41;)

[//]: # (    breed_classes = ['Holstein', 'Jersey', 'Gir', 'Sahiwal', 'Murrah'])

[//]: # (    predicted_index = np.argmax&#40;predictions[0]&#41;)

[//]: # (    )
[//]: # (    return {)

[//]: # (        'breed': breed_classes[predicted_index],)

[//]: # (        'confidence': float&#40;predictions[0][predicted_index]&#41;)

[//]: # (    })

[//]: # (```)

[//]: # ()
[//]: # (## Security Considerations)

[//]: # ()
[//]: # (### For Production Deployment:)

[//]: # ()
[//]: # (1. **Change Secret Key**: Update `SECRET_KEY` in `app.py` to a strong random string)

[//]: # (2. **Use Environment Variables**: Store sensitive configuration in environment variables)

[//]: # (3. **Enable HTTPS**: Use SSL/TLS certificates)

[//]: # (4. **Database**: Switch from SQLite to PostgreSQL/MySQL)

[//]: # (5. **WSGI Server**: Use Gunicorn or uWSGI instead of Flask development server)

[//]: # (6. **Reverse Proxy**: Set up nginx or Apache)

[//]: # (7. **Rate Limiting**: Implement rate limiting for uploads)

[//]: # (8. **CSRF Protection**: Enable CSRF tokens)

[//]: # (9. **File Validation**: Add strict file type validation)

[//]: # (10. **Backup**: Set up automated database backups)

[//]: # ()
[//]: # (### Production Deployment Example)

[//]: # ()
[//]: # (```bash)

[//]: # (# Install Gunicorn)

[//]: # (pip install gunicorn)

[//]: # ()
[//]: # (# Run with Gunicorn)

[//]: # (gunicorn -w 4 -b 0.0.0.0:8000 app:app)

[//]: # (```)

[//]: # ()
[//]: # (## Customization)

[//]: # ()
[//]: # (### Adding More Breeds)

[//]: # ()
[//]: # (Edit the `BREED_INFO` dictionary in `app.py`:)

[//]: # ()
[//]: # (```python)

[//]: # (BREED_INFO = {)

[//]: # (    'YourBreed': {)

[//]: # (        'description': 'Description here',)

[//]: # (        'origin': 'Origin location',)

[//]: # (        'avg_milk_production': 0000,)

[//]: # (        'characteristics': 'Key characteristics')

[//]: # (    })

[//]: # (})

[//]: # (```)

[//]: # ()
[//]: # (### Changing File Upload Limits)

[//]: # ()
[//]: # (Edit in `app.py`:)

[//]: # ()
[//]: # (```python)

[//]: # (app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB)

[//]: # (```)

[//]: # ()
[//]: # (### Modifying Inventory Limit)

[//]: # ()
[//]: # (Change in the `add_inventory&#40;&#41;` function in `app.py`:)

[//]: # ()
[//]: # (```python)

[//]: # (if count >= 100:  # Change 100 to your desired limit)

[//]: # (```)

[//]: # ()
[//]: # (## Troubleshooting)

[//]: # ()
[//]: # (### Google OAuth Not Working)

[//]: # (- Verify redirect URIs match exactly in Google Cloud Console)

[//]: # (- Check Client ID and Secret are correct)

[//]: # (- Ensure Google+ API is enabled)

[//]: # ()
[//]: # (### Database Errors)

[//]: # (- Delete `cattle_breed.db` and restart application)

[//]: # (- Check file permissions on upload folders)

[//]: # ()
[//]: # (### Import Errors)

[//]: # (- Ensure all dependencies are installed: `pip install -r requirements.txt`)

[//]: # (- Check Python version is 3.8+)

[//]: # ()
[//]: # (### File Upload Issues)

[//]: # (- Verify `uploads/` folders exist and have write permissions)

[//]: # (- Check file size doesn't exceed `MAX_CONTENT_LENGTH`)

[//]: # ()
[//]: # (## Support)

[//]: # ()
[//]: # (For issues or questions:)

[//]: # (- Check the troubleshooting section)

[//]: # (- Review error logs in console)

[//]: # (- Ensure all setup steps were followed correctly)

[//]: # ()
[//]: # (## License)

[//]: # ()
[//]: # (This project is provided as-is for educational and commercial use.)

[//]: # ()
[//]: # (## Admin Contact)

[//]: # ()
[//]: # (Protected admin email: patilshridhar1301@gmail.com)
=======
# GoVigyan
It detects the breed of the cows and buffalo with 75% - 80% of accuracy .
>>>>>>> 369e7b687286e46a3d576ef68ecffa15bf75ecaf
