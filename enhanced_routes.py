import cv2
import numpy as np
from PIL import Image
import os
import uuid
import mimetypes
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import PyPDF2
import docx
import markdown

# File upload configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB for videos
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'wmv', 'flv', 'mkv', 'webm', 'm4v'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'md', 'odt'}

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename, file_type):
    """Check if file extension is allowed for the given type"""
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

def create_upload_folder():
    """Create upload folder if it doesn't exist"""
    upload_path = os.path.join(current_app.root_path, 'static', UPLOAD_FOLDER)
    os.makedirs(upload_path, exist_ok=True)
    return upload_path

def generate_unique_filename(filename):
    """Generate a unique filename to prevent conflicts"""
    name, ext = os.path.splitext(secure_filename(filename))
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}_{unique_id}{ext}"

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return None

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading TXT file: {e}")
        return None

def extract_text_from_markdown(file_path):
    """Extract text from Markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
            # Convert markdown to HTML then extract text
            html = markdown.markdown(md_content)
            # For now, just return the markdown content
            return md_content.strip()
    except Exception as e:
        print(f"Error reading Markdown file: {e}")
        return None

def extract_document_text(file_path, filename):
    """Extract text from various document formats"""
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif extension in ['doc', 'docx']:
        return extract_text_from_docx(file_path)
    elif extension == 'txt':
        return extract_text_from_txt(file_path)
    elif extension == 'md':
        return extract_text_from_markdown(file_path)
    elif extension == 'rtf':
        # For RTF, we'll treat it as text for now
        return extract_text_from_txt(file_path)
    
    return None

@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
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
        upload_path = create_upload_folder()
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        
        # Save the file
        file.save(file_path)
        
        # Generate URL for the file
        file_url = f"/static/{UPLOAD_FOLDER}/{filename}"
        
        response_data = {
            'url': file_url,
            'filename': filename,
            'original_name': file.filename,
            'size': os.path.getsize(file_path),
            'type': file.content_type or mimetypes.guess_type(filename)[0]
        }
        
        # If it's a document, extract text
        if file_type == 'document':
            extracted_text = extract_document_text(file_path, file.filename)
            if extracted_text:
                response_data['extractedText'] = extracted_text
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@upload_bp.route('/api/files', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        upload_path = os.path.join(current_app.root_path, 'static', UPLOAD_FOLDER)
        
        if not os.path.exists(upload_path):
            return jsonify([]), 200
        
        files = []
        for filename in os.listdir(upload_path):
            file_path = os.path.join(upload_path, filename)
            if os.path.isfile(file_path):
                file_info = {
                    'name': filename,
                    'url': f"/static/{UPLOAD_FOLDER}/{filename}",
                    'size': os.path.getsize(file_path),
                    'type': mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                }
                files.append(file_info)
        
        # Sort by creation date (newest first)
        files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify(files), 200
        
    except Exception as e:
        print(f"Error listing files: {e}")
        return jsonify({'error': 'Failed to list files'}), 500

@upload_bp.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete an uploaded file"""
    try:
        upload_path = os.path.join(current_app.root_path, 'static', UPLOAD_FOLDER)
        file_path = os.path.join(upload_path, secure_filename(filename))
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Error deleting file: {e}")
        return jsonify({'error': 'Failed to delete file'}), 500

# Enhanced content routes with file support
content_enhanced_bp = Blueprint('content_enhanced', __name__)

@content_enhanced_bp.route('/api/admin/videos', methods=['GET'])
def get_admin_videos():
    """Get all videos for admin (including unpublished)"""
    from src.models.content import VideoContent
    try:
        videos = VideoContent.query.order_by(VideoContent.order_index.desc(), VideoContent.created_at.desc()).all()
        return jsonify([{
            'id': video.id,
            'title': video.title,
            'description': video.description,
            'video_url': video.video_url,
            'thumbnail_url': video.thumbnail_url,
            'is_published': video.is_published,
            'order_index': video.order_index,
            'created_at': video.created_at.isoformat()
        } for video in videos]), 200
    except Exception as e:
        print(f"Error fetching admin videos: {e}")
        return jsonify({'error': 'Failed to fetch videos'}), 500

@content_enhanced_bp.route('/api/admin/texts', methods=['GET'])
def get_admin_texts():
    """Get all texts for admin (including unpublished)"""
    from src.models.content import TextContent
    try:
        texts = TextContent.query.order_by(TextContent.order_index.desc(), TextContent.created_at.desc()).all()
        return jsonify([{
            'id': text.id,
            'title': text.title,
            'content': text.content,
            'excerpt': text.excerpt,
            'is_published': text.is_published,
            'order_index': text.order_index,
            'created_at': text.created_at.isoformat()
        } for text in texts]), 200
    except Exception as e:
        print(f"Error fetching admin texts: {e}")
        return jsonify({'error': 'Failed to fetch texts'}), 500
