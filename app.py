import os
from flask import Flask
from flask_login import LoginManager
from models import db, User
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp
from routes.user_routes import user_bp

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'trekking.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # blueprint route added in Milestone 2

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints will be registered here in later milestones:
    # from routes.auth_routes import auth_bp
    # from routes.admin_routes import admin_bp
    # from routes.staff_routes import staff_bp
    # from routes.user_routes import user_bp
    # app.register_blueprint(auth_bp)
    # app.register_blueprint(admin_bp)
    # app.register_blueprint(staff_bp)
    # app.register_blueprint(user_bp)
    
    app.register_blueprint(user_bp)   
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)