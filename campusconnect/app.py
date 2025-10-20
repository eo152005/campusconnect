from models import Event, Attendee, User  # Changed from 'model' to 'models'
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
import os
from database import db
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
# --- END NEW IMPORTS ---

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campusconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-me'

db.init_app(app)

# --- NEW: Initialize Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Route to redirect unauthorized users
# --- END NEW: Initialize Flask-Login ---

# Import models after db is created and bound to the app

# --- NEW: User Loader for Flask-Login ---


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# --- END NEW: User Loader ---


# --- Routes ---
@app.route('/')
def index():
    # Auto-clean past events before listing
    cleanup_past_events()
    q = request.args.get('q', '').strip().lower()
    events = Event.query.order_by(Event.date).all()
    if q:
        events = [e for e in events if q in e.title.lower() or (
            e.description and q in e.description.lower())]
    return render_template('index.html', events=events, request=request, year=datetime.now().year)


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    e = Event.query.get_or_404(event_id)
    return render_template('event.html', event=e, year=datetime.now().year)

# --- NEW: Delete Event Route ---


@app.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    if not current_user.is_admin_user:
        flash('Only admins can delete events.', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))
    e = Event.query.get_or_404(event_id)
    db.session.delete(e)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('index'))

# --- SECURED ROUTE ---


@app.route('/create', methods=['GET', 'POST'])
@login_required  # Requires a logged-in user
def create_event():
    if not (current_user.is_admin_user or getattr(current_user, 'is_organizer_user', False)):
        flash('Only organizers or admins can create events.', 'danger')
        return redirect(url_for('index'))
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

# --- SECURED ROUTE ---


@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required  # Requires a logged-in user
def edit_event(event_id):
    if not (current_user.is_admin_user or getattr(current_user, 'is_organizer_user', False)):
        flash('Only organizers or admins can edit events.', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))
    e = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        e.title = request.form['title']
        e.category = request.form.get('category')

        date_raw = request.form['date']
        try:
            e.date = datetime.strptime(date_raw, '%Y-%m-%d')
        except Exception:
            flash('Invalid date format', 'danger')
            return redirect(url_for('edit_event', event_id=event_id))

        e.time_str = request.form.get('time_str')
        e.location = request.form.get('location')
        e.description = request.form.get('description')
        e.image = request.form.get('image') or e.image

        try:
            db.session.commit()
            flash('Event updated successfully', 'success')
            return redirect(url_for('event_detail', event_id=e.id))
        except Exception as error:
            db.session.rollback()
            flash(f'Error updating event: {error}', 'danger')
            return redirect(url_for('edit_event', event_id=event_id))

    return render_template('edit.html', event=e, year=datetime.now().year)


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

# --- NEW: Authentication Routes ---


@app.route('/user/register', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first() is not None:
            flash('Username already taken.', 'danger')
            return render_template('register.html', year=datetime.now().year)

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', year=datetime.now().year)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html', year=datetime.now().year)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
# --- END NEW: Authentication Routes ---


@app.route('/calendar')
def calendar():
    # Auto-clean past events before listing
    cleanup_past_events()
    events = Event.query.order_by(Event.date).all()
    return render_template('calendar.html', events=events, year=datetime.now().year)

# --- DB initialization & seeding ---


def seed_if_empty():
    if Event.query.count() == 0:
        # Note: New User model requires an initial user for testing secured routes
        admin = User(username='admin', email='admin@campus.edu', role='admin')
        admin.set_password('password')  # Use 'password' for easy testing
        db.session.add(admin)

        e1 = Event(title='Annual Tech Fest 2024', category='Academic',
                   date=datetime(2024, 10, 26), time_str='09:00', location='Main Auditorium',
                   description='Join us for the biggest tech fest of the year...',
                   image='images/event1.jpg')
        e2 = Event(title='Startup Pitch Night', category='Workshop',
                   date=datetime(2024, 11, 15), time_str='18:30',
                   location='Innovation Hub, Room 201',
                   description='Pitch your startup ideas to a panel...',
                   image='images/event2.jpg')
        e3 = Event(title='University Soccer Championship', category='Sports',
                   date=datetime(2024, 11, 2), time_str='14:00',
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

        db.create_all()

        # Ensure schema has the new columns when upgrading existing DBs
        ensure_schema()

        if need_init:
            seed_if_empty()
            print(
                'Database created and seeded: campusconnect.db (Includes test User: admin/password)')

    app.run(debug=True)
   

# --- Admin & Maintenance Utilities ---

def cleanup_past_events():
    """Delete events whose date is strictly before today."""
    try:
        # Compare only date portion to avoid timezone confusion
        today = datetime.now()
        Event.query.filter(Event.date < today).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()


def ensure_schema():
    """Best-effort lightweight migration to add missing columns."""
    try:
        # Works for SQLite; harmless on others when supported
        engine = db.get_engine()
        with engine.connect() as conn:
            # Check for 'role' column in user table
            result = conn.exec_driver_sql("PRAGMA table_info('user')")
            columns = [row[1] for row in result]
            if 'role' not in columns:
                conn.exec_driver_sql("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'attendee'")
    except Exception:
        # Do not crash app if migration fails; developer can recreate DB
        pass


# --- Admin: User Management ---

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin_user:
        flash('Admins only.', 'danger')
        return redirect(url_for('index'))
    users = User.query.order_by(User.username).all()
    return render_template('admin_users.html', users=users, year=datetime.now().year)


@app.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
def set_user_role(user_id):
    if not current_user.is_admin_user:
        flash('Admins only.', 'danger')
        return redirect(url_for('admin_users'))
    target = User.query.get_or_404(user_id)
    new_role = request.form.get('role', 'attendee')
    if new_role not in ('attendee', 'organizer', 'admin'):
        flash('Invalid role.', 'danger')
        return redirect(url_for('admin_users'))

    # Prevent removing the last admin
    if target.role == 'admin' and new_role != 'admin':
        num_admins = User.query.filter_by(role='admin').count()
        if num_admins <= 1:
            flash('Cannot remove the last remaining admin.', 'warning')
            return redirect(url_for('admin_users'))

    target.role = new_role
    # Keep legacy flag in sync for now
    target.is_admin = (new_role == 'admin')
    try:
        db.session.commit()
        flash(f"Updated role for {target.username} to {new_role}.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating role: {e}', 'danger')
    return redirect(url_for('admin_users'))
  