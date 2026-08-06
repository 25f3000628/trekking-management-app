from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    db.create_all()  # creates all tables programmatically — satisfies "no manual DB creation" rule

    # Seed the one pre-existing Admin, only if it doesn't already exist
    existing_admin = User.query.filter_by(role="admin").first()
    if not existing_admin:
        admin = User(
            name="System Admin",
            email="admin@trekapp.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            status="active",
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created: admin@trekapp.com / admin123")
    else:
        print("Admin already exists, skipping seed.")

    print("Database initialized at trekking.db")