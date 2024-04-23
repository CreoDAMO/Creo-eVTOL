# Import necessary libraries
from flask import Flask, request, jsonify, abort, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import os
import jwt
import datetime
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import hashlib
import secrets
from flask_askpass import AskPass
import snort_integration_library as snort

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'eVTOL.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Secret key for JWT
app.config['SECRET_KEY'] = 'your_secret_key'

# Rate limiting setup
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per day", "20 per hour"]
)

# Risk-based authentication with Flask-Askpass
askpass = AskPass(app)

# Define database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define database schemas
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'role')

user_schema = UserSchema()
users_schema = UserSchema(many=True)

# Middleware for validating JSON requests
@app.before_request
def validate_json():
    if request.method == "POST" and not request.is_json:
        abort(400, description="Missing JSON in request")

# Custom validation error handler
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify(error.messages), 400

# JWT token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Hash or truncate IP addresses for privacy
def hash_ip(ip):
    # Hash the IP address using SHA-256
    return hashlib.sha256(ip.encode()).hexdigest()

# Seeded random token regeneration on refresh
def generate_refresh_token(user_id):
    # Generate a seeded random token using user ID and current time
    random_seed = f"{user_id}{datetime.datetime.utcnow()}"
    token = secrets.token_hex(32)
    return hashlib.sha256((token + random_seed).encode()).hexdigest()

# Routes
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if 'username' not in data or 'password' not in data:
        abort(400, description="Username or password missing")
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'New user created!'}), 201

@app.route('/login', methods=['POST'])
@askpass.ask('geolocation', 'device_fingerprinting')
def login_user():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    user = User.query.filter_by(username=auth.username).first()
    if not user or not user.check_password(auth.password):
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    token = jwt.encode({'id': user.id, 'role': user.role, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    refresh_token = generate_refresh_token(user.id)
    return jsonify({'token': token, 'refresh_token': refresh_token})

# Protected route example
@app.route('/user', methods=['GET'])
@token_required
def get_current_user(current_user):
    return user_schema.jsonify(current_user)

# Logout route
@app.route('/logout', methods=['POST'])
@token_required
def logout_user(current_user):
    # Invalidate token by not returning a new one
    return jsonify({'message': 'Logout successful!'})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
