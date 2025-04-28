import os
import subprocess
import sys

def init_migrations():
    print("Initializing database migrations...")
    
    # Create alembic directory if it doesn't exist
    if not os.path.exists("alembic"):
        subprocess.run(["alembic", "init", "alembic"])
        print("Alembic initialized.")
    
    # Create initial migration
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial migration"])
    print("Initial migration created.")
    
    # Apply migrations
    subprocess.run(["alembic", "upgrade", "head"])
    print("Migrations applied.")

if __name__ == "__main__":
    init_migrations()
