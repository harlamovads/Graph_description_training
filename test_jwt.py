# create file: migrate_exercise_status.py
from app import create_app
from backend.models import db
from sqlalchemy import text

def migrate_exercise_status():
    app = create_app()
    
    with app.app_context():
        try:
            # Add the status column
            db.session.execute(text("ALTER TABLE exercises ADD COLUMN status VARCHAR(20) DEFAULT 'draft'"))
            
            # Update existing exercises to be published (so they remain visible to students)
            db.session.execute(text("UPDATE exercises SET status = 'published' WHERE status IS NULL OR status = 'draft'"))
            
            db.session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_exercise_status()