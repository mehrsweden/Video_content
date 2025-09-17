import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory
from src.models.user import db
from src.models.content import VideoContent, TextContent
from src.routes.user import user_bp
from src.routes.content import content_bp
from enhanced_routes import upload_bp, content_enhanced_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'static'))

# Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Register existing blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(content_bp, url_prefix='/api')

# Register enhanced upload routes
app.register_blueprint(upload_bp)
app.register_blueprint(content_enhanced_bp)

# Database configuration - supports both SQLite and PostgreSQL
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
db.init_app(app)

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
    debug = True
    app.run(host='0.0.0.0', port=port, debug=debug)

