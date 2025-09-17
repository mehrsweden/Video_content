# Content Management System

This is a complete content management system with video upload functionality and automatic thumbnail generation. It includes a modern admin interface for managing videos, articles, and files.

## Features

- **Video Management:** Upload videos, generate thumbnails, and manage content.
- **File Management:** A complete file manager for videos, images, and documents.
- **Admin Interface:** A modern, responsive admin panel for easy content management.
- **RESTful API:** A complete set of API endpoints for content and file management.
- **Production Ready:** Properly configured for Heroku deployment.

## Deployment

This application is designed for deployment on Heroku. Follow these steps to deploy:

1. **Push to GitHub:** Push the code to your GitHub repository.
2. **Create Heroku App:** Create a new application on Heroku.
3. **Connect to GitHub:** Connect your Heroku app to your GitHub repository.
4. **Deploy:** Deploy the application from the `main` branch.

## Local Development

To run the application locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd content-cms-repo
   ```

2. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Access locally:**
   - Main site: http://localhost:5000
   - Admin panel: http://localhost:5000/admin.html

