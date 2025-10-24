from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db
from models import User, Medicine, Transaction, Sale, ExpiredMedicine
from datetime import datetime, date, timedelta
import re
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medicine_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_current_date():
    from datetime import date
    return {'current_date': date.today()}

# Inject navigation links and categories to all templates
@app.context_processor
def inject_navigation():
    categories = ['tablet', 'syrup', 'capsule', 'ointment', 'injection', 'drops', 'inhaler', 'cream', 'gel', 'powder']
    return {
        'navigation': [
            {'name': 'Dashboard', 'url': url_for('dashboard'), 'icon': 'fas fa-tachometer-alt'},
            {'name': 'All Medicines', 'url': url_for('medicines'), 'icon': 'fas fa-pills'},
            {'name': 'Add Medicine', 'url': url_for('add_medicine'), 'icon': 'fas fa-plus'},
            {'name': 'Expired Medicines', 'url': url_for('expired_medicines'), 'icon': 'fas fa-exclamation-triangle'},
            {'name': 'Sales', 'url': url_for('sales'), 'icon': 'fas fa-shopping-cart'},
            {'name': 'Transactions', 'url': url_for('transactions'), 'icon': 'fas fa-exchange-alt'},
        ],
        'categories': categories
    }

# Password validation function
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message)
            return redirect(url_for('signup'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Function to check and move expired medicines
def check_expired_medicines():
    expired_meds = Medicine.query.filter(
        Medicine.user_id == current_user.id,
        Medicine.expiry_date < date.today(),
        Medicine.quantity > 0
    ).all()
    
    for medicine in expired_meds:
        # Check if already in expired table
        existing = ExpiredMedicine.query.filter_by(medicine_id=medicine.id).first()
        if not existing:
            expired_record = ExpiredMedicine(
                medicine_id=medicine.id,
                user_id=current_user.id,
                name=medicine.name,
                batch_number=medicine.batch_number,
                category=medicine.category,
                quantity=medicine.quantity,
                price=medicine.price,
                expiry_date=medicine.expiry_date,
                original_value=medicine.quantity * medicine.price
            )
            db.session.add(expired_record)
    
    if expired_meds:
        db.session.commit()

@app.route('/dashboard')
@login_required
def dashboard():
    # Check for expired medicines
    check_expired_medicines()
    
    # Get alerts for expiring medicines (within 30 days)
    expiry_threshold = date.today() + timedelta(days=30)
    expiring_medicines = Medicine.query.filter(
        Medicine.user_id == current_user.id,
        Medicine.expiry_date <= expiry_threshold,
        Medicine.expiry_date >= date.today()
    ).all()
    
    # Get low stock alerts
    low_stock_medicines = Medicine.query.filter(
        Medicine.user_id == current_user.id,
        Medicine.quantity <= Medicine.low_stock_alert
    ).all()
    
    # Get total medicines count
    total_medicines = Medicine.query.filter_by(user_id=current_user.id).count()
    
    # Get expired medicines count
    expired_medicines = ExpiredMedicine.query.filter_by(user_id=current_user.id).count()
    
    # Get total stock value
    total_stock_value = db.session.query(db.func.sum(Medicine.quantity * Medicine.price)).filter(
        Medicine.user_id == current_user.id
    ).scalar() or 0
    
    # Get today's sales
    today_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.user_id == current_user.id,
        db.func.date(Sale.sale_date) == date.today()
    ).scalar() or 0
    
    # Get expired stock value
    expired_stock_value = db.session.query(db.func.sum(ExpiredMedicine.original_value)).filter(
        ExpiredMedicine.user_id == current_user.id
    ).scalar() or 0
    
    return render_template('dashboard.html',
                         expiring_medicines=expiring_medicines,
                         low_stock_medicines=low_stock_medicines,
                         total_medicines=total_medicines,
                         expired_medicines=expired_medicines,
                         total_stock_value=total_stock_value,
                         today_sales=today_sales,
                         expired_stock_value=expired_stock_value)

@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        name = request.form['name']
        batch_number = request.form['batch_number']
        category = request.form['category']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        low_stock_alert = int(request.form.get('low_stock_alert', 10))
        
        # Check if expiry date is valid
        if expiry_date <= date.today():
            flash('Expiry date must be greater than current date')
            return redirect(url_for('add_medicine'))
        
        medicine = Medicine(
            name=name,
            batch_number=batch_number,
            category=category,
            quantity=quantity,
            price=price,
            expiry_date=expiry_date,
            low_stock_alert=low_stock_alert,
            user_id=current_user.id
        )
        
        # Add medicine first and commit to get the ID
        db.session.add(medicine)
        db.session.commit()
        
        # Now add transaction record with the medicine ID
        transaction = Transaction(
            medicine_id=medicine.id,
            user_id=current_user.id,
            transaction_type='in',
            quantity=quantity,
            notes=f'Initial stock added'
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash('Medicine added successfully!')
        return redirect(url_for('medicines'))
    
    return render_template('add_medicine.html')

@app.route('/medicines')
@login_required
def medicines():
    from datetime import date, timedelta
    
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    
    # Build query with filters
    query = Medicine.query.filter(Medicine.user_id == current_user.id)
    
    if search:
        query = query.filter(Medicine.name.ilike(f'%{search}%'))
    
    if category_filter:
        query = query.filter(Medicine.category == category_filter)
    
    medicines_list = query.all()
    
    # Calculate expiry threshold (30 days from now)
    expiry_threshold = date.today() + timedelta(days=30)
    
    # Calculate total stock value
    total_stock_value = sum(med.quantity * med.price for med in medicines_list)
    total_items = sum(med.quantity for med in medicines_list)
    
    return render_template('medicines.html', 
                         medicines=medicines_list, 
                         search=search,
                         category_filter=category_filter,
                         current_date=date.today(),
                         expiry_threshold=expiry_threshold,
                         total_stock_value=total_stock_value,
                         total_items=total_items)

@app.route('/edit_medicine/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    
    # Check if medicine belongs to current user
    if medicine.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('medicines'))
    
    if request.method == 'POST':
        medicine.name = request.form['name']
        medicine.batch_number = request.form['batch_number']
        medicine.category = request.form['category']
        medicine.price = float(request.form['price'])
        medicine.low_stock_alert = int(request.form.get('low_stock_alert', 10))
        
        new_expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        if new_expiry_date <= date.today():
            flash('Expiry date must be greater than current date')
            return redirect(url_for('edit_medicine', medicine_id=medicine_id))
        
        medicine.expiry_date = new_expiry_date
        
        db.session.commit()
        flash('Medicine updated successfully!')
        return redirect(url_for('medicines'))
    
    return render_template('edit_medicine.html', medicine=medicine)

@app.route('/delete_medicine/<int:medicine_id>')
@login_required
def delete_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    
    # Check if medicine belongs to current user
    if medicine.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('medicines'))
    
    # Delete related transactions and sales first
    Transaction.query.filter_by(medicine_id=medicine_id).delete()
    Sale.query.filter_by(medicine_id=medicine_id).delete()
    ExpiredMedicine.query.filter_by(medicine_id=medicine_id).delete()
    db.session.delete(medicine)
    db.session.commit()
    
    flash('Medicine deleted successfully!')
    return redirect(url_for('medicines'))

@app.route('/update_stock/<int:medicine_id>', methods=['POST'])
@login_required
def update_stock(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    
    if medicine.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    action = request.form['action']
    quantity = int(request.form['quantity'])
    notes = request.form.get('notes', '')
    
    if action == 'add':
        medicine.quantity += quantity
        transaction_type = 'in'
    elif action == 'sell':
        if medicine.quantity < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        medicine.quantity -= quantity
        transaction_type = 'out'
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Add transaction record
    transaction = Transaction(
        medicine_id=medicine.id,
        user_id=current_user.id,
        transaction_type=transaction_type,
        quantity=quantity,
        notes=notes
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'success': True, 'new_quantity': medicine.quantity})

@app.route('/sell_medicine/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
def sell_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    
    if medicine.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('medicines'))
    
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        sale_price = float(request.form.get('sale_price', medicine.price))
        customer_name = request.form.get('customer_name', '')
        notes = request.form.get('notes', '')
        
        if quantity <= 0:
            flash('Quantity must be greater than 0')
            return redirect(url_for('sell_medicine', medicine_id=medicine_id))
        
        if medicine.quantity < quantity:
            flash(f'Insufficient stock. Available: {medicine.quantity}')
            return redirect(url_for('sell_medicine', medicine_id=medicine_id))
        
        total_amount = quantity * sale_price
        
        # Create sale record
        sale = Sale(
            medicine_id=medicine.id,
            user_id=current_user.id,
            quantity=quantity,
            sale_price=sale_price,
            total_amount=total_amount,
            customer_name=customer_name,
            notes=notes
        )
        
        # Update medicine quantity
        medicine.quantity -= quantity
        
        # Add transaction record
        transaction = Transaction(
            medicine_id=medicine.id,
            user_id=current_user.id,
            transaction_type='out',
            quantity=quantity,
            notes=f'Sold to {customer_name}. {notes}'
        )
        
        db.session.add(sale)
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Medicine sold successfully! Total amount: ₹{total_amount:.2f}')
        return redirect(url_for('medicines'))
    
    return render_template('sell_medicine.html', medicine=medicine)

@app.route('/sales')
@login_required
def sales():
    sales_list = Sale.query.join(Medicine).filter(
        Medicine.user_id == current_user.id
    ).order_by(Sale.sale_date.desc()).all()
    
    # Calculate total sales
    total_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.user_id == current_user.id
    ).scalar() or 0
    
    # Calculate today's sales
    today_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.user_id == current_user.id,
        db.func.date(Sale.sale_date) == date.today()
    ).scalar() or 0
    
    return render_template('sales.html', 
                         sales=sales_list, 
                         total_sales=total_sales,
                         today_sales=today_sales)

