import os
from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create new tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Database reset successfully!")
        print("Admin user created:")
        print("Username: admin")
        print("Password: admin123")

if __name__ == '__main__':
    reset_database()
