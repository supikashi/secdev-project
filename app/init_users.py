"""
Initialize default users (alice and bob) in the database.
This script should be run once after database setup.
"""

from database import create_user_db, get_user_by_username_db, init_db


def init_default_users():
    """Create default users if they don't exist."""
    # Initialize database tables
    init_db()

    # Create alice if not exists
    if not get_user_by_username_db("alice"):
        user = create_user_db("alice", "alicepass")
        if user:
            print(f"Created user: alice (id={user['id']})")
        else:
            print("Failed to create user: alice")
    else:
        print("User alice already exists")

    # Create bob if not exists
    if not get_user_by_username_db("bob"):
        user = create_user_db("bob", "bobpass")
        if user:
            print(f"Created user: bob (id={user['id']})")
        else:
            print("Failed to create user: bob")
    else:
        print("User bob already exists")


if __name__ == "__main__":
    init_default_users()
