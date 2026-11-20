"""
Courier Management System
Main entry point - initializes database and launches the login window.
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import initialize_database
from views.login_view import LoginWindow


def main():
    """Initialize database and launch the application."""
    # Ensure database tables and initial seed data exist
    initialize_database()

    # Launch desktop application GUI
    app = LoginWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
