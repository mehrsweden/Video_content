# Content Management System with Supabase Storage

A Flask-based content management system with video upload functionality using Supabase Storage for persistent file storage on Heroku.

## Features

- Video upload with automatic thumbnail generation using OpenCV
- Persistent file storage using Supabase Storage (no more disappearing files!)
- Admin interface with drag-and-drop uploads
- Complete CRUD operations for videos and text content
- RESTful API endpoints
- Optimized for Heroku deployment

## Setup Instructions

### 1. Supabase Setup

1. Create a Supabase account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Storage in the Supabase dashboard
4. Create a new bucket named `videos` (make it public)
5. Get your project URL and anon key from Settings > API

### 2. Heroku Deployment

1. Push this code to your GitHub repository
2. In Heroku dashboard, connect your GitHub repo
3. Set the following environment variables in Heroku:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_BUCKET=videos
SECRET_KEY=your-random-secret-key
```

### 3. Local Development (Optional)

1. Copy `.env.example` to `.env`
2. Fill in your Supabase credentials
3. Run:
```bash
pip install -r requirements.txt
python main.py
```

## Key Changes from Original

- **Persistent Storage**: Files now stored in Supabase Storage, not local filesystem
- **No More Data Loss**: Videos persist through dyno restarts
- **Cloud Thumbnails**: Thumbnails generated and stored in cloud
- **Direct URLs**: Files served directly from Supabase CDN

## File Structure

- `main.py` - Flask application with Supabase integration
- `requirements.txt` - Python dependencies including Supabase
- `static/` - HTML files (unchanged)
- `.env.example` - Environment variables template

## Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon/public key | `eyJ0eXAi...` |
| `SUPABASE_BUCKET` | Storage bucket name | `videos` |
| `SECRET_KEY` | Flask secret key | `your-secret-key` |
| `DATABASE_URL` | PostgreSQL URL (auto-set by Heroku) | `postgresql://...` |

## Deployment Steps

1. Fork/clone this repository
2. Set up Supabase project and storage bucket
3. Deploy to Heroku via GitHub integration
4. Set environment variables in Heroku dashboard
5. Your app will now have persistent video storage!