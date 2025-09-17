import os
import uuid
import mimetypes
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import cv2

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Models
class VideoContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TextContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# File upload configuration
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'wmv', 'flv', 'mkv', 'webm', 'm4v'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'md', 'odt'}

def allowed_file(filename, file_type):
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    if file_type == 'video':
        return extension in ALLOWED_VIDEO_EXTENSIONS
    elif file_type == 'image':
        return extension in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'document':
        return extension in ALLOWED_DOCUMENT_EXTENSIONS
    return False

def generate_unique_filename(filename):
    name, ext = os.path.splitext(secure_filename(filename))
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}_{unique_id}{ext}"

def generate_thumbnail(video_path, thumbnail_dir):
    try:
        vidcap = cv2.VideoCapture(video_path)
        success, image = vidcap.read()
        if success:
            thumbnail_filename = os.path.splitext(os.path.basename(video_path))[0] + ".jpg"
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
            cv2.imwrite(thumbnail_path, image)
            return f"/static/{app.config['UPLOAD_FOLDER']}/{thumbnail_filename}"
        return None
    except Exception as e:
        print(f"Thumbnail generation error: {e}")
        return None

# Routes
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/admin.html')
def admin():
    return send_from_directory('static', 'admin.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('type', 'video')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, file_type):
            return jsonify({'error': f'File type not allowed for {file_type}'}), 400
        
        # Create upload directory
        upload_path = os.path.join('static', app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_path, exist_ok=True)
        
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        file_url = f"/static/{app.config['UPLOAD_FOLDER']}/{filename}"
        thumbnail_url = None

        if file_type == 'video':
            thumbnail_url = generate_thumbnail(file_path, upload_path)

        response_data = {
            'url': file_url,
            'filename': filename,
            'original_name': file.filename,
            'size': os.path.getsize(file_path),
            'type': file.content_type or mimetypes.guess_type(filename)[0],
            'thumbnail_url': thumbnail_url
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        upload_path = os.path.join('static', app.config['UPLOAD_FOLDER'])
        
        if not os.path.exists(upload_path):
            return jsonify([]), 200
        
        files = []
        for filename in os.listdir(upload_path):
            file_path = os.path.join(upload_path, filename)
            if os.path.isfile(file_path):
                file_info = {
                    'name': filename,
                    'url': f"/static/{app.config['UPLOAD_FOLDER']}/{filename}",
                    'size': os.path.getsize(file_path),
                    'type': mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                }
                files.append(file_info)
        
        files.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(files), 200
        
    except Exception as e:
        print(f"Error listing files: {e}")
        return jsonify({'error': 'Failed to list files'}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        upload_path = os.path.join('static', app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(upload_path, secure_filename(filename))
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Error deleting file: {e}")
        return jsonify({'error': 'Failed to delete file'}), 500

@app.route('/api/videos', methods=['GET', 'POST'])
def videos():
    if request.method == 'GET':
        videos = VideoContent.query.filter_by(is_published=True).order_by(VideoContent.order_index.desc()).all()
        return jsonify([{
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'video_url': v.video_url,
            'thumbnail_url': v.thumbnail_url,
            'created_at': v.created_at.isoformat()
        } for v in videos])
    
    elif request.method == 'POST':
        data = request.get_json()
        video = VideoContent(
            title=data['title'],
            description=data.get('description'),
            video_url=data['video_url'],
            thumbnail_url=data.get('thumbnail_url'),
            is_published=data.get('is_published', True),
            order_index=data.get('order_index', 0)
        )
        db.session.add(video)
        db.session.commit()
        return jsonify({'message': 'Video created successfully'}), 201

@app.route('/api/admin/videos', methods=['GET'])
def admin_videos():
    videos = VideoContent.query.order_by(VideoContent.order_index.desc()).all()
    return jsonify([{
        'id': v.id,
        'title': v.title,
        'description': v.description,
        'video_url': v.video_url,
        'thumbnail_url': v.thumbnail_url,
        'is_published': v.is_published,
        'order_index': v.order_index,
        'created_at': v.created_at.isoformat()
    } for v in videos])

@app.route('/api/texts', methods=['GET', 'POST'])
def texts():
    if request.method == 'GET':
        texts = TextContent.query.filter_by(is_published=True).order_by(TextContent.order_index.desc()).all()
        return jsonify([{
            'id': t.id,
            'title': t.title,
            'content': t.content,
            'excerpt': t.excerpt,
            'created_at': t.created_at.isoformat()
        } for t in texts])
    
    elif request.method == 'POST':
        data = request.get_json()
        text = TextContent(
            title=data['title'],
            content=data['content'],
            excerpt=data.get('excerpt'),
            is_published=data.get('is_published', True),
            order_index=data.get('order_index', 0)
        )
        db.session.add(text)
        db.session.commit()
        return jsonify({'message': 'Text created successfully'}), 201

@app.route('/api/admin/texts', methods=['GET'])
def admin_texts():
    texts = TextContent.query.order_by(TextContent.order_index.desc()).all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'content': t.content,
        'excerpt': t.excerpt,
        'is_published': t.is_published,
        'order_index': t.order_index,
        'created_at': t.created_at.isoformat()
    } for t in texts])

@app.errorhandler(413)
def too_large(e):
    return "File is too large. Maximum size is 500MB.", 413

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create static directory
    os.makedirs('static', exist_ok=True)
    os.makedirs(os.path.join('static', app.config['UPLOAD_FOLDER']), exist_ok=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
