from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables from .env file, especially FLASK_SECRET_KEY and GEMINI_API_KEY
# Ensure .env is in the same directory as run.py (i.e., light_novel_generator/.env)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"Loaded environment variables from {dotenv_path}")
else:
    print(f"Warning: .env file not found at {dotenv_path}. Make sure it exists with necessary API keys.")


app = create_app()

if __name__ == '__main__':
    # For development, Flask's built-in server is fine.
    # Debug mode should be False in production.
    # Host '0.0.0.0' makes it accessible on the network.
    app.run(debug=True, host='0.0.0.0', port=5000)
