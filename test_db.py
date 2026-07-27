import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

def test_connection():
    database_url = settings.get("DATABASE_URL")
    print(f"Testing connection to: {database_url}")
    
    try:
        # Create an engine
        engine = create_engine(database_url)
        
        # Try to connect
        with engine.connect() as connection:
            print("Successfully connected to the database!")
            
    except SQLAlchemyError as e:
        print("Failed to connect to the database.")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
