from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_stats():
    conn = get_db_connection()
    today = datetime.now().date()
    
    # Total medicines
    total = conn.execute('SELECT COUNT(*) as count FROM medicines').fetchone()['count']
    
    # Expiring within 7 days
    week_alert = today + timedelta(days=7)
    expiring_soon = conn.execute('''
        SELECT COUNT(*) as count FROM medicines 
        WHERE expiry_date <= ? AND expiry_date >= ?
    ''', (week_alert.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()['count']
    
    # Expiring within 30 days
    month_alert = today + timedelta(days=30)
    expiring_month = conn.execute('''
        SELECT COUNT(*) as count FROM medicines 
        WHERE expiry_date <= ? AND expiry_date >= ?
    ''', (month_alert.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()['count']
    
    # Total quantity
    total_qty = conn.execute('SELECT SUM(quantity) as total FROM medicines').fetchone()['total'] or 0
    
    conn.close()
    
    return {
        'total': total,
        'expiring_soon': expiring_soon,
        'expiring_month': expiring_month,
        'total_quantity': total_qty
    }

@app.route('/')
def home():
    stats = get_dashboard_stats()
    return render_template('index.html', stats=stats)

@app.route('/add', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        try:
            name = request.form['name']
            quantity = request.form['quantity']
            expiry_date = request.form['expiry_date']
            batch_number = request.form['batch_number']
            category = request.form['category']
            
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO medicines (name, quantity, expiry_date, batch_number, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, quantity, expiry_date, batch_number, category))
            conn.commit()
            conn.close()
            
            return redirect(url_for('list_medicines'))
        except Exception as e:
            return f"Error: {str(e)}"
    
    return render_template('add_medicine.html')

@app.route('/list')
def list_medicines():
    conn = get_db_connection()
    medicines = conn.execute('SELECT * FROM medicines ORDER BY expiry_date').fetchall()
    conn.close()
    
    # Calculate status for each medicine
    today = datetime.now().date()
    medicine_list = []
    for med in medicines:
        expiry = datetime.strptime(med['expiry_date'], '%Y-%m-%d').date()
        days_left = (expiry - today).days
        
        if days_left < 0:
            status = 'expired'
        elif days_left <= 7:
            status = 'expiring'
        else:
            status = 'safe'
            
        medicine_list.append({
            'id': med['id'],
            'name': med['name'],
            'quantity': med['quantity'],
            'expiry_date': med['expiry_date'],
            'batch_number': med['batch_number'],
            'category': med['category'],
            'status': status,
            'days_left': days_left
        })
    
    return render_template('list_medicines.html', medicines=medicine_list)

@app.route('/alerts')
def alerts():
    conn = get_db_connection()
    today = datetime.now().date()
    alert_date = today + timedelta(days=30)
    
    medicines = conn.execute('''
        SELECT * FROM medicines 
        WHERE expiry_date <= ? AND expiry_date >= ?
        ORDER BY expiry_date
    ''', (alert_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchall()
    
    conn.close()
    
    # Calculate days left
    medicine_list = []
    for med in medicines:
        expiry = datetime.strptime(med['expiry_date'], '%Y-%m-%d').date()
        days_left = (expiry - today).days
        
        medicine_list.append({
            'id': med['id'],
            'name': med['name'],
            'quantity': med['quantity'],
            'expiry_date': med['expiry_date'],
            'batch_number': med['batch_number'],
            'category': med['category'],
            'days_left': days_left
        })
    
    return render_template('alerts.html', medicines=medicine_list, alert_days=30)

@app.route('/delete/<int:id>')
def delete_medicine(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM medicines WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_medicines'))

if __name__ == '__main__':
    app.run(debug=True)
