from flask import Flask
import os

def create_app():
    app = Flask(__name__)

    # Secret key for session management
    # In a real app, use a strong, randomly generated key stored securely.
    # For this project, we'll use a simple one or generate one if not set.
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-for-light-novel-app')

    # Ensure the instance folder exists if you plan to use it for SQLite DB, etc.
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # Register blueprints here, if any (none for now)
    from . import routes
    app.register_blueprint(routes.bp)

    return app
