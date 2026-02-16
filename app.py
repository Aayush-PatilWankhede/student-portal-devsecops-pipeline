"""
Student Portal Web Application
A secure Flask-based student management system with role-based access control
"""
import os
import logging
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from config import Config, allowed_file
from prometheus_flask_exporter import PrometheusMetrics

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)

# Initialize database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(
    level=getattr(logging, app.config['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(app.config['LOG_FILE']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['BASE_DIR'], 'database'), exist_ok=True)

# ===== DATABASE MODELS =====

class User(db.Model):
    """User model for both students and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    year = db.Column(db.Integer)
    role = db.Column(db.String(20), default='student')  # 'student' or 'admin'
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('Assignment', backref='user', lazy=True, foreign_keys='Assignment.user_id')
    feedback = db.relationship('Feedback', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Assignment(db.Model):
    """Assignment model for file uploads and grading"""
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    grade = db.Column(db.String(10))  # e.g., 'A', 'B+', '95%'
    comments = db.Column(db.Text)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    graded_at = db.Column(db.DateTime)
    
    grader = db.relationship('User', foreign_keys=[graded_by])
    
    def __repr__(self):
        return f'<Assignment {self.filename}>'

class Announcement(db.Model):
    """Announcement model for admin posts"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    
    creator = db.relationship('User', backref='announcements')
    
    def __repr__(self):
        return f'<Announcement {self.title}>'

class Feedback(db.Model):
    """Feedback model for student submissions"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.subject}>'

class Notification(db.Model):
    """Notification model for user alerts"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.id}>'

# ===== AUTHENTICATION DECORATORS =====

def login_required(f):
    """Decorator to protect routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            logger.warning(f'Unauthorized admin access attempt by user {session.get("user_id")}')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ===== HELPER FUNCTIONS =====

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(app.config['BCRYPT_LOG_ROUNDS'])).decode('utf-8')

def check_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, "Password is strong"

# ===== PUBLIC ROUTES =====

@app.route('/')
def index():
    """Home page - redirects based on authentication"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Student registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', '').strip()
        year = request.form.get('year', type=int)
        
        # Validation
        if not all([name, email, password, department, year]):
            flash('All fields are required', 'danger')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        # Password strength validation
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            flash(message, 'danger')
            return render_template('signup.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            logger.warning(f'Signup attempt with existing email: {email}')
            return render_template('signup.html')
        
        # Create new user
        hashed_password = hash_password(password)
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            department=department,
            year=year,
            role='student'
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            logger.info(f'New user registered: {email}')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'danger')
            logger.error(f'Registration error: {str(e)}')
            return render_template('signup.html')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not all([email, password]):
            flash('Email and password are required', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password(password, user.password):
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Set session
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            if remember:
                session.permanent = True
            
            flash(f'Welcome back, {user.name}!', 'success')
            logger.info(f'Successful login: {email}')
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            logger.warning(f'Failed login attempt: {email}')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}!', 'info')
    logger.info(f'User logged out: {user_name}')
    return redirect(url_for('login'))

# ===== STUDENT ROUTES =====

@app.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard"""
    user = User.query.get(session['user_id'])
    
    # Get recent announcements (top 3)
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    
    # Get assignment count
    assignment_count = Assignment.query.filter_by(user_id=user.id).count()
    
    # Get unread notifications count
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    
    return render_template('dashboard.html', 
                         user=user, 
                         announcements=recent_announcements,
                         assignment_count=assignment_count,
                         unread_count=unread_count)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update user profile"""
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.name = request.form.get('name', '').strip()
        user.department = request.form.get('department', '').strip()
        user.year = request.form.get('year', type=int)
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
            logger.info(f'Profile updated: {user.email}')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile', 'danger')
            logger.error(f'Profile update error: {str(e)}')
    
    return render_template('profile.html', user=user)

@app.route('/assignments')
@login_required
def assignments():
    """View student assignments with grades"""
    user_assignments = Assignment.query.filter_by(user_id=session['user_id']).order_by(Assignment.upload_date.desc()).all()
    return render_template('assignments.html', assignments=user_assignments)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload assignment file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid duplicates
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session['user_id']}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                
                # Create assignment record
                assignment = Assignment(
                    user_id=session['user_id'],
                    filename=filename
                )
                db.session.add(assignment)
                db.session.commit()
                
                flash('File uploaded successfully', 'success')
                logger.info(f'File uploaded: {filename} by user {session["user_id"]}')
                return redirect(url_for('assignments'))
            except Exception as e:
                flash('Error uploading file', 'danger')
                logger.error(f'Upload error: {str(e)}')
                return redirect(request.url)
        else:
            flash('Invalid file type. Only PDF, DOC, and DOCX files are allowed.', 'danger')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/download/<filename>')
@login_required
def download(filename):
    """Download uploaded file"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        flash('File not found', 'danger')
        logger.error(f'Download error: {str(e)}')
        return redirect(url_for('assignments'))

@app.route('/delete/<int:assignment_id>')
@login_required
def delete_assignment(assignment_id):
    """Delete assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if user owns this assignment or is admin
    if assignment.user_id != session['user_id'] and session.get('user_role') != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('assignments'))
    
    try:
        # Delete file from filesystem
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], assignment.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Delete database record
        db.session.delete(assignment)
        db.session.commit()
        
        flash('Assignment deleted successfully', 'success')
        logger.info(f'Assignment deleted: {assignment.filename}')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting assignment', 'danger')
        logger.error(f'Delete error: {str(e)}')
    
    return redirect(url_for('assignments'))

