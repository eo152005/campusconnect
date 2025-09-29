from flask import Flask, render_template, request, redirect, url_for, flash
# from flask_sqlalchemy import SQLAlchemy  <-- REMOVE THIS LINE
from datetime import datetime
import os

# --- NEW: Import db from new file ---
from database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campusconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-me'

# --- NEW: Bind db to app ---
db.init_app(app)


# Import models after db is created and bound to the app
from models import Event, Attendee

# --- Routes ---
@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    events = Event.query.order_by(Event.date).all()
    if q:
        events = [e for e in events if q in e.title.lower() or (e.description and q in e.description.lower())]
    return render_template('index.html', events=events, request=request, year=datetime.now().year)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    e = Event.query.get_or_404(event_id)
    return render_template('event.html', event=e, year=datetime.now().year)

@app.route('/create', methods=['GET','POST'])
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        category = request.form.get('category')
        date_raw = request.form['date']
        time_str = request.form.get('time_str')
        location = request.form.get('location')
        description = request.form.get('description')
        image = request.form.get('image') or 'images/event1.jpg'
        try:
            date = datetime.strptime(date_raw, '%Y-%m-%d')
        except Exception:
            flash('Invalid date', 'danger')
            return redirect(url_for('create_event'))
        e = Event(title=title, category=category, date=date, time_str=time_str,
                  location=location, description=description, image=image)
        db.session.add(e)
        db.session.commit()
        flash('Event created', 'success')
        return redirect(url_for('index'))
    return render_template('create.html', year=datetime.now().year)

@app.route('/register/<int:event_id>', methods=['POST'])
def register(event_id):
    e = Event.query.get_or_404(event_id)
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        flash('Name and email required', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))
    a = Attendee(name=name, email=email, event=e)
    db.session.add(a)
    db.session.commit()
    flash('Registered successfully', 'success')
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/calendar')
def calendar():
    events = Event.query.order_by(Event.date).all()
    return render_template('calendar.html', events=events, year=datetime.now().year)

# --- DB initialization & seeding ---
def seed_if_empty():
    if Event.query.count() == 0:
        e1 = Event(title='Annual Tech Fest 2024', category='Academic',
                   date=datetime(2024,10,26), time_str='09:00', location='Main Auditorium',
                   description='Join us for the biggest tech fest of the year...',
                   image='images/event1.jpg')
        e2 = Event(title='Startup Pitch Night', category='Workshop',
                   date=datetime(2024,11,15), time_str='18:30',
                   location='Innovation Hub, Room 201',
                   description='Pitch your startup ideas to a panel...',
                   image='images/event2.jpg')
        e3 = Event(title='University Soccer Championship', category='Sports',
                   date=datetime(2024,11,2), time_str='14:00',
                   location='North Campus Stadium',
                   description='Inter-department soccer tournament.',
                   image='images/event3.jpg')
        db.session.add_all([e1, e2, e3])
        db.session.commit()

if __name__ == '__main__':
    # Initialize the database within the application context
    with app.app_context():
        # Check if the database file needs to be created
        need_init = not os.path.exists('campusconnect.db')
        
        # This is where the error occurred, now it's inside the context
        db.create_all() 
        
        if need_init:
            seed_if_empty()
            print('Database created and seeded: campusconnect.db')
    
    # Run the application (this automatically handles the context for routes)
    app.run(debug=True)