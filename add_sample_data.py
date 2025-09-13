#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app
from src.models.user import db
from src.models.content import VideoContent, TextContent

def add_sample_data():
    with app.app_context():
        # Clear existing data
        VideoContent.query.delete()
        TextContent.query.delete()
        
        # Add sample video content
        video1 = VideoContent(
            title='Big Buck Bunny',
            description='A short computer-animated comedy film featuring a giant rabbit. This is a sample video to demonstrate the video functionality.',
            video_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            thumbnail_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/BigBuckBunny.jpg',
            is_published=True,
            order_index=1
        )
        
        video2 = VideoContent(
            title='Elephants Dream',
            description='A surreal short film about two characters exploring a strange mechanical world. Another sample video with different content.',
            video_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
            thumbnail_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ElephantsDream.jpg',
            is_published=True,
            order_index=2
        )
        
        # Add sample text content
        text1 = TextContent(
            title='Welcome to Content Hub',
            excerpt='Learn about our amazing content management system and how it can help you showcase your creative work.',
            content='''Welcome to Content Hub, your one-stop destination for amazing videos and articles. Our platform allows you to easily manage and display your creative content in a beautiful, modern interface.

Whether you are sharing short films, tutorials, or written stories, Content Hub provides the tools you need to showcase your work professionally. The platform features:

• A clean, responsive design that works on all devices
• Easy content management through the admin panel
• Support for both video and text content
• Customizable ordering and publishing controls
• Modern web technologies for fast loading

Start exploring and see what Content Hub can do for your creative projects!''',
            is_published=True,
            order_index=1
        )
        
        text2 = TextContent(
            title='Getting Started Guide',
            excerpt='A comprehensive guide to using the admin panel and managing your content effectively.',
            content='''Getting started with Content Hub is easy! Here is a step-by-step guide to help you make the most of your content management system:

## Admin Panel Access
Access the admin panel by navigating to /admin.html in your browser. This is where you'll manage all your content.

## Adding Videos
1. Click on the "Videos" tab in the admin panel
2. Fill in the video title (required)
3. Provide the video URL (required) - this should be a direct link to your video file
4. Add a thumbnail URL (optional) for a preview image
5. Write a description to help visitors understand your content
6. Set the order index to control display order (higher numbers appear first)
7. Toggle the "Published" checkbox to control visibility

## Creating Articles
1. Switch to the "Articles" tab
2. Enter a compelling title for your article
3. Write an excerpt that summarizes your content
4. Add your full article content in the main text area
5. Set the order index and publishing status as needed

## Tips for Success
• Use descriptive titles that capture attention
• Write engaging excerpts to encourage readers to click
• Order your content strategically using the order index
• Preview your changes on the main site regularly

Your content will automatically appear on the main website for visitors to enjoy. Happy content creating!''',
            is_published=True,
            order_index=2
        )
        
        # Add all content to the database
        db.session.add_all([video1, video2, text1, text2])
        db.session.commit()
        
        print('Sample data added successfully!')
        print(f'Added {VideoContent.query.count()} videos')
        print(f'Added {TextContent.query.count()} articles')

if __name__ == '__main__':
    add_sample_data()
