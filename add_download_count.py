#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

def add_download_count():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(database_url)
    
    print("Adding download_count column to document table...")
    
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE document 
                ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0
            """))
            conn.commit()
            print("✅ download_count column added")
            
            result = conn.execute(text("""
                UPDATE document 
                SET download_count = 0 
                WHERE download_count IS NULL
            """))
            conn.commit()
            print(f"✅ Updated {result.rowcount} documents")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

if __name__ == '__main__':
    add_download_count()
