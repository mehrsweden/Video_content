from flask import Blueprint, request, jsonify
from src.models.content import db, VideoContent, TextContent
from datetime import datetime

content_bp = Blueprint('content', __name__)

# Video Content Routes
@content_bp.route('/videos', methods=['GET'])
def get_videos():
    """Get all published videos ordered by order_index"""
    videos = VideoContent.query.filter_by(is_published=True).order_by(VideoContent.order_index.desc(), VideoContent.created_at.desc()).all()
    return jsonify([video.to_dict() for video in videos])

@content_bp.route('/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Get a specific video by ID"""
    video = VideoContent.query.get_or_404(video_id)
    if not video.is_published:
        return jsonify({'error': 'Video not found'}), 404
    return jsonify(video.to_dict())

@content_bp.route('/videos', methods=['POST'])
def create_video():
    """Create a new video content"""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('video_url'):
        return jsonify({'error': 'Title and video_url are required'}), 400
    
    video = VideoContent(
        title=data['title'],
        description=data.get('description', ''),
        video_url=data['video_url'],
        thumbnail_url=data.get('thumbnail_url', ''),
        is_published=data.get('is_published', True),
        order_index=data.get('order_index', 0)
    )
    
    db.session.add(video)
    db.session.commit()
    
    return jsonify(video.to_dict()), 201

@content_bp.route('/videos/<int:video_id>', methods=['PUT'])
def update_video(video_id):
    """Update an existing video"""
    video = VideoContent.query.get_or_404(video_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    video.title = data.get('title', video.title)
    video.description = data.get('description', video.description)
    video.video_url = data.get('video_url', video.video_url)
    video.thumbnail_url = data.get('thumbnail_url', video.thumbnail_url)
    video.is_published = data.get('is_published', video.is_published)
    video.order_index = data.get('order_index', video.order_index)
    video.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(video.to_dict())

@content_bp.route('/videos/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete a video"""
    video = VideoContent.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({'message': 'Video deleted successfully'})

# Text Content Routes
@content_bp.route('/texts', methods=['GET'])
def get_texts():
    """Get all published text content ordered by order_index"""
    texts = TextContent.query.filter_by(is_published=True).order_by(TextContent.order_index.desc(), TextContent.created_at.desc()).all()
    return jsonify([text.to_dict() for text in texts])

@content_bp.route('/texts/<int:text_id>', methods=['GET'])
def get_text(text_id):
    """Get a specific text content by ID"""
    text = TextContent.query.get_or_404(text_id)
    if not text.is_published:
        return jsonify({'error': 'Text content not found'}), 404
    return jsonify(text.to_dict())

@content_bp.route('/texts', methods=['POST'])
def create_text():
    """Create a new text content"""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content are required'}), 400
    
    text = TextContent(
        title=data['title'],
        content=data['content'],
        excerpt=data.get('excerpt', ''),
        is_published=data.get('is_published', True),
        order_index=data.get('order_index', 0)
    )
    
    db.session.add(text)
    db.session.commit()
    
    return jsonify(text.to_dict()), 201

@content_bp.route('/texts/<int:text_id>', methods=['PUT'])
def update_text(text_id):
    """Update an existing text content"""
    text = TextContent.query.get_or_404(text_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    text.title = data.get('title', text.title)
    text.content = data.get('content', text.content)
    text.excerpt = data.get('excerpt', text.excerpt)
    text.is_published = data.get('is_published', text.is_published)
    text.order_index = data.get('order_index', text.order_index)
    text.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(text.to_dict())

@content_bp.route('/texts/<int:text_id>', methods=['DELETE'])
def delete_text(text_id):
    """Delete a text content"""
    text = TextContent.query.get_or_404(text_id)
    db.session.delete(text)
    db.session.commit()
    
    return jsonify({'message': 'Text content deleted successfully'})

# Admin routes to get all content (including unpublished)
@content_bp.route('/admin/videos', methods=['GET'])
def get_all_videos():
    """Get all videos (including unpublished) for admin"""
    videos = VideoContent.query.order_by(VideoContent.order_index.desc(), VideoContent.created_at.desc()).all()
    return jsonify([video.to_dict() for video in videos])

@content_bp.route('/admin/texts', methods=['GET'])
def get_all_texts():
    """Get all text content (including unpublished) for admin"""
    texts = TextContent.query.order_by(TextContent.order_index.desc(), TextContent.created_at.desc()).all()
    return jsonify([text.to_dict() for text in texts])
