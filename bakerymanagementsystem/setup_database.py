import mysql.connector
from datetime import datetime, timedelta
import random

# Database configuration
db_config = {
    'user': 'root',
    'password': 'Praveen@16',
    'host': 'localhost',
}

def create_database():
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password']
    )
    cursor = connection.cursor()
    
    # Create database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS cakeshop")
    cursor.execute("USE cakeshop")
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(255) DEFAULT 'user',
        login_time DATETIME NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INT AUTO_INCREMENT PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        customer_phone VARCHAR(20) NOT NULL,
        bill_date DATETIME NOT NULL,
        total_amount DECIMAL(10, 2) DEFAULT 0.00
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bill_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        bill_id INT NOT NULL,
        item_name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS supplier (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        address TEXT NOT NULL,
        category VARCHAR(50) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        email VARCHAR(100) NOT NULL
    )
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_time DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
    );""")
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print("Database and tables created successfully!")

def insert_sample_data():
    connection = mysql.connector.connect(**db_config, database='cakeshop')
    cursor = connection.cursor()
    
    # Sample users
    users = [
        ('admin', 'admin123', 'Admin User', 'admin@sweetdelights.com'),
        ('john', 'john123', 'John Smith', 'john@example.com'),
        ('sarah', 'sarah123', 'Sarah Johnson', 'sarah@example.com')
    ]
    
    for user in users:
        try:
            cursor.execute(
                "INSERT INTO users (username, password, full_name, email) VALUES (%s, %s, %s, %s)",
                user
            )
        except mysql.connector.errors.IntegrityError:
            print(f"User {user[0]} already exists, skipping...")
    
    # Sample stock categories and items
    stock_items = [
        # Cakes
        ('Chocolate Cake', 'Cakes', 20, 450.00),
        ('Vanilla Cake', 'Cakes', 15, 400.00),
        ('Red Velvet Cake', 'Cakes', 10, 500.00),
        ('Black Forest Cake', 'Cakes', 8, 550.00),
        ('Pineapple Cake', 'Cakes', 12, 420.00),
        
        # Pastries
        ('Chocolate Eclair', 'Pastries', 30, 60.00),
        ('Cream Puff', 'Pastries', 25, 50.00),
        ('Apple Turnover', 'Pastries', 20, 70.00),
        ('Fruit Tart', 'Pastries', 15, 80.00),
        ('Chocolate Croissant', 'Pastries', 18, 65.00),
        
        # Cookies
        ('Chocolate Chip Cookie', 'Cookies', 50, 25.00),
        ('Oatmeal Raisin Cookie', 'Cookies', 40, 30.00),
        ('Peanut Butter Cookie', 'Cookies', 45, 28.00),
        ('Almond Cookie', 'Cookies', 35, 32.00),
        ('Sugar Cookie', 'Cookies', 55, 20.00),
        
        # Breads
        ('White Bread', 'Breads', 25, 40.00),
        ('Whole Wheat Bread', 'Breads', 20, 45.00),
        ('Baguette', 'Breads', 15, 50.00),
        ('Multigrain Bread', 'Breads', 18, 55.00),
        ('Garlic Bread', 'Breads', 22, 60.00),
        
        # Beverages
        ('Coffee', 'Beverages', 100, 30.00),
        ('Tea', 'Beverages', 80, 25.00),
        ('Hot Chocolate', 'Beverages', 60, 35.00),
        ('Fruit Juice', 'Beverages', 70, 40.00),
        ('Milkshake', 'Beverages', 50, 60.00)
    ]
    
    for item in stock_items:
        cursor.execute(
            "INSERT INTO stocks (name, category, quantity, unit_price) VALUES (%s, %s, %s, %s)",
            item
        )
    
    # Sample suppliers
    suppliers = [
        ('Flour Power Co.', '123 Wheat Street, Flourville', 'Flour & Grains', '555-1234', 'info@flourpower.com'),
        ('Dairy Delight', '456 Milk Road, Creamtown', 'Dairy', '555-2345', 'orders@dairydelight.com'),
        ('Sweet Success', '789 Sugar Lane, Sweetville', 'Sugar & Sweeteners', '555-3456', 'sales@sweetsuccess.com'),
        ('Fruit Fusion', '101 Orchard Way, Fruitland', 'Fruits & Nuts', '555-4567', 'contact@fruitfusion.com'),
        ('Choco World', '202 Cocoa Avenue, Chocolateville', 'Chocolate & Cocoa', '555-5678', 'info@chocoworld.com'),
        ('Pack Perfect', '303 Box Street, Wraptown', 'Packaging', '555-6789', 'service@packperfect.com'),
        ('Baker\'s Best Equipment', '404 Tool Road, Gearville', 'Equipment', '555-7890', 'sales@bakersbestequip.com')
    ]
    
    for supplier in suppliers:
        cursor.execute(
            "INSERT INTO supplier (name, address, category, phone, email) VALUES (%s, %s, %s, %s, %s)",
            supplier
        )
    
    # Sample customer bills and items
    customer_names = ['Raj Kumar', 'Priya Sharma', 'Amit Patel', 'Neha Singh', 'Vikram Mehta', 
                     'Ananya Gupta', 'Rahul Verma', 'Pooja Reddy', 'Sanjay Joshi', 'Meera Kapoor']
    
    phone_prefixes = ['98765', '87654', '76543', '65432', '54321']
    phone_suffixes = ['12345', '23456', '34567', '45678', '56789']
    
    # Generate bills for the past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    current_date = start_date
    while current_date <= end_date:
        # Generate 1-3 bills per day
        for _ in range(random.randint(1, 3)):
            customer_name = random.choice(customer_names)
            customer_phone = f"{random.choice(phone_prefixes)}{random.choice(phone_suffixes)}"
            bill_date = current_date.replace(
                hour=random.randint(8, 20),
                minute=random.randint(0, 59)
            )
            total_amount = 0
            bill_items = []
            
            # Generate 1-5 items per bill
            for _ in range(random.randint(1, 5)):
                item = random.choice(stock_items)
                quantity = random.randint(1, 5)
                price = item[3]
                total_amount += quantity * price
                bill_items.append((item[0], item[1], quantity, price))
            
            # Insert bill into bills table
            cursor.execute(
                "INSERT INTO bills (customer_name, customer_phone, bill_date, total_amount) VALUES (%s, %s, %s, %s)",
                (customer_name, customer_phone, bill_date, total_amount)
            )
            bill_id = cursor.lastrowid
            
            # Insert bill items into bill_items table
            for item in bill_items:
                cursor.execute(
                    "INSERT INTO bill_items (bill_id, item_name, category, quantity, price) VALUES (%s, %s, %s, %s, %s)",
                    (bill_id, item[0], item[1], item[2], item[3])
                )
        
        current_date += timedelta(days=1)
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print("Sample data inserted successfully!")

if __name__ == '__main__':
    create_database()
    insert_sample_data()

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import mysql.connector
from datetime import datetime, timedelta
import random
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
db_config = {
    'user': 'root',
    'password': 'Praveen@16',
    'host': 'localhost',
    'database': 'cakeshop'
}

# Helper function to get a database connection
def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    return connection

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and user['password'] == password:  # In a real app, use password hashing
            # Record login
            login_time = datetime.now()
            cursor.execute(
                "INSERT INTO login (username, password, login_time) VALUES (%s, %s, %s)",
                (username, password, login_time)
            )
            connection.commit()
            
            # Set session variables
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
        
        cursor.close()
        connection.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (full_name, email, username, password) VALUES (%s, %s, %s, %s)",
                (full_name, email, username, password)
            )
            connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry error
                flash('Username or email already exists', 'error')
            else:
                flash(f'An error occurred: {err}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get total sales
    cursor.execute("SELECT SUM(total_amount) as total_sales FROM bills")
    result = cursor.fetchone()
    total_sales = result['total_sales'] if result['total_sales'] else 0
    
    # Get total customers (unique)
    cursor.execute("SELECT COUNT(DISTINCT customer_phone) as total_customers FROM bills")
    total_customers = cursor.fetchone()['total_customers']
    
    # Get total products
    cursor.execute("SELECT COUNT(*) as total_products FROM stocks")
    total_products = cursor.fetchone()['total_products']
    
    # Get low stock items
    cursor.execute("SELECT * FROM stocks WHERE quantity < 10 ORDER BY quantity ASC LIMIT 5")
    low_stock = cursor.fetchall()
    
    # Get recent sales
    cursor.execute("""
        SELECT b.id, b.customer_name, b.bill_date, b.total_amount 
        FROM bills b 
        ORDER BY b.bill_date DESC 
        LIMIT 5
    """)
    recent_sales = cursor.fetchall()
    
    # Get sales data for the last 7 days
    cursor.execute("""
        SELECT DATE(bill_date) as date, SUM(total_amount) as amount
        FROM bills
        WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(bill_date)
        ORDER BY date
    """)
    sales_data = cursor.fetchall()
    
    dates = [sale['date'].strftime('%d/%m') for sale in sales_data]
    amounts = [float(sale['amount']) for sale in sales_data]
    
    cursor.close()
    connection.close()
    
    return render_template('dashboard.html', 
                          total_sales=total_sales,
                          total_customers=total_customers,
                          total_products=total_products,
                          low_stock=low_stock,
                          recent_sales=recent_sales,
                          dates=dates,
                          amounts=amounts)

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    return render_template('billing.html')

@app.route('/get_categories', methods=['GET'])
@login_required
def get_categories():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT category FROM stocks")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify({'categories': [cat['category'] for cat in categories]})

@app.route('/get_items_by_category/<category>', methods=['GET'])
@login_required
def get_items_by_category(category):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT name, unit_price FROM stocks WHERE category = %s AND quantity > 0", (category,))
    items = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify({'items': items})

@app.route('/submit_bill', methods=['POST'])
@login_required
def submit_bill():
    data = request.get_json()
    customer_name = data['customerName']
    customer_phone = data['customerPhone']
    bill_items = data['billItems']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Calculate total amount
    total_amount = sum(float(item['price']) * int(item['quantity']) for item in bill_items)
    
    # Insert the bill into the bills table
    bill_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO bills (customer_name, customer_phone, bill_date, total_amount) VALUES (%s, %s, %s, %s)",
        (customer_name, customer_phone, bill_date, total_amount)
    )
    bill_id = cursor.lastrowid
    
    # Insert each bill item into the bill_items table and update the stocks table
    for item in bill_items:
        cursor.execute(
            "INSERT INTO bill_items (bill_id, item_name, category, quantity, price) VALUES (%s, %s, %s, %s, %s)",
            (bill_id, item['itemName'], item['category'], item['quantity'], item['price'])
        )
        cursor.execute(
            "UPDATE stocks SET quantity = quantity - %s WHERE name = %s AND category = %s",
            (item['quantity'], item['itemName'], item['category'])
        )
    
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Bill saved successfully!", "bill_id": bill_id})

@app.route('/bill_receipt/<int:bill_id>')
@login_required
def bill_receipt(bill_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get bill details
    cursor.execute("""
        SELECT b.*, DATE_FORMAT(b.bill_date, '%d/%m/%Y %H:%i') as formatted_date
        FROM bills b
        WHERE b.id = %s
    """, (bill_id,))
    bill = cursor.fetchone()
    
    if not bill:
        flash('Bill not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Get bill items
    cursor.execute("""
        SELECT bi.*, (bi.quantity * bi.price) as item_total
        FROM bill_items bi
        WHERE bi.bill_id = %s
    """, (bill_id,))
    items = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('bill_receipt.html', bill=bill, items=items)

@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get unique customers with their latest bill date
    cursor.execute("""
        SELECT customer_name, customer_phone, MAX(bill_date) as last_visit
        FROM bills
        GROUP BY customer_name, customer_phone
        ORDER BY last_visit DESC
    """)
    customers_data = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('customers.html', customers_data=customers_data)

@app.route('/customer/<phone>')
@login_required
def customer_details(phone):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get customer info
    cursor.execute("""
        SELECT customer_name, customer_phone, 
               MIN(bill_date) as first_visit, 
               MAX(bill_date) as last_visit,
               COUNT(*) as visit_count,
               SUM(total_amount) as total_spent
        FROM bills
        WHERE customer_phone = %s
        GROUP BY customer_name, customer_phone
    """, (phone,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    # Get purchase history
    cursor.execute("""
        SELECT b.id, b.bill_date, b.total_amount,
               GROUP_CONCAT(bi.item_name SEPARATOR ', ') as items
        FROM bills b
        JOIN bill_items bi ON b.id = bi.bill_id
        WHERE b.customer_phone = %s
        GROUP BY b.id
        ORDER BY b.bill_date DESC
    """, (phone,))
    purchase_history = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('customer_details.html', customer=customer, purchase_history=purchase_history)

@app.route('/stocks', methods=['GET', 'POST'])
@login_required
def stocks():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT category FROM stocks")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('stocks.html', categories=categories)

@app.route('/stocks/<category>')
@login_required
def get_stocks_by_category(category):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, name, quantity, unit_price FROM stocks WHERE category = %s"
    cursor.execute(query, (category,))
    stocks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('stocks_category.html', category=category, stocks=stocks)

@app.route('/add_stock', methods=['GET', 'POST'])
@login_required
def add_stock():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        
        if category == 'new':
            category = request.form['newCategory']
        
        quantity = request.form['quantity']
        unit_price = request.form['unit_price']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO stocks (name, category, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                (name, category, quantity, unit_price)
            )
            connection.commit()
            flash('Stock item added successfully!', 'success')
            return redirect(url_for('stocks'))
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    # Get categories for the form
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT category FROM stocks")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('add_stock.html', categories=categories)

@app.route('/edit_stock/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def edit_stock(stock_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        quantity = request.form['quantity']
        unit_price = request.form['unit_price']
        
        try:
            cursor.execute(
                "UPDATE stocks SET name = %s, category = %s, quantity = %s, unit_price = %s WHERE id = %s",
                (name, category, quantity, unit_price, stock_id)
            )
            connection.commit()
            flash('Stock item updated successfully!', 'success')
            return redirect(url_for('get_stocks_by_category', category=category))
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
    
    # Get stock item
    cursor.execute("SELECT * FROM stocks WHERE id = %s", (stock_id,))
    stock = cursor.fetchone()
    
    if not stock:
        flash('Stock item not found', 'error')
        return redirect(url_for('stocks'))
    
    # Get categories for the form
    cursor.execute("SELECT DISTINCT category FROM stocks")
    categories = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('edit_stock.html', stock=stock, categories=categories)

@app.route('/delete_stock/<int:stock_id>')
@login_required
def delete_stock(stock_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get stock category before deletion
    cursor.execute("SELECT category FROM stocks WHERE id = %s", (stock_id,))
    stock = cursor.fetchone()
    
    if not stock:
        flash('Stock item not found', 'error')
        return redirect(url_for('stocks'))
    
    category = stock['category']
    
    # Delete the stock item
    cursor.execute("DELETE FROM stocks WHERE id = %s", (stock_id,))
    connection.commit()
    
    flash('Stock item deleted successfully!', 'success')
    
    cursor.close()
    connection.close()
    
    return redirect(url_for('get_stocks_by_category', category=category))

@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM supplier")
    suppliers = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/add_supplier', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        category = request.form['category']
        phone = request.form['phone']
        email = request.form['email']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO supplier (name, address, category, phone, email) VALUES (%s, %s, %s, %s, %s)",
                (name, address, category, phone, email)
            )
            connection.commit()
            flash('Supplier added successfully!', 'success')
            return redirect(url_for('suppliers'))
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('add_supplier.html')

@app.route('/reports')
@login_required
def reports():
    # This would be implemented with more detailed reporting functionality
    flash('Reports feature coming soon!', 'info')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
