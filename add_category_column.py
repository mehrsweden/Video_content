#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

def add_category_columns():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(database_url)
    
    print("=" * 60)
    print("ADDING CATEGORY COLUMNS")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            print("Adding category to video_content...")
            conn.execute(text("""
                ALTER TABLE video_content 
                ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'Miscellaneous'
            """))
            conn.commit()
            print("✅ video_content.category added")
            
            print("Adding category to document...")
            conn.execute(text("""
                ALTER TABLE document 
                ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'Miscellaneous'
            """))
            conn.commit()
            print("✅ document.category added")
            
            print("\nUpdating existing records...")
            result = conn.execute(text("""
                UPDATE video_content 
                SET category = 'Miscellaneous' 
                WHERE category IS NULL OR category = ''
            """))
            conn.commit()
            print(f"✅ Updated {result.rowcount} videos")
            
            result = conn.execute(text("""
                UPDATE document 
                SET category = 'Miscellaneous' 
                WHERE category IS NULL OR category = ''
            """))
            conn.commit()
            print(f"✅ Updated {result.rowcount} documents")
            
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

if __name__ == '__main__':
    add_category_columns()
