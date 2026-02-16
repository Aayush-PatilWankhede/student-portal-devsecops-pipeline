# Student Portal Web Application

A secure, feature-rich Flask-based student management system designed with DevSecOps principles in mind. This application provides role-based access control for students and administrators, assignment management with grading, announcements, feedback, and real-time notifications.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Features

### Authentication & Security
- ✅ Secure user registration and login
- ✅ Role-based access control (Student/Admin)
- ✅ Password hashing with bcrypt (12 rounds)
- ✅ Password strength validation
- ✅ Session management with secure cookies
- ✅ "Remember me" functionality
- ✅ Password reset capability
- ✅ Last login tracking

### Student Features
- 📊 **Dashboard**: Overview with statistics, recent announcements, and quick actions
- 👤 **Profile Management**: Update personal information and change password
- 📄 **Assignment System**: Upload files (PDF/DOC/DOCX), download, delete, view grades
- 📢 **Announcements**: View announcements with search and filter functionality
- 💬 **Feedback System**: Submit feedback with 1-5 star ratings
- 🔔 **Notifications**: Real-time notifications with unread badges

### Admin Features
- 🎛️ **Admin Dashboard**: System statistics and recent activity overview
- 👥 **Student Management**: View all students and their details
- ✏️ **Assignment Grading**: Grade submissions, add comments, track grading history
- 📣 **Announcement Management**: Create, edit, and delete announcements  
- 📊 **Feedback Review**: View and filter student feedback by rating
- 📨 **Notification System**: Send notifications to all students or specific individuals

### Additional Features
- 🔍 Search and filter functionality across modules
- 🏥 Health check endpoint for monitoring (`/health`)
- 🔒 File upload validation (type and size limits)
- 📝 Comprehensive logging system
- ⚠️ Custom error pages (404, 500)
- 📱 Responsive design for all devices

## 🛠️ Technology Stack

- **Backend**: Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Session-based with bcrypt
- **Frontend**: HTML5, Bootstrap 5, Bootstrap Icons
- **Security**: Environment variables, input validation, SQL injection protection
- **DevOps**: Ready for containerization and CI/CD integration

## 📁 Project Structure

```
student-portal/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── .dockerignore              # Docker ignore rules
├── Dockerfile                 # Docker image configuration
├── docker-compose.yml         # Docker Compose configuration
├── Jenkinsfile                # Jenkins CI/CD pipeline
├── README.md                  # This file
│
├── templates/                 # HTML templates (22 files)
│   ├── base.html             # Base template with navigation
│   ├── login.html            # Login page
│   ├── signup.html           # Registration page
│   ├── dashboard.html        # Student dashboard
│   ├── profile.html          # Profile management
│   ├── assignments.html      # Assignment list
│   ├── upload.html           # File upload form
│   ├── announcements.html    # Announcements view
│   ├── feedback.html         # Feedback form
│   ├── notifications.html    # Notification center
│   ├── reset_password.html   # Password reset
│   ├── admin_*.html          # Admin templates (10 files)
│   ├── 404.html              # Not found error
│   └── 500.html              # Server error
│
├── static/                   
│   ├── css/
│   │   └── style.css         # Custom stylesheet
│   └── uploads/              # Student file uploads
│
└── database/
    └── students.db           # SQLite database (auto-created)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone or download the project**
   ```bash
   cd student-portal
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example file
   copy .env.example .env    # Windows
   cp .env.example .env      # Linux/Mac
   
   # Edit .env and set your SECRET_KEY
   # For production, use a strong random key:
   # python -c "import secrets; print(secrets.token_hex(32))"
   ```

5. **Initialize the database**
   ```bash
   python app.py
   ```
   This will create the database and seed the default admin account.

6. **Access the application**
   - Open your browser and navigate to: `http://127.0.0.1:5000`
   - Default admin credentials:
     - Email: `admin@student-portal.com`
     - Password: `Admin@123`

## 👤 Default Accounts

### Admin Account
- **Email**: admin@student-portal.com
- **Password**: Admin@123
- **Role**: Administrator

> ⚠️ **Important**: Change the admin password immediately after first login!

