import os
import uuid
import mimetypes
import tempfile
import requests
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY') 
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'videos')

print("=== SUPABASE CONFIG ===")
print(f"URL: {'SET' if SUPABASE_URL else 'MISSING'}")
print(f"KEY: {'SET' if SUPABASE_KEY else 'MISSING'}")
print(f"BUCKET: {SUPABASE_BUCKET}")

# Test if we can reach Supabase
supabase_available = False
if SUPABASE_URL and SUPABASE_KEY:
    try:
        # Test connection with simple HTTP request
        test_url = f"{SUPABASE_URL}/storage/v1/bucket"
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        if response.status_code in [200, 401, 403]:  # Any response means connection works
            supabase_available = True
            print("✅ Supabase HTTP connection successful")
        else:
            print(f"❌ Supabase HTTP test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Supabase HTTP test error: {e}")
else:
    print("❌ Missing Supabase credentials")

print(f"Supabase available: {supabase_available}")

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
    category = db.Column(db.String(100), default='Miscellaneous')
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

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    category = db.Column(db.String(100), default='Miscellaneous')
    is_published = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=True)
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

def upload_to_supabase_http(file_data, filename, content_type):
    """Upload file to Supabase using direct HTTP requests"""
    if not supabase_available:
        print("❌ Supabase not available")
        return None
    
    try:
        print(f"📤 Uploading {filename} via HTTP...")
        
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
        
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": content_type,
            "x-upsert": "true"  # Add this to allow updates
        }
        
        # For PDFs, add cache control to force inline viewing
        if content_type == "application/pdf":
            headers["Cache-Control"] = "public, max-age=3600"
        
        response = requests.post(upload_url, data=file_data, headers=headers, timeout=300)
        
        print(f"📊 Upload response: {response.status_code}")
        
        if response.status_code == 200:
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
            print(f"✅ Upload successful: {public_url}")
            return public_url
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ HTTP upload error: {e}")
        return None

def generate_thumbnail_http(video_data, original_filename):
    """Generate thumbnail and upload via HTTP"""
    if not supabase_available:
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
            
            # Upload thumbnail via HTTP
            thumbnail_url = upload_to_supabase_http(thumbnail_data, thumbnail_filename, "image/jpeg")
            
            # Cleanup
            vidcap.release()
            os.unlink(temp_video_path)
            return thumbnail_url
        
        vidcap.release()
        os.unlink(temp_video_path)
        return None
        
    except ImportError:
        print("❌ OpenCV not available for thumbnails")
        return None
    except Exception as e:
        print(f"❌ Thumbnail error: {e}")
        return None

def list_supabase_files_http():
    """List files using HTTP requests"""
    if not supabase_available:
        return []
    
    try:
        list_url = f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET}"
        headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
        
        response = requests.post(list_url, headers=headers, json={})
        
        if response.status_code == 200:
            files = []
            for file_info in response.json():
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_info['name']}"
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
        print(f"❌ List files error: {e}")
        return []