@app.route('/transactions')
@login_required
def transactions():
    transactions_list = Transaction.query.join(Medicine).filter(
        Medicine.user_id == current_user.id
    ).order_by(Transaction.transaction_date.desc()).all()
    
    return render_template('transactions.html', transactions=transactions_list)

@app.route('/expired_medicines')
@login_required
def expired_medicines():
    expired_list = ExpiredMedicine.query.filter_by(user_id=current_user.id).order_by(ExpiredMedicine.expired_at.desc()).all()
    
    total_expired_value = sum(med.original_value for med in expired_list)
    total_expired_items = sum(med.quantity for med in expired_list)
    
    return render_template('expired_medicines.html',
                         expired_medicines=expired_list,
                         total_expired_value=total_expired_value,
                         total_expired_items=total_expired_items)

@app.route('/api/medicines')
@login_required
def api_medicines():
    medicines = Medicine.query.filter_by(user_id=current_user.id).all()
    result = []
    
    for med in medicines:
        result.append({
            'id': med.id,
            'name': med.name,
            'batch_number': med.batch_number,
            'category': med.category,
            'quantity': med.quantity,
            'price': med.price,
            'expiry_date': med.expiry_date.isoformat(),
            'low_stock_alert': med.low_stock_alert,
            'is_expired': med.expiry_date < date.today(),
            'is_low_stock': med.quantity <= med.low_stock_alert,
            'is_expiring_soon': med.expiry_date <= (date.today() + timedelta(days=30))
        })
    
    return jsonify(result)

# Jinja2 filter for unique values
@app.template_filter('unique')
def unique_filter(sequence):
    seen = set()
    result = []
    for item in sequence:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)