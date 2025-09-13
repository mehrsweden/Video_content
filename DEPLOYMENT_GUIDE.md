# Content Hub - Deployment Guide

This guide will help you deploy the Content Hub application to your own hosting service with a custom domain.

## Project Overview

Content Hub is a Flask-based content management system that allows you to display videos and text articles on a beautiful website with an admin panel for content management.

## Prerequisites

- Python 3.8 or higher
- A hosting service that supports Python/Flask applications
- A custom domain (optional)

## Local Development Setup

1. **Extract the project files** to your desired directory
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application:**
   ```bash
   python src/main.py
   ```
5. **Access the application:**
   - Main website: http://localhost:5000
   - Admin panel: http://localhost:5000/admin.html

## Deployment Options

### Option 1: Heroku (Recommended for beginners)

1. **Install Heroku CLI** from https://devcenter.heroku.com/articles/heroku-cli
2. **Create a Procfile** in the project root:
   ```
   web: python src/main.py
   ```
3. **Update main.py** for production (change the last line):
   ```python
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 5000))
       app.run(host='0.0.0.0', port=port, debug=False)
   ```
4. **Deploy to Heroku:**
   ```bash
   heroku create your-app-name
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```
5. **Add custom domain** (requires paid Heroku plan):
   ```bash
   heroku domains:add www.yourdomain.com
   ```

### Option 2: DigitalOcean App Platform

1. **Create a DigitalOcean account** at https://digitalocean.com
2. **Create a new App** from the control panel
3. **Connect your GitHub repository** or upload the project
4. **Configure the app:**
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Run command: `python src/main.py`
5. **Add custom domain** in the app settings

### Option 3: Railway

1. **Create account** at https://railway.app
2. **Deploy from GitHub** or upload project
3. **Railway will auto-detect** the Flask application
4. **Add custom domain** in project settings

### Option 4: PythonAnywhere

1. **Create account** at https://pythonanywhere.com
2. **Upload project files** via file manager
3. **Create a web app** with manual configuration
4. **Configure WSGI file** to point to your Flask app
5. **Add custom domain** (paid plans only)

## Environment Variables

For production deployment, consider setting these environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-database-url  # If using external database
```

## Database Considerations

The project uses SQLite by default, which works for small to medium applications. For production with high traffic, consider:

- **PostgreSQL** (recommended for Heroku)
- **MySQL**
- **SQLite** (fine for smaller applications)

To switch to PostgreSQL:
1. Add `psycopg2-binary` to requirements.txt
2. Update the database URL in main.py
3. Set DATABASE_URL environment variable

## Custom Domain Setup

After deploying to your chosen platform:

1. **Purchase a domain** from a registrar (GoDaddy, Namecheap, etc.)
2. **Configure DNS settings:**
   - Add CNAME record pointing to your hosting platform
   - Or add A record with the IP address
3. **Update platform settings** to recognize your custom domain
4. **Enable SSL/HTTPS** (most platforms offer free SSL certificates)

## Content Management

Once deployed:

1. **Access admin panel** at `yourdomain.com/admin.html`
2. **Add your content:**
   - Videos: Provide direct video file URLs
   - Articles: Write your text content
3. **Manage visibility** with the Published checkbox
4. **Control order** with the Order Index field

## Security Considerations

For production deployment:

1. **Change the SECRET_KEY** in main.py
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** on your domain
4. **Consider adding authentication** to the admin panel
5. **Regular backups** of your database

## Troubleshooting

- **500 errors**: Check application logs on your hosting platform
- **Database issues**: Ensure database file permissions are correct
- **Static files not loading**: Verify static file serving configuration
- **Admin panel not working**: Check JavaScript console for errors

## Support

- Flask documentation: https://flask.palletsprojects.com/
- Hosting platform documentation for specific deployment issues
- Check application logs for error details

## File Structure

```
content-cms-backend/
├── src/
│   ├── models/
│   │   ├── user.py          # User model (for future authentication)
│   │   └── content.py       # Video and text content models
│   ├── routes/
│   │   ├── user.py          # User API routes
│   │   └── content.py       # Content management API routes
│   ├── static/
│   │   ├── index.html       # Main website
│   │   └── admin.html       # Admin panel
│   ├── database/
│   │   └── app.db          # SQLite database
│   └── main.py             # Flask application entry point
├── requirements.txt        # Python dependencies
├── add_sample_data.py     # Script to add sample content
└── README.md              # Project documentation
```

Good luck with your deployment!
