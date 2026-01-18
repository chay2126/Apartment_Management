🏢 Apartment Management System
A comprehensive web-based apartment management system built with Flask, featuring separate portals for administrators and residents with role-based access control.
📋 Table of Contents

Overview
Features
Technology Stack
System Architecture
Usage
Database Schema
API Endpoints

🎯 Overview
The Apartment Management System is a full-stack web application designed to streamline apartment operations, maintenance tracking, expense management, and resident communication. It provides two distinct interfaces:

Admin Portal: Full management capabilities for apartment administrators
Resident Portal: Self-service portal for residents with read-only access to community information

✨ Features
👨‍💼 Admin Portal
1. Maintenance Management

View all payment records with advanced filtering (by month, status)
Track due payments across all flats
Monitor total collection amounts
Mark payments as PAID/DUE
View payment history with transaction details
Automatic monthly payment record generation for all flats

2. Expense Tracking

Add, edit, and delete apartment expenses
Categorize expenses (Electricity, Water, Cleaning, Repair, Security, Gardening, Maintenance, Other)
Filter expenses by month
View monthly expense summaries
Track total and average expenses

3. Service Provider Directory

Manage service provider contacts
Categorize services (Cleaning, Plumbing, Electrical, Carpentry, Painting, Security, Gardening)
Store phone numbers and additional notes
Quick add/edit/delete functionality
Service provider search and filtering

4. Notice Board

Create and manage community notices
Categorize notices (Announcement, Event, Maintenance, Emergency, General)
Set priority levels (High, Medium, Low)
Edit and delete notices
Timestamp tracking for all notices

5. Watchman Notifications

Send instant Telegram notifications to watchman
Predefined message templates (General, Urgent, Delivery, Maintenance, Security)
Custom message option
Real-time delivery confirmation

🏠 Resident Portal
1. Maintenance Payment

View payment history
Pay maintenance via UPI with QR code
Select month and enter transaction details
Transaction ID duplicate prevention
Payment summary and statistics
Completion rate tracking

2. Expense Viewing (Read-Only)

View all apartment expenses
Filter by month
See monthly expense summaries
Track spending patterns

3. Watchman Notifications

Auto-filled flat number (from session)
Select notification reason
Send instant Telegram alerts
Message preview before sending

4. Service Directory (Read-Only)

Browse all service providers
View contact information
Category-based organization
Click-to-call functionality

5. Notice Board (Read-Only)

View all community notices
Filter by category and priority
Stay updated on apartment announcements

🛠 Technology Stack
Backend

Framework: Flask 2.x (Python)
Database: SQLite 3
Authentication: Session-based with role-based access control
API Integration: Telegram Bot API

Frontend

HTML5 with Jinja2 templating
CSS3 with custom styling
JavaScript (Vanilla) for interactivity
Responsive Design for mobile/tablet/desktop

External Services

Telegram Bot API for real-time notifications
UPI Payment Integration (QR code-based)

🏗 System Architecture
apartment-management-system/
│
├── app.py                          # Main Flask application
├── apartment.db                    # SQLite database
├── get_chat_id.py                 # Telegram bot utility
│
├── templates/                      # HTML templates
│   ├── login.html                 # Login page
│   ├── admin_home.html            # Admin dashboard
│   ├── resident_home.html         # Resident dashboard
│   ├── maintenence.html           # Maintenance menu
│   ├── view_payments.html         # All payments view
│   ├── due_payments.html          # Due payments view
│   ├── total_amount.html          # Total collection summary
│   ├── expenses.html              # Expense management (admin)
│   ├── services.html              # Service directory (admin)
│   ├── notify_watchman.html       # Notify watchman (admin)
│   ├── resident_maintenance.html  # Maintenance payment (resident)
│   ├── resident_expenses.html     # Expense viewing (resident)
│   ├── resident_notify.html       # Notify watchman (resident)
│   └── resident_services.html     # Service directory (resident)
│
└── static/                         # Static files
    ├── css/
    │   └── style.css              # Main stylesheet
    ├── js/
    │   └── script.js              # JavaScript utilities
    └── images/
        └── upi_qr.png             # UPI payment QR code
        
📊 Database Schema
Tables
1. users
sql- user_id (INTEGER PRIMARY KEY)
- username (TEXT UNIQUE)
- password (TEXT)
- full_name (TEXT)
- phone (TEXT)
- user_type (TEXT) -- 'admin' or 'resident'
- flat_id (INTEGER) -- Foreign key to flats table (for residents)
2. flats
sql- flat_id (INTEGER PRIMARY KEY)
- flat_no (TEXT UNIQUE)
- owner_name (TEXT)
3. payments
sql- payment_id (INTEGER PRIMARY KEY)
- flat_id (INTEGER) -- Foreign key
- month (TEXT) -- Format: YYYY-MM
- amount (INTEGER)
- status (TEXT) -- 'PAID' or 'DUE'
- payment_mode (TEXT) -- 'UPI', 'Cash', 'Bank Transfer'
- transaction_id (TEXT UNIQUE)
- paid_date (DATE)
4. expenses
sql- expense_id (INTEGER PRIMARY KEY)
- month (TEXT) -- Format: YYYY-MM
- category (TEXT)
- amount (INTEGER)
5. services
sql- service_id (INTEGER PRIMARY KEY)
- service_name (TEXT)
- phone_number (TEXT)
- category (TEXT)
- notes (TEXT)
6. notices
sql- notice_id (INTEGER PRIMARY KEY)
- title (TEXT)
- content (TEXT)
- category (TEXT)
- priority (TEXT) -- 'High', 'Medium', 'Low'
- created_date (TIMESTAMP)
- updated_date (TIMESTAMP)

💻 Usage
Admin Login

Navigate to the login page
Enter admin credentials
Access the admin dashboard

Resident Login

Navigate to the login page
Enter resident credentials (username: flat number)
Access the resident portal

Key Operations
Adding a Resident

Admin creates a user with user_type='resident'
Links user to a flat via flat_id
Resident can now log in and access their portal

Processing Payments

Residents submit payment via UPI
Enter transaction ID and amount
Admin can verify and track all payments
System prevents duplicate transaction IDs

Managing Expenses

Admin adds monthly expenses
Categorizes and tracks spending
Residents can view expense breakdowns

Sending Notifications

Select notification type or write custom message
System sends to watchman's Telegram
Instant delivery confirmation

📡 API Endpoints
Authentication

POST /login - User login
GET /logout - User logout

Admin Routes

GET /admin - Admin dashboard
GET /maintenance - Maintenance menu
GET /view/flats - View all payments
GET /due/payments - View due payments
GET /total/amount - Total collection summary
GET /expenses - Expense management
POST /expenses/add - Add expense
POST /expenses/edit/<id> - Edit expense
POST /expenses/delete/<id> - Delete expense
GET /services - Service directory
POST /services/add - Add service
POST /services/edit/<id> - Edit service
POST /services/delete/<id> - Delete service
GET /notify - Notify watchman page
POST /notify/send - Send notification

Resident Routes

GET /resident - Resident dashboard
GET /resident/maintenance - Maintenance payment page
POST /resident/maintenance/pay - Submit payment
GET /resident/expenses - View expenses
GET /resident/notify - Notify watchman page
POST /resident/notify/send - Send notification
GET /resident/services - View services

Notice Board (Both)

GET /api/notices - Get all notices (JSON)
POST /notices/add - Add notice (admin only)
POST /notices/edit/<id> - Edit notice (admin only)
POST /notices/delete/<id> - Delete notice (admin only)

Built with ❤️ for better apartment management
⭐ Star this repository if you find it helpful!
