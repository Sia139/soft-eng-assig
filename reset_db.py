from app import app, db  # Import the Flask app and `db` object from your application

def reset_database():
    print("Resetting the database...")
    
    # Use the application context
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        print("All tables dropped.")
        
        # # Recreate all tables
        # db.create_all()
        # print("All tables recreated.")

if __name__ == "__main__":
    reset_database()
