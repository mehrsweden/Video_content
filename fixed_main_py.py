import os
import uuid
import mimetypes
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Database configuration for Heroku
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
        import cv2
        vidcap = cv2.VideoCapture(video_path)
        success, image = vidcap.read()
        if success:
            thumbnail_filename = os.path.splitext(os.path.basename(video_path))[0] + ".jpg"
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
            cv2.imwrite(thumbnail_path, image)
            vidcap.release()
            return f"https://mehropenmind.com/static/{app.config['UPLOAD_FOLDER']}/{thumbnail_filename}"
        return None
    except Exception as e:
        print(f"Thumbnail generation error: {e}")
        return None

def init_db():
    """Initialize database - called separately from main app startup"""
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
            
            # Create upload directory
            upload_path = os.path.join(app.static_folder or 'static', app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_path, exist_ok=True)
            print("Upload directory created successfully")
            
    except Exception as e:
        print(f"Database initialization error: {e}")

# Routes
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Content Hub</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
            .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Content Hub</h1>
            <p>Welcome to your content management system!</p>
            <a href="/admin" class="btn">Go to Admin Panel</a>
            <a href="/api/health" class="btn">Check Health</a>
        </div>
    </body>
    </html>
    '''

@app.route('/admin')
def admin():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .nav { background: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px; }
            .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
            .section { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="nav">
            <a href="/">← Back to Home</a>
            <a href="/api/health">Health Check</a>
            <a href="/api/admin/videos">Videos API</a>
            <a href="/api/admin/texts">Texts API</a>
        </div>
        
        <div class="section">
            <h2>Quick Actions</h2>
            <p>Use the API endpoints to manage content:</p>
            <ul>
                <li><strong>GET /api/videos</strong> - List published videos</li>
                <li><strong>GET /api/texts</strong> - List published texts</li>
                <li><strong>POST /api/upload</strong> - Upload files</li>
                <li><strong>GET /api/files</strong> - List uploaded files</li>
            </ul>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
@app.route('/api/health')
def health():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'features': {
            'article_download': 'enabled',
            'video_upload': 'enabled',
            'file_management': 'enabled'
        }
    })

# Article download route
@app.route('/api/download/article/<int:article_id>')
def download_article(article_id):
    try:
        article = TextContent.query.get_or_404(article_id)
        
        content = f"""{article.title}
{'=' * len(article.title)}

{f"{article.excerpt}\n\n" if article.excerpt else ""}{article.content}

---
Created: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Article ID: {article.id}
"""
        
        safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_').lower()[:50]
        filename = f"{safe_title}_{article.id}.txt"
        
        return Response(
            content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Upload and file management routes
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
        
        upload_path = os.path.join(app.static_folder or 'static', app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_path, exist_ok=True)
        
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        file_url = f"https://mehropenmind.com/static/{app.config['UPLOAD_FOLDER']}/{filename}"
        thumbnail_url = None

        if file_type == 'video':
            thumbnail_url = generate_thumbnail(file_path, upload_path)

        return jsonify({
            'url': file_url,
            'filename': filename,
            'original_name': file.filename,
            'size': os.path.getsize(file_path),
            'type': file.content_type or mimetypes.guess_type(filename)[0],
            'thumbnail_url': thumbnail_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        upload_path = os.path.join(app.static_folder or 'static', app.config['UPLOAD_FOLDER'])
        
        if not os.path.exists(upload_path):
            return jsonify([]), 200
        
        files = []
        for filename in os.listdir(upload_path):
            file_path = os.path.join(upload_path, filename)
            if os.path.isfile(file_path):
                files.append({
                    'name': filename,
                    'url': f"https://mehropenmind.com/static/{app.config['UPLOAD_FOLDER']}/{filename}",
                    'size': os.path.getsize(file_path),
                    'type': mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })
        
        files.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(files), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to list files'}), 500

# Video management routes
@app.route('/api/videos', methods=['GET', 'POST'])
def videos():
    try:
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
                order_index=data.get('order_index', 0)
            )
            db.session.add(video)
            db.session.commit()
            return jsonify({'message': 'Video created successfully', 'id': video.id}), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/videos', methods=['GET'])
def admin_videos():
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Text content routes
@app.route('/api/texts', methods=['GET', 'POST'])
def texts():
    try:
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
                order_index=data.get('order_index', 0)
            )
            db.session.add(text)
            db.session.commit()
            return jsonify({'message': 'Text created successfully', 'id': text.id}), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/texts', methods=['GET'])
def admin_texts():
    try:
        texts = TextContent.query.order_by(TextContent.order_index.desc()).all()
        return jsonify([{
            'id': t.id,
            'title': t.title,
            'content': t.content[:200] + '...' if len(t.content) > 200 else t.content,
            'excerpt': t.excerpt,
            'is_published': t.is_published,
            'order_index': t.order_index,
            'created_at': t.created_at.isoformat()
        } for t in texts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize database when imported, not when running
if not os.environ.get('SKIP_DB_INIT'):
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)