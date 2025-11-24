#!/usr/bin/env python3
"""
Database Migration Script: Add Category Column
"""

import os
import sys

def migrate_database():
    print("=" * 60)
    print("DATABASE MIGRATION: Adding Category Support")
    print("=" * 60)
    print()
    
    from main import app, db, VideoContent, Document
    
    with app.app_context():
        try:
            print("Step 1: Creating database tables with new schema...")
            db.create_all()
            print("✅ Tables created/updated successfully")
            print()
            
            print("Step 2: Checking existing records...")
            
            # Update videos without categories
            videos_without_category = VideoContent.query.filter(
                (VideoContent.category == None) | (VideoContent.category == '')
            ).all()
            
            if videos_without_category:
                print(f"Found {len(videos_without_category)} videos without categories")
                for video in videos_without_category:
                    video.category = 'Miscellaneous'
                    print(f"  - Updated: {video.title}")
                
                db.session.commit()
                print("✅ All videos updated with default category")
            else:
                print("✅ All videos already have categories")
            
            print()
            
            # Update documents without categories
            documents_without_category = Document.query.filter(
                (Document.category == None) | (Document.category == '')
            ).all()
            
            if documents_without_category:
                print(f"Found {len(documents_without_category)} documents without categories")
                for doc in documents_without_category:
                    doc.category = 'Miscellaneous'
                    print(f"  - Updated: {doc.title}")
                
                db.session.commit()
                print("✅ All documents updated with default category")
            else:
                print("✅ All documents already have categories")
            
            print()
            print("=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print()
            print(f"Total Videos: {VideoContent.query.count()}")
            print(f"Total Documents: {Document.query.count()}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate_database()
