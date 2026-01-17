from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
from datetime import datetime
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!

database = "apartment.db"

# TELEGRAM BOT CONFIGURATION
TELEGRAM_BOT_TOKEN = "8493019914:AAF4lR6K5auN_foC3XbJlS1OfNXtzpbKDqM"  # Replace with your bot token
WATCHMAN_CHAT_ID = "757449530"  # Replace with watchman's chat ID

def db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

def send_telegram_message(message):
    """Send message via Telegram Bot"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": WATCHMAN_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Error sending telegram: {e}")
        return None

# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Only Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('user_type') != 'admin':
            return redirect(url_for('resident_home'))
        return f(*args, **kwargs)
    return decorated_function

# Resident Only Decorator
def resident_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('user_type') != 'resident':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ========== AUTHENTICATION ROUTES ==========

@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_type') == 'admin':
        return redirect(url_for('index'))
    else:
        return redirect(url_for('resident_home'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = db_connection()
        cursor = conn.cursor()
        
        # For residents, join with flats table to get flat_no
        if username != 'admin':
            cursor.execute('''
                SELECT u.*, f.flat_no 
                FROM users u
                LEFT JOIN flats f ON u.flat_id = f.flat_id
                WHERE u.username = ? AND u.password = ?
            ''', (username, password))
        else:
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            session['full_name'] = user['full_name']
            session['phone'] = user['phone']
            
            # Store flat_no for residents (not flat_id)
            if user['user_type'] == 'resident':
                session['flat_no'] = user['flat_no']  # This is from the JOIN
                session['flat_id'] = user['flat_id']   # Keep flat_id for database queries
            else:
                session['flat_no'] = None
                session['flat_id'] = None
            
            if user['user_type'] == 'admin':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('resident_home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# ========== ADMIN ROUTES ==========

@app.route("/admin")
@admin_required
def index():
    user_data = {
        'full_name': session.get('full_name'),
        'user_type': session.get('user_type')
    }
    return render_template("admin_home.html", user=user_data)

@app.route("/maintenance")
@admin_required
def maintenance():
    return render_template("maintenence.html")

@app.route("/view/flats", methods=["GET"])
@admin_required
def get_flats_payments():
    month_filter = request.args.get("month")
    status_filter = request.args.get("status")
    
    conn = db_connection()
    
    # JOIN with flats table to get flat_no
    query = '''
        SELECT p.*, f.flat_no, f.owner_name 
        FROM payments p
        JOIN flats f ON p.flat_id = f.flat_id
        WHERE 1=1
    '''
    params = []
    
    if month_filter:
        query += ' AND p.month = ?'
        params.append(month_filter)
    
    if status_filter:
        query += ' AND p.status = ?'
        params.append(status_filter)
    
    query += ' ORDER BY p.month DESC, f.flat_no'
    
    flats = conn.execute(query, params).fetchall()
    
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT month FROM payments ORDER BY month DESC')
    months = cursor.fetchall()
    
    conn.close()
    
    return render_template("view_payments.html", flats=flats, months=months)

@app.route("/due/payments", methods=['GET'])
@admin_required
def get_due_payments():
    month_filter = request.args.get("month")
    
    conn = db_connection()
    
    # JOIN with flats table to get flat_no
    query = '''
        SELECT p.*, f.flat_no, f.owner_name 
        FROM payments p
        JOIN flats f ON p.flat_id = f.flat_id
        WHERE p.status = ?
    '''
    params = ['DUE']
    
    if month_filter:
        query += ' AND p.month = ?'
        params.append(month_filter)
    
    query += ' ORDER BY p.month DESC, f.flat_no'
    
    flats = conn.execute(query, params).fetchall()
    
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT month FROM payments ORDER BY month DESC')
    months = cursor.fetchall()
    
    conn.close()
    
    return render_template("due_payments.html", flats=flats, months=months)

@app.route("/total/amount", methods=['GET'])
@admin_required
def get_total_amount():
    conn = db_connection()
    
    cursor = conn.cursor()
    cursor.execute('SELECT month FROM payments ORDER BY month DESC LIMIT 1')
    recent_month_row = cursor.fetchone()
    
    if not recent_month_row:
        conn.close()
        return render_template("total_amount.html", recent_month=None, total_collected=0, total_due=0, grand_total=0, flats=[])
    
    recent_month = recent_month_row['month']
    
    # JOIN with flats table
    cursor.execute('''
        SELECT p.*, f.flat_no, f.owner_name 
        FROM payments p
        JOIN flats f ON p.flat_id = f.flat_id
        WHERE p.month = ? 
        ORDER BY f.flat_no
    ''', (recent_month,))
    flats = cursor.fetchall()
    
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN status = 'PAID' THEN amount ELSE 0 END) as collected,
            SUM(CASE WHEN status = 'DUE' THEN amount ELSE 0 END) as due,
            SUM(amount) as total
        FROM payments 
        WHERE month = ?
    ''', (recent_month,))
    
    totals = cursor.fetchone()
    
    conn.close()
    
    return render_template("total_amount.html", 
                         recent_month=recent_month,
                         total_collected=totals['collected'] or 0,
                         total_due=totals['due'] or 0,
                         grand_total=totals['total'] or 0,
                         flats=flats)

@app.route("/mark/paid/<int:payment_id>", methods=['POST'])
@admin_required
def mark_payment_paid(payment_id):
    conn = db_connection()
    
    conn.execute('''
        UPDATE payments 
        SET status = 'PAID', 
            payment_mode = 'Cash', 
            paid_date = ?
        WHERE payment_id = ?
    ''', (datetime.now().strftime('%Y-%m-%d'), payment_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('get_due_payments'))

@app.route("/expenses", methods=['GET'])
@admin_required
def view_expenses():
    month_filter = request.args.get("month")
    
    conn = db_connection()
    
    query = 'SELECT * FROM expenses WHERE 1=1'
    params = []
    
    if month_filter:
        query += ' AND month = ?'
        params.append(month_filter)
    
    query += ' ORDER BY month DESC, expense_id'
    
    expenses = conn.execute(query, params).fetchall()
    
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT month FROM expenses ORDER BY month DESC')
    months = cursor.fetchall()
    
    cursor.execute('''
        SELECT month, SUM(amount) as total
        FROM expenses
        GROUP BY month
        ORDER BY month DESC
    ''')
    monthly_totals = cursor.fetchall()
    
    conn.close()
    
    return render_template("expenses.html", expenses=expenses, months=months, monthly_totals=monthly_totals)

@app.route("/expenses/add", methods=['POST'])
@admin_required
def add_expense():
    month = request.form.get('month')
    category = request.form.get('category')
    amount = request.form.get('amount')
    
    conn = db_connection()
    conn.execute('''
        INSERT INTO expenses (month, category, amount)
        VALUES (?, ?, ?)
    ''', (month, category, amount))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_expenses'))

@app.route("/expenses/edit/<int:expense_id>", methods=['POST'])
@admin_required
def edit_expense(expense_id):
    month = request.form.get('month')
    category = request.form.get('category')
    amount = request.form.get('amount')
    
    conn = db_connection()
    conn.execute('''
        UPDATE expenses
        SET month = ?, category = ?, amount = ?
        WHERE expense_id = ?
    ''', (month, category, amount, expense_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_expenses'))

@app.route("/expenses/delete/<int:expense_id>", methods=['POST'])
@admin_required
def delete_expense(expense_id):
    conn = db_connection()
    conn.execute('DELETE FROM expenses WHERE expense_id = ?', (expense_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_expenses'))

@app.route("/services", methods=['GET'])
@admin_required
def view_services():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM services ORDER BY category, service_name')
    services = cursor.fetchall()
    conn.close()
    
    return render_template("services.html", services=services)

@app.route("/services/add", methods=['POST'])
@admin_required
def add_service():
    service_name = request.form.get('service_name')
    phone_number = request.form.get('phone_number')
    category = request.form.get('category')
    notes = request.form.get('notes')
    
    conn = db_connection()
    conn.execute('''
        INSERT INTO services (service_name, phone_number, category, notes)
        VALUES (?, ?, ?, ?)
    ''', (service_name, phone_number, category, notes))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_services'))

@app.route("/services/edit/<int:service_id>", methods=['POST'])
@admin_required
def edit_service(service_id):
    service_name = request.form.get('service_name')
    phone_number = request.form.get('phone_number')
    category = request.form.get('category')
    notes = request.form.get('notes')
    
    conn = db_connection()
    conn.execute('''
        UPDATE services
        SET service_name = ?, phone_number = ?, category = ?, notes = ?
        WHERE service_id = ?
    ''', (service_name, phone_number, category, notes, service_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_services'))

@app.route("/services/delete/<int:service_id>", methods=['POST'])
@admin_required
def delete_service(service_id):
    conn = db_connection()
    conn.execute('DELETE FROM services WHERE service_id = ?', (service_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_services'))

@app.route("/notify")
@admin_required
def notify_watchman():
    return render_template("notify_watchman.html")

@app.route("/notify/send", methods=['POST'])
@admin_required
def send_notification():
    flat_no = request.form.get('flat_no')
    message_type = request.form.get('message_type')
    custom_message = request.form.get('custom_message')
    
    messages = {
        'general': f"🔔 <b>Alert</b>\n\nFlat <b>{flat_no}</b> is calling you.\nPlease visit immediately.",
        'urgent': f"🚨 <b>URGENT</b>\n\nFlat <b>{flat_no}</b> needs immediate assistance.\nPlease rush!",
        'delivery': f"📦 <b>Delivery Alert</b>\n\nGuest/Delivery at Flat <b>{flat_no}</b>.\nPlease attend.",
        'maintenance': f"🔧 <b>Maintenance</b>\n\nFlat <b>{flat_no}</b> needs maintenance support.\nPlease visit.",
        'security': f"🚨 <b>Security Alert</b>\n\nFlat <b>{flat_no}</b> requires security assistance.\nPlease respond immediately."
    }
    
    if message_type == 'custom' and custom_message:
        message = f"📨 <b>Message from Flat {flat_no}</b>\n\n{custom_message}"
    else:
        message = messages.get(message_type, messages['general'])
    
    try:
        result = send_telegram_message(message)
        
        if result and result.get('ok'):
            return render_template("notify_watchman.html", success=True, flat_no=flat_no)
        else:
            error_message = "Failed to send notification. Please check bot configuration."
            return render_template("notify_watchman.html", error=error_message)
    
    except Exception as e:
        error_message = f"Failed to send notification: {str(e)}"
        return render_template("notify_watchman.html", error=error_message)

# NOTICES ROUTES (Both Admin and Resident can view)
@app.route("/api/notices", methods=['GET'])
@login_required
def get_notices():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notices ORDER BY priority DESC, created_date DESC')
    notices = cursor.fetchall()
    conn.close()
    
    notices_list = []
    for notice in notices:
        notices_list.append({
            'notice_id': notice['notice_id'],
            'title': notice['title'],
            'content': notice['content'],
            'category': notice['category'],
            'priority': notice['priority'],
            'created_date': notice['created_date'],
            'updated_date': notice['updated_date']
        })
    
    return jsonify(notices_list)

@app.route("/notices/add", methods=['POST'])
@admin_required
def add_notice():
    title = request.form.get('title')
    content = request.form.get('content')
    category = request.form.get('category')
    priority = request.form.get('priority')
    
    conn = db_connection()
    conn.execute('''
        INSERT INTO notices (title, content, category, priority)
        VALUES (?, ?, ?, ?)
    ''', (title, content, category, priority))
    conn.commit()
    conn.close()
    
    return redirect('/?tab=notices')

@app.route("/notices/edit/<int:notice_id>", methods=['POST'])
@admin_required
def edit_notice(notice_id):
    title = request.form.get('title')
    content = request.form.get('content')
    category = request.form.get('category')
    priority = request.form.get('priority')
    
    conn = db_connection()
    conn.execute('''
        UPDATE notices
        SET title = ?, content = ?, category = ?, priority = ?, updated_date = CURRENT_TIMESTAMP
        WHERE notice_id = ?
    ''', (title, content, category, priority, notice_id))
    conn.commit()
    conn.close()
    
    return redirect('/?tab=notices')

@app.route("/notices/delete/<int:notice_id>", methods=['POST'])
@admin_required
def delete_notice(notice_id):
    conn = db_connection()
    conn.execute('DELETE FROM notices WHERE notice_id = ?', (notice_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ========== RESIDENT ROUTES ==========

@app.route("/resident")
@resident_required
def resident_home():
    user_data = {
        'full_name': session.get('full_name'),
        'flat_id': session.get('flat_id'),
        'flat_no': session.get('flat_no'),
        'phone': session.get('phone'),
        'user_type': session.get('user_type')
    }
    return render_template("resident_home.html", user=user_data)

# Resident routes will be added in next phases
@app.route("/resident/maintenance")
@resident_required
def resident_maintenance():
    flat_id = session.get('flat_id')
    flat_no = session.get('flat_no')
    
    # Check for success/error messages
    success = request.args.get('success')
    error = request.args.get('error')
    
    error_message = None
    if error == 'duplicate':
        error_message = "This Transaction ID has already been used. Please use a unique Transaction ID."
    
    conn = db_connection()
    cursor = conn.cursor()
    
    # Get ALL payments for this flat (for history)
    cursor.execute('''
        SELECT * FROM payments 
        WHERE flat_id = ? 
        ORDER BY month DESC
    ''', (flat_id,))
    all_payments = cursor.fetchall()
    
    # Get ONLY DUE payments for dropdown (actual DUE records from database)
    cursor.execute('''
        SELECT * FROM payments 
        WHERE flat_id = ? AND status = 'DUE'
        ORDER BY month ASC
    ''', (flat_id,))
    due_payments = cursor.fetchall()
    
    # Calculate totals
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN status = 'PAID' THEN amount ELSE 0 END) as paid,
            SUM(CASE WHEN status = 'DUE' THEN amount ELSE 0 END) as due,
            SUM(amount) as total,
            SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) as paid_count,
            SUM(CASE WHEN status = 'DUE' THEN 1 ELSE 0 END) as due_count
        FROM payments 
        WHERE flat_id = ?
    ''', (flat_id,))
    
    totals = cursor.fetchone()
    conn.close()
    
    total_paid = totals['paid'] or 0
    total_due = totals['due'] or 0
    grand_total = totals['total'] or 0
    paid_count = totals['paid_count'] or 0
    due_count = totals['due_count'] or 0
    
    completion_rate = round((total_paid / grand_total * 100) if grand_total > 0 else 0, 1)
    
    user_data = {
        'full_name': session.get('full_name'),
        'flat_no': session.get('flat_no'),
        'flat_id': session.get('flat_id')
    }
    
    return render_template("resident_maintenance.html",
                         user=user_data,
                         all_payments=all_payments,
                         due_payments=due_payments,
                         total_paid=total_paid,
                         total_due=total_due,
                         grand_total=grand_total,
                         paid_count=paid_count,
                         due_count=due_count,
                         completion_rate=completion_rate,
                         success=success,
                         error=error_message)

@app.route("/resident/maintenance/pay", methods=['POST'])
@resident_required
def resident_pay_maintenance():
    flat_id = session.get('flat_id')
    flat_no = session.get('flat_no')
    month = request.form.get('month')
    amount = request.form.get('amount')
    transaction_id = request.form.get('transaction_id').strip().upper()
    
    conn = db_connection()
    cursor = conn.cursor()
    
    # Check if transaction ID already exists (case-insensitive)
    cursor.execute('SELECT * FROM payments WHERE UPPER(transaction_id) = ?', (transaction_id,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return redirect(url_for('resident_maintenance') + '?error=duplicate')
    
    # Update payment using flat_id (not flat_no)
    cursor.execute('''
        UPDATE payments
        SET status = 'PAID',
            payment_mode = 'UPI',
            transaction_id = ?,
            paid_date = ?,
            amount = ?
        WHERE flat_id = ? AND month = ?
    ''', (transaction_id, datetime.now().strftime('%Y-%m-%d'), amount, flat_id, month))
    
    rows_affected = cursor.rowcount
    
    # If no rows were updated, it means the record doesn't exist, so insert it
    if rows_affected == 0:
        cursor.execute('''
            INSERT INTO payments (flat_id, month, amount, status, payment_mode, transaction_id, paid_date)
            VALUES (?, ?, ?, 'PAID', 'UPI', ?, ?)
        ''', (flat_id, month, amount, transaction_id, datetime.now().strftime('%Y-%m-%d')))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('resident_maintenance') + '?success=1')

@app.route("/resident/expenses")
@resident_required
def resident_expenses():
    return "<h1>Resident Expenses - Coming in Phase 3</h1><a href='/resident'>Back to Home</a>"

@app.route("/resident/notify")
@resident_required
def resident_notify():
    return "<h1>Resident Notify Watchman - Coming in Phase 4</h1><a href='/resident'>Back to Home</a>"

@app.route("/resident/services")
@resident_required
def resident_services():
    return "<h1>Resident Services - Coming in Phase 5</h1><a href='/resident'>Back to Home</a>"

if __name__ == "__main__":
    app.run(debug=True)
