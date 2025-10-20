# 📚 Registrar System User Guide
**VBCA School Management System**

---

## 🔐 Login Instructions

**Access the System:**
- Website: https://vbcasms.onrender.com
- Username: `crenz`
- Password: `crenz123`

**Important:** Please change your password after first login for security.

---

## 📊 Dashboard Overview

When you log in, you'll see the **Registrar Dashboard** with:

### Quick Statistics Cards
- **Total Students** - All students in the system
- **Active Students** - Currently enrolled students
- **Enrolled This Year** - New enrollments this academic year
- **Graduated** - Completed students
- **Transferred** - Students who moved to other schools
- **Total Documents** - All uploaded SF10 and student documents

### Quick Action Buttons
- 🔍 **Search Students** - Find student records quickly
- 📤 **Bulk Import** - Upload multiple student records at once
- 📊 **Analytics** - View detailed reports and statistics
- 📋 **SF10 Records** - Manage SF10 forms

---

## 🔍 1. STUDENT SEARCH

**Purpose:** Find and view student information quickly

**How to Use:**
1. Click **"Search Students"** from the dashboard
2. Enter search criteria:
   - Student ID
   - Name (first or last)
   - Grade level
   - Section
   - Admission date
3. Click **"Search"**
4. View results in the table
5. Click on any student to see full details

**Tips:**
- Leave fields blank to see all students
- Use partial names (e.g., "Mar" finds "Maria", "Mark", "Mario")
- Filter by active/inactive status
- Sort results by clicking column headers

---

## 👤 2. STUDENT DETAILS & EDITING

**Purpose:** View and update individual student information

**How to View:**
1. Search for a student
2. Click on their name or ID
3. View complete profile with all information

**How to Edit:**
1. Open student details
2. Click **"Edit Student"** button
3. Update information:
   - Personal details (name, birthdate, address)
   - Contact information (phone, email)
   - Parent/Guardian information
   - Emergency contacts
   - Medical information
   - Academic information (grade, section)
4. Click **"Save Changes"**

**Important Fields:**
- ✅ Student ID (cannot be changed)
- ✅ Date of Birth (verify format: MM/DD/YYYY)
- ✅ Parent/Guardian name and contact
- ✅ Emergency contact information

---

## 📤 3. BULK IMPORT (Excel Upload)

**Purpose:** Add multiple students at once from Excel/CSV file

**Step-by-Step Process:**

### Step 1: Download Template
1. Click **"Bulk Import"** from dashboard
2. Click **"Download Template"** button
3. Save the Excel template to your computer

### Step 2: Fill Template
Open the template and fill in student data:

**Required Columns:**
- `student_id` - Unique ID (e.g., 2024-001)
- `first_name` - Student's first name
- `last_name` - Student's last name
- `date_of_birth` - Format: YYYY-MM-DD (e.g., 2010-05-15)
- `grade` - Grade level (e.g., Grade 7, Grade 8)
- `section` - Section name (e.g., A, B, Diamond)

**Optional Columns:**
- `email` - Student email
- `phone` - Contact number
- `address` - Home address
- `parent_name` - Parent/Guardian name
- `parent_phone` - Parent contact number
- `parent_email` - Parent email
- `emergency_contact` - Emergency contact name
- `emergency_phone` - Emergency contact number

### Step 3: Upload File
1. Click **"Choose File"** button
2. Select your filled template
3. Click **"Upload & Preview"**

### Step 4: Review & Confirm
1. Check the preview of students to be imported
2. Review any warnings or errors
3. Fix errors if needed
4. Click **"Confirm Import"**
5. Wait for success message

**Important Notes:**
- ⚠️ File must be .xlsx or .csv format
- ⚠️ Student IDs must be unique
- ⚠️ All required fields must be filled
- ⚠️ Maximum 100 students per upload
- ✅ System automatically checks for duplicates

---

## 📋 4. SF10 DOCUMENT MANAGEMENT

**Purpose:** Manage student SF10 forms (permanent records)

### View SF10 Dashboard
1. Click **"SF10 Records"** from main dashboard
2. View statistics:
   - Total SF10 records
   - By grade level
   - Recent uploads

### Create New SF10 Record
1. Click **"Create SF10"**
2. Fill in form sections:
   - **Student Information**
   - **Academic Year**
   - **Subject Grades**
   - **Attendance Records**
3. Click **"Save SF10"**

### Upload Bulk SF10 Data
1. Click **"Upload SF10"**
2. Download SF10 template
3. Fill Excel file with data
4. Upload and preview
5. Confirm upload

### View/Edit SF10
1. Search for student SF10
2. Click on record to view
3. Click **"Edit"** to update
4. Save changes

---

## 📊 5. ANALYTICS & REPORTS

**Purpose:** Generate reports and view enrollment statistics

**Available Reports:**
1. **Enrollment Summary**
   - Total students by grade
   - Active vs inactive students
   - Monthly enrollment trends

2. **Grade Distribution**
   - Students per grade level
   - Students per section
   - Classroom capacity

3. **Demographics**
   - Age distribution
   - Gender ratio
   - Geographic distribution

**How to Generate:**
1. Click **"Analytics"** from dashboard
2. Select report type
3. Choose date range (if applicable)
4. Click **"Generate Report"**
5. View results
6. Click **"Export"** to download as Excel

---

## 📁 6. DOCUMENT UPLOAD

**Purpose:** Upload and manage student documents

**Supported Documents:**
- Birth certificates
- Report cards
- Medical records
- ID photos
- Transfer credentials
- Any PDF/image files

