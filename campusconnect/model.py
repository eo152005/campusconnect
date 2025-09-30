from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import db  # Assumes 'db' is already imported from your new database.py
from models import Event, Attendee, User


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    time_str = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)  # path under static/
    attendees = db.relationship(
        'Attendee', backref='event', cascade='all, delete-orphan')


class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

# --- NEW: User Model for Authentication ---


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Stores the hashed password
    is_admin = db.Column(db.Boolean, default=False)  # Admin flag

    def set_password(self, password):
        """Hashes the password before storing it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks a plain password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_admin_user(self):
        return self.is_admin