### Student Accounts
Students can register themselves using the signup page. Each student account includes:
- Full name
- Email (unique)
- Password (must meet strength requirements)
- Department
- Year (1-4)

## 🗄️ Database Schema

### Tables

**users** - Stores both students and admins
- `id`, `name`, `email`, `password` (hashed), `department`, `year`, `role`, `last_login`, `created_at`

**assignments** - File uploads and grades
- `id`, `user_id`, `filename`, `upload_date`, `grade`, `comments`, `graded_by`, `graded_at`

**announcements** - Admin announcements
- `id`, `title`, `message`, `created_by`, `created_at`, `updated_at`

**feedback** - Student feedback submissions
- `id`, `user_id`, `subject`, `message`, `rating` (1-5), `created_at`

**notifications** - User notifications
- `id`, `user_id`, `message`, `is_read`, `created_at`

## 🔒 Security Features

### Implemented Security Measures

1. **Password Security**
   - Bcrypt hashing with 12 rounds
   - Password strength validation
   - Secure password reset flow

2. **Session Security**
   - HTTP-only cookies
   - Secure session management
   - Automatic session timeout (1 hour)

3. **Input Validation**
   - Server-side validation on all forms
   - File type whitelist (PDF, DOC, DOCX)
   - File size limits (16MB)
   - SQL injection protection via ORM

4. **Access Control**
   - Role-based authentication
   - Protected routes with decorators
   - Admin-only route protection

5. **File Upload Security**
   - Werkzeug secure_filename
   - Type validation
   - Size restrictions
   - Unique filename generation

6. **Logging**
   - Login attempts (success/failure)
   - File uploads
   - Assignment grading
 - Security events
   - Error tracking

## 🔧 Configuration

### Environment Variables

Edit `.env` file to configure:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///database/students.db

# Upload Settings
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# Security
SESSION_COOKIE_SECURE=False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### File Upload Configuration

Modify `config.py` to change:
- `ALLOWED_EXTENSIONS`: File types allowed
- `MAX_CONTENT_LENGTH`: Maximum file size

## 📊 API Endpoints

### Health Check
```
GET /health
```
Returns JSON with application health status:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-16T10:00:00",
  "database": "connected"
}
```

## 🐳 DevSecOps Integration

This application is designed to integrate with DevSecOps pipelines and tools:

### Security Scanning
- **Snyk**: Dependency vulnerability scanning
- **SonarQube**: Code quality and security analysis
- **OWASP ZAP**: Dynamic application security testing
- **Bandit**: Python security linter

### Secrets Management
- Environment variable support for HashiCorp Vault integration
- No hardcoded credentials
- `.env` files excluded from version control

### CI/CD Ready
- Structured for GitHub Actions/Jenkins pipelines
- Automated testing hooks
- Docker containerization ready

## 🔄 Jenkins CI/CD Pipeline

The project includes a comprehensive Jenkins pipeline (`Jenkinsfile`) with DevSecOps best practices.

### Pipeline Stages

1. **Checkout** - Clone code from GitHub
2. **Build Docker Image** - Build containerized application
3. **Run Tests** - Execute automated tests
4. **Security Scanning** - Parallel vulnerability scans:
   - Trivy: Container image scanning
   - Bandit: Python code security analysis
5. **Code Quality Analysis** - Flake8 linting
6. **Push to Registry** - Push images to Docker registry
7. **Deploy to Staging** - Automated staging deployment
8. **Health Check** - Verify application health
9. **Manual Approval** - Production deployment gate
10. **Deploy to Production** - Production deployment
11. **Post Actions** - Notifications and cleanup

### Jenkins Setup

**Prerequisites:**
- Jenkins server with Docker installed
- Docker Pipeline plugin
- Email Extension Plugin (for notifications)

**Configure Jenkins:**

1. Create a new Pipeline job in Jenkins
2. Point to your Git repository
3. Set up credentials:
   ```
   - Docker Hub credentials (ID: docker-hub-credentials)
   - Email notification settings
   ```
4. Update environment variables in Jenkinsfile:
   ```groovy
   DOCKER_REGISTRY = 'your-registry.com'
   ```

**Trigger Pipeline:**
```bash
# Manual trigger from Jenkins UI
# Or automatic trigger on git push (configure webhook)
```

### Security Scanning Tools

- **Trivy**: Scans Docker images for HIGH/CRITICAL vulnerabilities
- **Bandit**: Python security linter for common security issues
- **Flake8**: Code quality and style checker

### Monitoring Stack

The application includes a complete monitoring solution with **Prometheus** for metrics collection and **Grafana** for visualization.

**Components:**
- **Prometheus**: Metrics collection and storage (Port 9090)
- **Grafana**: Dashboard and visualization (Port 3000)
- **Flask Exporter**: Automatic Flask metrics instrumentation

**Quick Start:**
```bash
# Start all services including monitoring
docker-compose up -d

