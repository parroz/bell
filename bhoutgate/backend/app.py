from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session, send_file
import os
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__, 
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'static')),
    static_url_path='/static'
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Ensure config directory exists
os.makedirs(app.static_folder, exist_ok=True)

# Load settings from file
def load_settings():
    try:
        with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json'), 'r') as f:
            settings = json.load(f)
            # Ensure all required settings exist
            if 'video_path' not in settings:
                settings['video_path'] = os.path.join(app.static_folder, 'video.mp4')
            if 'mqtt_publish_topic' not in settings:
                settings['mqtt_publish_topic'] = 'bhoutgate/access'
            if 'mqtt_subscribe_topic' not in settings:
                settings['mqtt_subscribe_topic'] = 'bhoutgate/access/granted'
            return settings
    except FileNotFoundError:
        return {
            'mqtt_broker': 'localhost',
            'mqtt_port': 1883,
            'mqtt_publish_topic': 'bhoutgate/access',
            'mqtt_subscribe_topic': 'bhoutgate/access/granted',
            'video_path': os.path.join(app.static_folder, 'video.mp4'),
            'admin_password': generate_password_hash('admin')  # Default password
        }

# Save settings to file
def save_settings(settings):
    with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json'), 'w') as f:
        json.dump(settings, f, indent=4)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        settings = load_settings()
        password = request.form.get('password')
        if check_password_hash(settings['admin_password'], password):
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    settings = load_settings()
    return render_template('index.html', settings=settings)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Get the file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Define allowed file types and their corresponding filenames
        allowed_files = {
            '.png': 'logo.png',
            '.mp4': 'video.mp4',
            '.mp3': 'bell.mp3',  # Add support for bell sound
            '.wav': 'bell.mp3',  # Also allow WAV files
            '.crt': 'ca_cert.crt',
            '.key': 'client_key.key'
        }
        
        if file_ext not in allowed_files:
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save the file with the predefined name
        filename = allowed_files[file_ext]
        file_path = os.path.join(app.static_folder, filename)
        print(f"Saving file to: {file_path}")  # Debug print
        try:
            file.save(file_path)
            print(f"File saved successfully")  # Debug print
        except Exception as e:
            print(f"Error saving file: {str(e)}")  # Debug print
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        
        # Update settings if it's a video file
        if file_ext == '.mp4':
            settings = load_settings()
            settings['video_path'] = file_path
            save_settings(settings)
        # Update settings if it's a bell sound file
        elif file_ext in ['.mp3', '.wav']:
            settings = load_settings()
            settings['bell_sound_path'] = file_path
            save_settings(settings)
        
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})

@app.route('/save_settings', methods=['POST'])
@login_required
def save_settings_route():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
        
    settings = load_settings()
    new_settings = request.get_json()
    
    # If password is being changed
    if 'admin_password' in new_settings and new_settings['admin_password']:
        settings['admin_password'] = generate_password_hash(new_settings['admin_password'])
        del new_settings['admin_password']
    
    settings.update(new_settings)
    save_settings(settings)
    return jsonify({'message': 'Settings saved successfully'})

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        print(f"Attempting to serve {filename} from {app.static_folder}")
        response = send_from_directory(app.static_folder, filename)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error serving {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    print(f"Static files will be served from: {app.static_folder}")
    app.run(host='0.0.0.0', port=8080, debug=True) 