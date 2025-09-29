
from database import db

class Event(db.Model):
# ... rest of models.py remains the same ...
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    time_str = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)  # path under static/
    attendees = db.relationship('Attendee', backref='event', cascade='all, delete-orphan')

class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