def delete_file_http(filename):
    """Delete file using HTTP requests"""
    if not supabase_available:
        return False
    
    try:
        delete_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
        headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}
        
        response = requests.delete(delete_url, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return False

# Routes
@app.route('/')
def index():
    status = "Supabase Connected ✅" if supabase_available else "Supabase Disconnected ❌"
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Mehr Open Mind</title></head>
        <body>
            <h1>Mehr Open Mind</h1>
            <p>Status: {status}</p>
            <a href="/admin.html">Go to Admin Panel</a>
            <br><a href="/health">Check Health</a>
        </body>
        </html>
        '''
@app.route('/admin.html')
def admin():
    # Check for password protection
    admin_password = request.args.get('password')
    correct_password = os.environ.get('ADMIN_PASSWORD', 'defaultpassword')
    
    if admin_password != correct_password:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Admin Access Required</title></head>
        <body style="text-align:center; padding:50px; font-family:Arial;">
            <h2>Admin Access Required</h2>
            <form method="GET">
                <input type="password" name="password" placeholder="Enter admin password" required style="padding:10px; margin:10px;">
                <br>
                <button type="submit" style="padding:10px 20px; margin:10px;">Access Admin Panel</button>
            </form>
        </body>
        </html>
        '''
    
    # If password is correct, show admin panel
    try:
        return send_from_directory(app.static_folder, 'admin.html')
    except Exception as e:
        status = "Supabase Connected" if supabase_available else "Supabase Error"
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Admin Panel</title></head>
        <body>
            <h1>Admin Panel</h1>
            <p>Status: {status}</p>
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
            'available': supabase_available,
            'method': 'direct_http',
            'bucket': SUPABASE_BUCKET,
            'url_configured': bool(SUPABASE_URL),
            'key_configured': bool(SUPABASE_KEY)
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
        
        print(f"📁 Processing: {file.filename} -> {filename}")
        print(f"📊 Size: {len(file_data)} bytes")
        
        # Upload using HTTP
        file_url = upload_to_supabase_http(file_data, filename, content_type)
        
        if not file_url:
            return jsonify({
                'error': 'Failed to upload to Supabase',
                'supabase_available': supabase_available,
                'method': 'direct_http'
            }), 500
        
        # Generate thumbnail
        thumbnail_url = None
        if file_type == 'video':
            thumbnail_url = generate_thumbnail_http(file_data, filename)

        response_data = {
            'url': file_url,
            'filename': filename,
            'original_name': file.filename,
            'size': len(file_data),
            'type': content_type,
            'thumbnail_url': thumbnail_url,
            'method': 'http_upload'
        }
        
        print(f"✅ Upload complete: {file_url}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        files = list_supabase_files_http()
        files.sort(key=lambda x: x.get('created', ''), reverse=True)
        return jsonify(files), 200
    except Exception as e:
        print(f"❌ List files error: {e}")
        return jsonify({'error': 'Failed to list files'}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        if delete_file_http(secure_filename(filename)):
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({'error': 'Failed to delete file'}), 500

@app.route('/api/process-pdf-article', methods=['POST'])
def process_pdf_article():
    try:
        import PyPDF2
        import io
        
        data = request.get_json()
        pdf_url = data['file_url']
        title = data['title']
        
        # Download PDF from Supabase
        response = requests.get(pdf_url)
        pdf_data = io.BytesIO(response.content)
        
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(pdf_data)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n\n"
        
        # Create article in database
        article = TextContent(
            title=title,
            content=text_content.strip(),
            excerpt=data.get('description', ''),
            is_published=True
        )
        db.session.add(article)
        db.session.commit()
        
        return jsonify({'message': 'Article processed successfully', 'id': article.id})
    except Exception as e:
        print(f"PDF processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos', methods=['GET', 'POST'])
def videos():
    try:
        if request.method == 'GET':
            category = request.args.get('category')  # ADD THIS LINE
            if category:  # ADD THIS BLOCK
                videos = VideoContent.query.filter_by(is_published=True, category=category).order_by(VideoContent.order_index.desc()).all()
            else:
                videos = VideoContent.query.filter_by(is_published=True).order_by(VideoContent.order_index.desc()).all()
            return jsonify([{
                'id': v.id,
                'title': v.title,
                'description': v.description,
                'video_url': v.video_url,
                'thumbnail_url': v.thumbnail_url,
                'category': v.category,  # ADD THIS LINE
                'created_at': v.created_at.isoformat()
            } for v in videos])
   
        
       elif request.method == 'POST':
            data = request.get_json()
            video = VideoContent(
                title=data['title'],
                description=data.get('description'),
                video_url=data['video_url'],
                thumbnail_url=data.get('thumbnail_url'),
                category=data.get('category', 'Miscellaneous'),  # ADD THIS LINE
                is_published=data.get('is_published', True),
                order_index=data.get('order_index', 0)
            )
            db.session.add(video)
            db.session.commit()
            return jsonify({'message': 'Video created successfully'}), 201
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
            'file_url': t.file_url,  # ADD THIS LINE
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
                'file_url': text.file_url,  # ADD THIS LINE
                'is_published': text.is_published,
                'order_index': text.order_index,
                'created_at': text.created_at.isoformat()
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            text.title = data.get('title', text.title)
            text.content = data.get('content', text.content)
            text.excerpt = data.get('excerpt', text.excerpt)
            text.file_url = data.get('file_url', text.file_url)  # ADD THIS LINE
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
@app.route('/api/documents', methods=['GET', 'POST'])
def documents_api():
    try:
        if request.method == 'GET':
            category = request.args.get('category')  # ADD THIS
            if category:  # ADD THIS BLOCK
                documents = Document.query.filter_by(is_published=True, category=category).order_by(Document.created_at.desc()).all()
            else:
                documents = Document.query.filter_by(is_published=True).order_by(Document.created_at.desc()).all()
            return jsonify([{
                'id': d.id,
                'title': d.title,
                'description': d.description,
                'file_url': d.file_url,
                'filename': d.filename,
                'category': d.category,  # ADD THIS LINE
                'download_count': d.download_count,
                'created_at': d.created_at.isoformat()
            } for d in documents])
        
       elif request.method == 'POST':
            data = request.get_json()
            document = Document(
                title=data['title'],
                description=data.get('description'),
                file_url=data['file_url'],
                filename=data.get('filename', data['title']),
                file_type=data.get('file_type'),
                file_size=data.get('file_size'),
                category=data.get('category', 'Miscellaneous'),  # ADD THIS LINE
                is_published=data.get('is_published', True)
            )
            db.session.add(document)
            db.session.commit()
            return jsonify({'message': 'Document created successfully'}), 201
    except Exception as e:
        print(f"Documents API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/documents', methods=['GET'])
def admin_documents():
    """Get all documents for admin management"""
    try:
        documents = Document.query.order_by(Document.created_at.desc()).all()
        return jsonify([{
            'id': d.id,
            'title': d.title,
            'description': d.description,
            'file_url': d.file_url,
            'filename': d.filename,
            'file_type': d.file_type,
            'file_size': d.file_size,
            'is_published': d.is_published,
            'download_count': d.download_count,
            'created_at': d.created_at.isoformat()
        } for d in documents])
    except Exception as e:
        print(f"Admin documents error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete document from admin panel"""
    try:
        document = Document.query.get_or_404(doc_id)
        
        # Optionally delete file from Supabase
        filename = document.filename
        delete_file_http(filename)
        
        db.session.delete(document)
        db.session.commit()
        return jsonify({'message': 'Document deleted successfully'})
        
    except Exception as e:
        print(f"Delete document error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/documents')
def public_documents():
    """Public page to view documents"""
    try:
        documents = Document.query.filter_by(is_published=True).order_by(Document.created_at.desc()).all()
        doc_list = ""
        for doc in documents:
            size_mb = round(doc.file_size / (1024*1024), 2) if doc.file_size else 0
            # Add inline parameter to force viewing instead of downloading
            view_url = f"{doc.file_url}?inline=true"
            
            doc_list += f'''
            <div style="border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 8px; background: white;">
                <h3>
                    <a href="{view_url}" target="_blank" style="color: #007cba; text-decoration: none; cursor: pointer;">
                        📄 {doc.title}
                    </a>
                </h3>
                <p style="color: #666; margin: 10px 0;">{doc.description or 'No description available'}</p>
                <p style="color: #888; font-size: 14px;">
                    Size: {size_mb if size_mb > 0 else 'Unknown'} MB | 
                    Views: {doc.download_count} | 
                    Added: {doc.created_at.strftime('%Y-%m-%d')}
                </p>
                <div style="margin-top: 15px;">
                    <a href="{view_url}" target="_blank" 
                       style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Read More
                    </a>
                </div>
            </div>
            '''
        
        if not doc_list:
            doc_list = "<p>No documents available.</p>"
            
        return f'''<!DOCTYPE html>
        <html>
        <head>
            <title>Documents - Mehr Open Mind</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
                h1 {{ color: #333; text-align: center; }}
            </style>
        </head>
        <body>
            <h1>📋 Documents</h1>
            <p style="text-align: center;"><a href="/" style="color: #007cba; text-decoration: none;">← Back to Home</a></p>
            <hr>
            {doc_list}
        </body>
        </html>'''
    except Exception as e:
        return f"<h1>Error loading documents</h1><p>{str(e)}</p>"
@app.route('/download/<int:doc_id>')
def download_document(doc_id):
    """Handle document downloads and track download count"""
    try:
        document = Document.query.get_or_404(doc_id)
        
        if not document.is_published:
            return "Document not available", 404
        
        # Increment download count
        document.download_count += 1
        db.session.commit()
        
        # Redirect to the actual file URL in Supabase
        return redirect(document.file_url)
        
    except Exception as e:
        print(f"Download document error: {e}")
        return jsonify({'error': str(e)}), 500
# Initialize database
with app.app_context():
    try:
        db.create_all()
        print("✅ Database ready")
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
