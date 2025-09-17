# Content Management System

A complete content management system with video upload functionality and automatic thumbnail generation.

## Features

- **Video Management:** Upload videos with automatic thumbnail generation using OpenCV
- **File Management:** Complete file manager for videos, images, and documents
- **Admin Interface:** Modern, responsive admin panel with drag-and-drop uploads
- **RESTful API:** Complete set of API endpoints for content and file management
- **Production Ready:** Configured for Heroku deployment with PostgreSQL

## Heroku Deployment

This application is optimized for Heroku deployment:

1. **Push to GitHub:** Update your repository with these files
2. **Deploy to Heroku:** Connect your GitHub repository to Heroku
3. **Add PostgreSQL:** Add Heroku Postgres add-on to your app
4. **Configure Domain:** Set up your custom domain mehropenmind.com

## Key Dependencies

- Flask with SQLAlchemy for web framework and database
- OpenCV for video thumbnail generation
- Gunicorn for production WSGI server
- PostgreSQL for production database
- Various file processing libraries (PyPDF2, python-docx, etc.)

## Local Development

```bash
git clone <your-repository>
cd <repository-name>
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Access at: http://localhost:5000
