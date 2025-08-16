# create_tables.py

# This script is designed to be run once to set up your database tables.

from app.db.base import Base, engine
from app.db.models import Store, Product # Import all your models here

def main():
    """
    Connects to the database and creates all tables based on the defined models.
    """
    print("Connecting to the database to create tables...")

    # A safety check to ensure we have an engine configured
    if not engine:
        print("Database engine not configured. Please check your .env file and DATABASE_URL.")
        return

    try:
        # This is the magic command that creates the tables.
        # It looks at all the classes that inherit from 'Base' and creates
        # the corresponding tables in the database.
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        print("You can now run the FastAPI application.")

    except Exception as e:
        print(f"An error occurred while creating tables: {e}")
        print("Please check your database connection string in the .env file and ensure the database server is running.")

if __name__ == "__main__":
    main()