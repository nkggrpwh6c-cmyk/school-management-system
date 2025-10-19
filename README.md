# School Management System

A comprehensive web-based school management system designed to handle 1,000+ students with role-based access control for students, teachers, parents, and administrators.

## Features

### 🔐 Authentication & Authorization
- Multi-role login system (Student, Teacher, Parent, Admin)
- Secure password hashing and session management
- Role-based access control with permission levels
- Teacher admin access for confidential grade management

### 👨‍🎓 Student Management
- Student registration and profile management
- Academic year and grade management
- Class section management with capacity tracking
- Student document management
- Comprehensive student search and filtering

### 👨‍🏫 Teacher Management
- Teacher profiles and class assignments
- Teacher admin access for grade management
- Staff management with employment records

### 👨‍👩‍👧‍👦 Parent Portal
- Secure parent login
- View linked children's information
- Check attendance records
- View fee payment status
- Download fee receipts

### 💰 Fee Management
- Fee structure configuration by grade/class
- Payment recording with receipt generation
- Payment history and pending dues tracking
- Multiple payment methods support

### 📅 Timetable & Scheduling
- Weekly class timetables
- Teacher schedule management
- Room/venue assignment
- Conflict detection for double-booking
- PDF export functionality

### 📊 Grades System (Teacher Admin Only)
- Secure grade entry interface
- Subject-wise marks management
- Grade calculation and GPA
- Progress tracking across terms
- Confidential access control

### 📈 Reports & Analytics
- Student enrollment statistics
- Attendance reports (daily, monthly, yearly)
- Fee collection reports
- Academic performance analytics
- Export reports to PDF/Excel

## Technology Stack

- **Backend**: Python 3.8+ with Django 4.2
- **Database**: PostgreSQL (production-ready for 1,000+ students)
- **Frontend**: HTML5, CSS3, JavaScript with Bootstrap 5
- **Authentication**: Django's built-in auth system with custom user model
- **Security**: HTTPS, CSRF protection, XSS protection, input validation

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package installer)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd school-management-system
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
1. Create a PostgreSQL database:
```sql
CREATE DATABASE school_management;
CREATE USER school_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE school_management TO school_user;
```

2. Copy environment file:
```bash
cp env.example .env
```

3. Update `.env` file with your database credentials:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=school_management
DB_USER=school_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Collect Static Files
```bash
python manage.py collectstatic
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## User Roles & Access

### Student
- View personal dashboard with attendance summary
- Access timetable and academic information
- View fee status and payment history
- Update personal profile

### Teacher
- Access teacher dashboard with assigned classes
- Mark attendance for students
- Enter and manage grades (teacher admin only)
- View class schedules and student information

### Parent
- View linked children's information
- Check attendance records
- View fee payment status and download receipts
- Access timetables for children

### Admin
- Full system access
- Manage all users, students, teachers, and parents
- Configure academic years, grades, and sections
- Generate comprehensive reports
- System administration and maintenance

## Security Features

- **CSRF Protection**: All forms protected against Cross-Site Request Forgery
- **XSS Protection**: Template escaping prevents Cross-Site Scripting attacks
- **SQL Injection Protection**: Django ORM prevents SQL injection
- **Secure Password Storage**: PBKDF2 hashing with salt
- **Session Security**: Secure session management with timeout
- **Input Validation**: Comprehensive form validation and sanitization
- **Role-Based Access**: Granular permission system

## Scalability Considerations

- **Database Optimization**: Proper indexing for 1,000+ students
- **Connection Pooling**: Efficient database connection management
- **Pagination**: Large dataset handling with pagination
- **Caching**: Frequently accessed data caching
- **Query Optimization**: select_related and prefetch_related usage

## Production Deployment

### Environment Variables
Set the following environment variables for production:

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=school_management
DB_USER=production_user
DB_PASSWORD=secure_password
DB_HOST=your-db-host
DB_PORT=5432
```

### Static Files
```bash
python manage.py collectstatic --noinput
```

### Database Backup
```bash
pg_dump school_management > backup.sql
```

## API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout
- `POST /accounts/signup/` - User registration

### Students
- `GET /students/` - Student dashboard
- `GET /students/list/` - Student list with search/filter
- `GET /students/{id}/` - Student details
- `POST /students/create/` - Create new student
- `PUT /students/{id}/edit/` - Update student

### Attendance
- `GET /students/attendance/` - Attendance records
- `POST /students/attendance/mark/` - Mark attendance

### Reports
- `GET /reports/` - Reports dashboard
- `GET /reports/attendance/` - Attendance reports
- `GET /reports/fees/` - Fee collection reports

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.

## Changelog

### Version 1.0.0
- Initial release
- Complete student management system
- Role-based authentication
- Attendance tracking
- Fee management
- Timetable system
- Grade management
- Reports and analytics
