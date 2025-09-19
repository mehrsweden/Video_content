import os
import uuid
import mimetypes
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Initialize Supabase
supabase = None
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'videos')

try:
    from supabase import create_client
    
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✓ Supabase client initialized successfully")
        print(f"✓ Using bucket: {SUPABASE_BUCKET}")
    else:
        print("⚠ Warning: SUPABASE_URL or SUPABASE_KEY not found")
        
except ImportError:
    print("⚠ Warning: Supabase library not installed")
except Exception as e:
    print(f"⚠ Supabase initialization error: {e}")

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

# File configuration
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

def upload_to_supabase(file_data, filename, content_type):
    """Upload file to Supabase Storage"""
    if not supabase:
        print("❌ Supabase not available for upload")
        return None
    
    try:
        print(f"📤 Uploading {filename} to Supabase...")
        
        # Upload file to Supabase Storage
        result = supabase.storage.from_(SUPABASE_BUCKET).upload(
            filename,
            file_data,
            file_options={"content-type": content_type}
        )
        
        if result.data:
            print(f"✓ Upload successful: {filename}")
            # Get public URL
            public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
            print(f"✓ Public URL: {public_url}")
            return public_url
        else:
            print(f"❌ Upload failed: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Supabase upload error: {e}")
        return None

def generate_thumbnail(video_data, original_filename):
    """Generate thumbnail from video and upload to Supabase"""
    if not supabase:
        return None
    
    try:
        import cv2
        import numpy as np
        
        print(f"🖼️ Generating thumbnail for {original_filename}...")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(video_data)
            temp_video_path = temp_video.name

        # Extract first frame
        vidcap = cv2.VideoCapture(temp_video_path)
        success, image = vidcap.read()
        
        if success:
            base_name = os.path.splitext(original_filename)[0]
            thumbnail_filename = f"{base_name}_thumb.jpg"
            
            # Convert to JPEG
            _, buffer = cv2.imencode('.jpg', image)
            thumbnail_data = buffer.tobytes()
            
            # Upload thumbnail
            result = supabase.storage.from_(SUPABASE_BUCKET).upload(
                thumbnail_filename, 
                thumbnail_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            if result.data:
                thumbnail_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(thumbnail_filename)
                print(f"✓ Thumbnail created: {thumbnail_url}")
                
                # Cleanup
                vidcap.release()
                os.unlink(temp_video_path)
                return thumbnail_url
        
        vidcap.release()
        os.unlink(temp_video_path)
        return None
        
    except ImportError:
        print("⚠ OpenCV not available for thumbnail generation")
        return None
    except Exception as e:
        print(f"❌ Thumbnail generation error: {e}")
        return None

def list_supabase_files():
    """List files from Supabase Storage"""
    if not supabase:
        return []
    
    try:
        result = supabase.storage.from_(SUPABASE_BUCKET).list()
        if result:
            files = []
            for file_info in result:
                public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_info['name'])
                
                files.append({
                    'name': file_info['name'],
                    'url': public_url,
                    'size': file_info.get('metadata', {}).get('size', 0),
                    'type': file_info.get('metadata', {}).get('mimetype', 'application/octet-stream'),
                    'created': file_info.get('created_at', datetime.utcnow().isoformat())
                })
            return files
        return []
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def delete_from_supabase(filename):
    """Delete file from Supabase Storage"""
    if not supabase:
        return False
    
    try:
        result = supabase.storage.from_(SUPABASE_BUCKET).remove([filename])
        return result.data is not None
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
        return False