@app.route('/announcements')
@login_required
def announcements():
    """View all announcements with search/filter"""
    search_query = request.args.get('search', '').strip()
    
    query = Announcement.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Announcement.title.contains(search_query),
                Announcement.message.contains(search_query)
            )
        )
    
    all_announcements = query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=all_announcements, search_query=search_query)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    """Submit feedback"""
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        rating = request.form.get('rating', type=int)
        
        if not all([subject, message, rating]) or rating not in range(1, 6):
            flash('All fields are required and rating must be between 1-5', 'danger')
            return render_template('feedback.html')
        
        new_feedback = Feedback(
            user_id=session['user_id'],
            subject=subject,
            message=message,
            rating=rating
        )
        
        try:
            db.session.add(new_feedback)
            db.session.commit()
            flash('Feedback submitted successfully', 'success')
            logger.info(f'Feedback submitted by user {session["user_id"]}')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting feedback', 'danger')
            logger.error(f'Feedback error: {str(e)}')
    
    return render_template('feedback.html')

@app.route('/notifications')
@login_required
def notifications():
    """View user notifications"""
    user_notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return render_template('notifications.html', notifications=user_notifications, unread_count=unread_count)

@app.route('/mark_read/<int:notification_id>')
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != session['user_id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('notifications'))
    
    notification.is_read = True
    db.session.commit()
    
    return redirect(url_for('notifications'))

@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    """Reset user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        user = User.query.get(session['user_id'])
        
        if not check_password(current_password, user.password):
            flash('Current password is incorrect', 'danger')
            return render_template('reset_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('reset_password.html')
        
        # Validate new password strength
        is_strong, message = validate_password_strength(new_password)
        if not is_strong:
            flash(message, 'danger')
            return render_template('reset_password.html')
        
        user.password = hash_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        logger.info(f'Password reset by user {user.email}')
        return redirect(url_for('profile'))
    
    return render_template('reset_password.html')

# ===== ADMIN ROUTES =====

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    stats = {
        'total_students': User.query.filter_by(role='student').count(),
        'total_assignments': Assignment.query.count(),
        'total_announcements': Announcement.query.count(),
        'total_feedback': Feedback.query.count(),
        'ungraded_assignments': Assignment.query.filter_by(grade=None).count()
    }
    
    # Recent activity
    recent_assignments = Assignment.query.order_by(Assignment.upload_date.desc()).limit(5).all()
    recent_feedback = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', stats=stats, recent_assignments=recent_assignments, recent_feedback=recent_feedback)

@app.route('/admin/students')
@admin_required
def admin_students():
    """View all students"""
    all_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).all()
    return render_template('admin_students.html', students=all_students)

@app.route('/admin/student/<int:student_id>')
@admin_required
def admin_student_detail(student_id):
    """View student details"""
    student = User.query.get_or_404(student_id)
    student_assignments = Assignment.query.filter_by(user_id=student_id).all()
    student_feedback = Feedback.query.filter_by(user_id=student_id).all()
    
    return render_template('admin_student_detail.html', student=student, assignments=student_assignments, feedback=student_feedback)

@app.route('/admin/assignments')
@admin_required
def admin_assignments():
    """View all assignments"""
    all_assignments = Assignment.query.order_by(Assignment.upload_date.desc()).all()
    return render_template('admin_assignments.html', assignments=all_assignments)

@app.route('/admin/grade/<int:assignment_id>', methods=['GET', 'POST'])
@admin_required
def admin_grade(assignment_id):
    """Grade assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if request.method == 'POST':
        grade = request.form.get('grade', '').strip()
        comments = request.form.get('comments', '').strip()
        
        assignment.grade = grade
        assignment.comments = comments
        assignment.graded_by = session['user_id']
        assignment.graded_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            # Send notification to student
            notification = Notification(
                user_id=assignment.user_id,
                message=f'Your assignment "{assignment.filename}" has been graded: {grade}'
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Assignment graded successfully', 'success')
            logger.info(f'Assignment {assignment_id} graded by admin {session["user_id"]}')
            return redirect(url_for('admin_assignments'))
        except Exception as e:
            db.session.rollback()
            flash('Error grading assignment', 'danger')
            logger.error(f'Grading error: {str(e)}')
    
    return render_template('admin_grade.html', assignment=assignment)

@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    """Manage announcements"""
    all_announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin_announcements.html', announcements=all_announcements)

@app.route('/admin/announcement/create', methods=['GET', 'POST'])
@admin_required
def admin_create_announcement():
    """Create announcement"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        
        if not all([title, message]):
            flash('Title and message are required', 'danger')
            return render_template('admin_create_announcement.html')
        
        announcement = Announcement(
            title=title,
            message=message,
            created_by=session['user_id']
        )
        
        try:
            db.session.add(announcement)
            db.session.commit()
            flash('Announcement created successfully', 'success')
            logger.info(f'Announcement created by admin {session["user_id"]}')
            return redirect(url_for('admin_announcements'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating announcement', 'danger')
            logger.error(f'Announcement creation error: {str(e)}')
    
    return render_template('admin_create_announcement.html')

@app.route('/admin/announcement/edit/<int:announcement_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_announcement(announcement_id):
    """Edit announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title', '').strip()
        announcement.message = request.form.get('message', '').strip()
        announcement.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('Announcement updated successfully', 'success')
            logger.info(f'Announcement {announcement_id} updated by admin {session["user_id"]}')
            return redirect(url_for('admin_announcements'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating announcement', 'danger')
            logger.error(f'Announcement update error: {str(e)}')
    
    return render_template('admin_edit_announcement.html', announcement=announcement)

@app.route('/admin/announcement/delete/<int:announcement_id>')
@admin_required
def admin_delete_announcement(announcement_id):
    """Delete announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully', 'success')
        logger.info(f'Announcement {announcement_id} deleted by admin {session["user_id"]}')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting announcement', 'danger')
        logger.error(f'Announcement deletion error: {str(e)}')
    
    return redirect(url_for('admin_announcements'))

@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    """View all feedback"""
    rating_filter = request.args.get('rating', type=int)
    
    query = Feedback.query
    if rating_filter:
        query = query.filter_by(rating=rating_filter)
    
    all_feedback = query.order_by(Feedback.created_at.desc()).all()
    return render_template('admin_feedback.html', feedback=all_feedback, rating_filter=rating_filter)

@app.route('/admin/notifications', methods=['GET', 'POST'])
@admin_required
def admin_notifications():
    """Send notifications to students"""
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        recipient_type = request.form.get('recipient_type', 'all')
        student_id = request.form.get('student_id', type=int)
        
        if not message:
            flash('Message is required', 'danger')
            return render_template('admin_notifications.html', students=User.query.filter_by(role='student').all())
        
        try:
            if recipient_type == 'all':
                # Send to all students
                students = User.query.filter_by(role='student').all()
                for student in students:
                    notification = Notification(user_id=student.id, message=message)
                    db.session.add(notification)
                flash(f'Notification sent to all {len(students)} students', 'success')
                logger.info(f'Notification sent to all students by admin {session["user_id"]}')
            else:
                # Send to specific student
                notification = Notification(user_id=student_id, message=message)
                db.session.add(notification)
                flash('Notification sent successfully', 'success')
                logger.info(f'Notification sent to student {student_id} by admin {session["user_id"]}')
            
            db.session.commit()
            return redirect(url_for('admin_notifications'))
        except Exception as e:
            db.session.rollback()
            flash('Error sending notification', 'danger')
            logger.error(f'Notification error: {str(e)}')
    
    students = User.query.filter_by(role='student').all()
    return render_template('admin_notifications.html', students=students)

# ===== UTILITY ROUTES =====

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = 'disconnected'
        logger.error(f'Health check database error: {str(e)}')
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status
    })

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    logger.warning(f'404 error: {request.url}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    logger.error(f'500 error: {str(e)}')
    db.session.rollback()
    return render_template('500.html'), 500

# ===== DATABASE INITIALIZATION =====

def init_db():
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        admin = User.query.filter_by(email='admin@student-portal.com').first()
        if not admin:
            admin = User(
                name='System Administrator',
                email='admin@student-portal.com',
                password=hash_password('Admin@123'),
                department='Administration',
                year=0,
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            logger.info('Default admin account created')
            print('Default admin account created:')
            print('Email: admin@student-portal.com')
            print('Password: Admin@123')
        
        logger.info('Database initialized successfully')

# ===== MAIN =====

if __name__ == '__main__':
    init_db()
    print('Starting Student Portal on http://0.0.0.0:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)