**How to Upload:**
1. Go to student profile
2. Click **"Upload Document"**
3. Choose document type
4. Select file (PDF, JPG, PNG)
5. Add description (optional)
6. Click **"Upload"**

**Document Management:**
- View all documents in student profile
- Download documents anytime
- Delete outdated documents
- Maximum file size: 5MB per file

---

## 🗂️ 7. ARCHIVE SYSTEM

**Purpose:** Store records of graduated/transferred students

### Archive a Student
1. Open student profile
2. Click **"Archive Student"**
3. Select reason:
   - Graduated
   - Transferred
   - Inactive
4. Add notes (optional)
5. Click **"Confirm Archive"**

### View Archived Students
1. Go to Student Search
2. Filter by **"Archived"** status
3. View archived records

### Restore Archived Student
1. Find archived student
2. Click **"Restore"**
3. Confirm restoration
4. Student becomes active again

**Note:** Archived students are still searchable but don't appear in active counts.

---

## ✅ 8. DATA VALIDATION FEATURES

**Automatic Checks:**
- ✅ Duplicate student IDs
- ✅ Duplicate LRNs (Learner Reference Numbers)
- ✅ Invalid birthdates (future dates)
- ✅ Missing required fields
- ✅ Invalid email formats
- ✅ Invalid phone number formats

**When You'll See Warnings:**
- During bulk import
- When creating new students
- When editing student information

**What to Do:**
- Red errors = Must fix before saving
- Yellow warnings = Review but can proceed
- Green success = All data is valid

---

## 💾 9. BACKUP & DATA PROTECTION

**Automatic Features:**
- 🔒 Daily automatic backups
- 🔒 Encrypted data storage
- 🔒 Secure file uploads
- 🔒 Session timeout (30 minutes)

**Manual Backup:**
1. Click **"Export Students"** from dashboard
2. Select export format (Excel/CSV)
3. Choose what to include
4. Click **"Download Backup"**
5. Save file securely

**Best Practices:**
- Keep local backup copies
- Don't share login credentials
- Log out when finished
- Clear browser cache on shared computers

---

## 🔐 SECURITY & PRIVACY

**Your Responsibilities:**
1. **Password Security**
   - Change default password immediately
   - Use strong password (min 12 characters)
   - Never share your password
   - Don't write password down

2. **Data Privacy**
   - Student data is confidential
   - Only access data you need
   - Don't share student information outside the system
   - Report any suspicious activity

3. **Best Practices**
   - Lock computer when away
   - Log out after each session
   - Use secure internet connection
   - Don't access on public WiFi without VPN

**System Security Features:**
- ✅ Account lockout after 5 failed login attempts
- ✅ Session timeout after 30 minutes
- ✅ Encrypted connections (HTTPS)
- ✅ Activity logging for audits
- ✅ Role-based access control

---

## ⚠️ TROUBLESHOOTING

### Can't Login?
- ✅ Check username and password (case-sensitive)
- ✅ Clear browser cache and cookies
- ✅ Try different browser
- ✅ Contact admin if locked out

### Upload Failed?
- ✅ Check file format (.xlsx or .csv)
- ✅ Verify file size (max 5MB)
- ✅ Check for required fields
- ✅ Remove special characters from data

### Can't Find Student?
- ✅ Check spelling
- ✅ Try different search terms
- ✅ Check if student is archived
- ✅ Verify student exists in system

### Page Loading Slow?
- ✅ Check internet connection
- ✅ Clear browser cache
- ✅ Close other tabs/programs
- ✅ Try refreshing page

---

## 📞 SUPPORT & CONTACT

**For Technical Issues:**
- Contact IT Administrator
- Email: admin@vbca.edu (example)

**For Data Questions:**
- Contact School Administrator
- Refer to school policies

**Emergency Data Recovery:**
- Contact system administrator immediately
- Daily backups are available

---

## 📋 QUICK REFERENCE CHECKLIST

### Daily Tasks:
- [ ] Check new enrollments
- [ ] Review pending documents
- [ ] Update student information as needed
- [ ] Respond to data requests

### Weekly Tasks:
- [ ] Generate attendance reports
- [ ] Review archived students
- [ ] Check data quality
- [ ] Export backup copy

### Monthly Tasks:
- [ ] Generate enrollment statistics
- [ ] Review and clean duplicate records
- [ ] Update archived student status
- [ ] Verify all SF10 records are current

### Quarterly Tasks:
- [ ] Full data backup
- [ ] Review system security settings
- [ ] Update student photos
- [ ] Generate comprehensive reports

---

## 🎯 TIPS FOR EFFICIENCY

1. **Use Keyboard Shortcuts:**
   - Ctrl+F to search on page
   - Tab to move between fields
   - Enter to submit forms

2. **Batch Operations:**
   - Use bulk import for multiple students
   - Archive multiple students at once
   - Export data in batches

3. **Filters & Sorting:**
   - Use advanced filters to narrow results
   - Save common search criteria
   - Sort by most-used columns

4. **Regular Maintenance:**
   - Archive graduated students promptly
   - Remove duplicate records
   - Update contact information regularly
   - Keep SF10 records current

---

## ✨ NEW FEATURES (2025)

- ✨ **Smart Data Validation** - Automatic error checking
- ✨ **Modern Dashboard** - Faster, cleaner interface
- ✨ **Archive System** - Better organization of past students
- ✨ **Enhanced Search** - More powerful filters
- ✨ **Mobile Responsive** - Works on tablets and phones
- ✨ **Auto Backup** - Daily encrypted backups

---

**Last Updated:** October 2025  
**Version:** 2.0  
**System:** VBCA School Management System

For questions or suggestions, please contact your system administrator.

