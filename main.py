import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Handle PostgreSQL URL format for Heroku
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Default to SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Import models after db initialization
from src.models.user import User
from src.models.content import VideoContent, TextContent

# Import routes
from src.routes.content import upload_bp, content_enhanced_bp

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(content_enhanced_bp)

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create uploads directory
    upload_path = os.path.join(app.static_folder, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(413)
def too_large(e):
    return "File is too large. Maximum size is 500MB.", 413

if __name__ == '__main__':
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
