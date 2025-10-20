from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    time_str = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)
    attendees = db.relationship('Attendee', backref='event', cascade='all, delete-orphan')

class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='attendee')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_admin_user(self):
        return (self.role == 'admin') or bool(self.is_admin)

    @property
    def is_organizer_user(self):
        return self.role == 'organizer'