# Routes
@app.route('/')
def index():
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Content Hub</title></head>
        <body>
            <h1>Content Hub</h1>
            <p>Welcome to your content management system!</p>
            <p>Status: {'Supabase Connected' if supabase else 'Supabase Disconnected'}</p>
            <a href="/admin.html">Go to Admin Panel</a>
            <br><a href="/health">Check Health Status</a>
            <br><br><small>Debug: {str(e)}</small>
        </body>
        </html>
        '''

@app.route('/admin.html')
def admin():
    try:
        return send_from_directory(app.static_folder, 'admin.html')
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Admin Panel</title></head>
        <body>
            <h1>Admin Panel</h1>
            <p>Status: {'Supabase Connected ✓' if supabase else 'Supabase Disconnected ❌'}</p>
            <small>Debug: {str(e)}</small>
        </body>
        </html>
        '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'supabase': {
            'available': supabase is not None,
            'bucket': SUPABASE_BUCKET,
            'url_configured': bool(os.environ.get('SUPABASE_URL')),
            'key_configured': bool(os.environ.get('SUPABASE_KEY'))
        }
    })

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
        
        # Read file data
        file_data = file.read()
        filename = generate_unique_filename(file.filename)
        content_type = file.content_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        print(f"📁 Processing upload: {file.filename} -> {filename}")
        print(f"📊 File size: {len(file_data)} bytes")
        
        # Upload to Supabase
        file_url = upload_to_supabase(file_data, filename, content_type)
        
        if not file_url:
            return jsonify({
                'error': 'Failed to upload to Supabase', 
                'supabase_available': supabase is not None,
                'bucket': SUPABASE_BUCKET
            }), 500
        
        # Generate thumbnail for videos
        thumbnail_url = None
        if file_type == 'video':
            thumbnail_url = generate_thumbnail(file_data, filename)

        response_data = {
            'url': file_url,
            'filename': filename,
            'original_name': file.filename,
            'size': len(file_data),
            'type': content_type,
            'thumbnail_url': thumbnail_url,
            'uploaded_to_supabase': True
        }
        
        print(f"✅ Upload complete: {file_url}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        files = list_supabase_files()
        files.sort(key=lambda x: x.get('created', ''), reverse=True)
        return jsonify(files), 200
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return jsonify({'error': 'Failed to list files'}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        if delete_from_supabase(secure_filename(filename)):
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
        return jsonify({'error': 'Failed to delete file'}), 500

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
                is_published=data.get('is_published', True),
                order_index=data.get('order_index', 0)
            )
            db.session.add(video)
            db.session.commit()
            return jsonify({'message': 'Video created successfully'}), 201
    except Exception as e:
        print(f"❌ Videos API error: {e}")
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
        print(f"❌ Admin videos error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<int:video_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_video(video_id):
    try:
        video = VideoContent.query.get_or_404(video_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'video_url': video.video_url,
                'thumbnail_url': video.thumbnail_url,
                'is_published': video.is_published,
                'order_index': video.order_index,
                'created_at': video.created_at.isoformat()
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            video.title = data.get('title', video.title)
            video.description = data.get('description', video.description)
            video.video_url = data.get('video_url', video.video_url)
            video.thumbnail_url = data.get('thumbnail_url', video.thumbnail_url)
            video.is_published = data.get('is_published', video.is_published)
            video.order_index = data.get('order_index', video.order_index)
            db.session.commit()
            return jsonify({'message': 'Video updated successfully'})
        
        elif request.method == 'DELETE':
            db.session.delete(video)
            db.session.commit()
            return jsonify({'message': 'Video deleted successfully'})
            
    except Exception as e:
        print(f"❌ Manage video error: {e}")
        return jsonify({'error': str(e)}), 500

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
                is_published=data.get('is_published', True),
                order_index=data.get('order_index', 0)
            )
            db.session.add(text)
            db.session.commit()
            return jsonify({'message': 'Text created successfully'}), 201
    except Exception as e:
        print(f"❌ Texts API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/texts', methods=['GET'])
def admin_texts():
    try:
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
    except Exception as e:
        print(f"❌ Admin texts error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/texts/<int:text_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_text(text_id):
    try:
        text = TextContent.query.get_or_404(text_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': text.id,
                'title': text.title,
                'content': text.content,
                'excerpt': text.excerpt,
                'is_published': text.is_published,
                'order_index': text.order_index,
                'created_at': text.created_at.isoformat()
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            text.title = data.get('title', text.title)
            text.content = data.get('content', text.content)
            text.excerpt = data.get('excerpt', text.excerpt)
            text.is_published = data.get('is_published', text.is_published)
            text.order_index = data.get('order_index', text.order_index)
            db.session.commit()
            return jsonify({'message': 'Text updated successfully'})
        
        elif request.method == 'DELETE':
            db.session.delete(text)
            db.session.commit()
            return jsonify({'message': 'Text deleted successfully'})
            
    except Exception as e:
        print(f"❌ Manage text error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File is too large. Maximum size is 500MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize database
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
