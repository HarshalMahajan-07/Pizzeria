from flask import Flask
from routes.auth_routes import auth_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # required for sessions

app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(debug=True)
