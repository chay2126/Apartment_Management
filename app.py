from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/maintenance")
def maintenance():
    return render_template("maintenence.html")

@app.route("/view/flats", methods=["GET"])
def get_flats_payments():
    month_filter = request.args.get("month")
    status_filter = request.args.get("status")
    
    conn = db_connection()
    
    query = 'SELECT * FROM payments WHERE 1=1'
    params = []
    
    if month_filter:
        query += ' AND month = ?'
        params.append(month_filter)
    
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)
    
    query += ' ORDER BY month DESC, flat_id'
    
    flats = conn.execute(query, params).fetchall()
    
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT month FROM payments ORDER BY month DESC')
    months = cursor.fetchall()
    
    conn.close()
    
    return render_template("view_payments.html", flats=flats, months=months)

@app.route("/due/payments", methods=['GET'])
def get_due_payments():
    month_filter = request.args.get("month")
    
    conn = db_connection()
    
    query = 'SELECT * FROM payments WHERE status = ?'
    params = ['DUE']
    
    if month_filter:
        query += ' AND month = ?'
        params.append(month_filter)
    
    query += ' ORDER BY month DESC, flat_id'
    
    flats = conn.execute(query, params).fetchall()
    
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT month FROM payments ORDER BY month DESC')
    months = cursor.fetchall()
    
    conn.close()
    
    return render_template("due_payments.html", flats=flats, months=months)

@app.route("/total/amount", methods=['GET'])
def get_total_amount():
    conn = db_connection()
    
    cursor = conn.cursor()
    cursor.execute('SELECT month FROM payments ORDER BY month DESC LIMIT 1')
    recent_month_row = cursor.fetchone()
    
    if not recent_month_row:
        conn.close()
        return render_template("total_amount.html", recent_month=None, total_collected=0, total_due=0, grand_total=0, flats=[])
    
    recent_month = recent_month_row['month']
    
    cursor.execute('SELECT * FROM payments WHERE month = ? ORDER BY flat_id', (recent_month,))
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
def delete_expense(expense_id):
    conn = db_connection()
    conn.execute('DELETE FROM expenses WHERE expense_id = ?', (expense_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_expenses'))

# Add these routes after the expenses routes

# SERVICES ROUTES
@app.route("/services", methods=['GET'])
def view_services():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM services ORDER BY category, service_name')
    services = cursor.fetchall()
    conn.close()
    
    return render_template("services.html", services=services)

@app.route("/services/add", methods=['POST'])
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
def delete_service(service_id):
    conn = db_connection()
    conn.execute('DELETE FROM services WHERE service_id = ?', (service_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_services'))    

# NOTIFY WATCHMAN ROUTES - TELEGRAM VERSION
@app.route("/notify")
def notify_watchman():
    return render_template("notify_watchman.html")

@app.route("/notify/send", methods=['POST'])
def send_notification():
    flat_no = request.form.get('flat_no')
    message_type = request.form.get('message_type')
    custom_message = request.form.get('custom_message')
    
    # Prepare message based on type
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


@app.route("/api/notices", methods=['GET'])
def get_notices():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notices ORDER BY priority DESC, created_date DESC')
    notices = cursor.fetchall()
    conn.close()
    
    # Convert to list of dicts
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
def delete_notice(notice_id):
    conn = db_connection()
    conn.execute('DELETE FROM notices WHERE notice_id = ?', (notice_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})        


                

if __name__ == "__main__":
    app.run(debug=True)