# Access monitoring tools
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (login: admin/admin)
```

**Available Metrics:**
- Request rate and throughput
- Response time (p50, p95, p99 percentiles)
- HTTP status codes (2xx, 4xx, 5xx)
- Error rates and exceptions
- Application health status

**Grafana Dashboard:**
Navigate to http://localhost:3000 → Dashboards → "Student Portal Monitoring" to view:
- Real-time request metrics
- Performance graphs
- Error tracking
- System health indicators

The Prometheus datasource and dashboard are pre-configured and auto-loaded on startup.

### Monitoring
- Health check endpoint for uptime monitoring
- Comprehensive logging for Prometheus/Grafana integration
- Structured log format for log aggregation

## 🐳 Docker Deployment

The application includes production-ready Docker configuration with security best practices.

### Quick Start with Docker Compose

```bash
# Build and run with docker-compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at `http://localhost:5000`

### Manual Docker Build

```bash
# Build the Docker image
docker build -t student-portal:latest .

# Run the container
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/database:/app/database \
  -v $(pwd)/static/uploads:/app/static/uploads \
  -v $(pwd)/logs:/app/logs \
  -e SECRET_KEY=your-secret-key \
  --name student-portal-app \
  student-portal:latest

# View logs
docker logs -f student-portal-app

# Stop and remove
docker stop student-portal-app
docker rm student-portal-app
```

### Docker Features

- **Multi-stage build**: Optimized image size
- **Non-root user**: Enhanced security
- **Health checks**: Built-in container health monitoring
- **Volume mounts**: Persistent data for database, uploads, and logs
- **Environment variables**: Flexible configuration


## 📝 Logging

Logs are written to:
- **Console**: All log levels
- **File**: `app.log` (configurable in `config.py`)

Log events include:
- Authentication events
- File operations
- Database operations
- Security events
- Error tracking

## 🧪 Testing

### Automated Testing (Future Enhancement)

The application is designed to support automated testing using pytest:

```bash
# Install testing dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=app tests/
```

## 🔮 Future Enhancements

Potential improvements for production:
- [ ] Email verification for registration
- [ ] Email-based password reset
- [ ] Two-factor authentication (2FA)
- [ ] Export data to PDF/CSV
- [ ] Advanced analytics dashboard
- [ ] Real-time chat support
- [ ] Assignment due dates and reminders
- [ ] Bulk file upload
- [ ] API for mobile app integration
- [ ] Multi-language support

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset database
rm database/students.db
python app.py
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Permission Errors (File Upload)
```bash
# Windows
icacls static\uploads /grant Everyone:(OI)(CI)F

# Linux/Mac
chmod 755 static/uploads
```

## 📄 License

This project is created for educational and DevSecOps demonstration purposes.

## 👨‍💻 Developer Notes

### Code Structure
- **app.py**: All routes, models, and business logic
- **config.py**: Environment and security configuration
- **templates/**: Jinja2 templates with Bootstrap 5
- **static/css/style.css**: Custom styles and animations

### Best Practices Implemented
✅ Separation of concerns  
✅ DRY (Don't Repeat Yourself) principle  
✅ Consistent naming conventions  
✅ Comprehensive comments  
✅ Error handling  
✅ Security-first design  
✅ Responsive UI/UX  

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review application logs in `app.log`
3. Use the feedback form within the application
4. Contact system administrator

## 🎓 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://www.sqlalchemy.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [DevSecOps Best Practices](https://www.devsecops.org/)

---

**Built with ❤️ for DevSecOps Excellence**

Last Updated: February 2026
