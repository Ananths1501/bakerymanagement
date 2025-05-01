from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import mysql.connector
from datetime import datetime, timedelta
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = 'bakery_secret_key_2024'

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

# Check if user is logged in
def is_logged_in():
    return 'user_id' in session

# Require login for certain routes
def login_required(route_function):
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash('Please login to access this page', 'error')
            return redirect(url_for('login_page'))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user and check_password_hash(user['password'], password):
            # Store user info in session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            # Log the login
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO login_history (user_id, login_time) VALUES (%s, %s)",
                (user['id'], datetime.now())
            )
            connection.commit()
            cursor.close()
            connection.close()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        role = request.form.get('role', 'staff')
        
        # Check if username already exists
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            connection.close()
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (full_name, email, username, password) VALUES (%s, %s, %s, %s)",
            (full_name, email, username, hashed_password)
        )
        connection.commit()
        cursor.close()
        connection.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login_page'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get total sales
    cursor.execute("SELECT SUM(total_amount) as total_sales FROM bills")
    total_sales = cursor.fetchone()['total_sales'] or 0
    
    # Get total customers
    cursor.execute("SELECT COUNT(DISTINCT customer_phone) as total_customers FROM bills")
    total_customers = cursor.fetchone()['total_customers'] or 0
    
    # Get total products
    cursor.execute("SELECT COUNT(*) as total_products FROM stocks")
    total_products = cursor.fetchone()['total_products'] or 0
    
    # Get low stock items
    cursor.execute("SELECT name, category, quantity FROM stocks WHERE quantity < 10")
    low_stock = cursor.fetchall()
    
    # Get recent sales
    cursor.execute("""
        SELECT b.id, b.customer_name, b.total_amount, b.bill_date 
        FROM bills b 
        ORDER BY b.bill_date DESC LIMIT 5
    """)
    recent_sales = cursor.fetchall()
    
    # Get sales data for chart
    cursor.execute("""
        SELECT DATE(bill_date) as date, SUM(total_amount) as amount 
        FROM bills 
        WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(bill_date)
        ORDER BY date
    """)
    sales_data = cursor.fetchall()
    
    # Format for chart
    dates = [sale['date'].strftime('%Y-%m-%d') for sale in sales_data]
    amounts = [float(sale['amount']) for sale in sales_data]
    
    cursor.close()
    connection.close()
    
    return render_template('dashboard.html', 
                          total_sales=total_sales,
                          total_customers=total_customers,
                          total_products=total_products,
                          low_stock=low_stock,
                          recent_sales=recent_sales,
                          dates=json.dumps(dates),
                          amounts=json.dumps(amounts))

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    return render_template('billing.html')

@app.route('/customers')
@login_required
def customers():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT customer_name, customer_phone, 
               COUNT(id) as visit_count, 
               SUM(total_amount) as total_spent,
               MAX(bill_date) as last_visit 
        FROM bills 
        GROUP BY customer_phone, customer_name
        ORDER BY last_visit DESC
    """)
    customers_data = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('customers.html', customers_data=customers_data)

@app.route('/customer_details/<phone>')
@login_required
def customer_details(phone):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get customer info
    cursor.execute("""
        SELECT customer_name, customer_phone, 
               COUNT(id) as visit_count, 
               SUM(total_amount) as total_spent,
               MAX(bill_date) as last_visit,
               MIN(bill_date) as first_visit
        FROM bills 
        WHERE customer_phone = %s
        GROUP BY customer_phone, customer_name
    """, (phone,))
    customer = cursor.fetchone()
    
    # Get customer purchase history
    cursor.execute("""
        SELECT b.id, b.bill_date, b.total_amount,
               GROUP_CONCAT(CONCAT(bi.item_name, ' (', bi.quantity, ')') SEPARATOR ', ') as items
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

@app.route('/stocks')
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
        quantity = request.form['quantity']
        unit_price = request.form['unit_price']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if item already exists
        cursor.execute("SELECT id FROM stocks WHERE name = %s AND category = %s", (name, category))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing stock
            cursor.execute(
                "UPDATE stocks SET quantity = quantity + %s, unit_price = %s WHERE name = %s AND category = %s",
                (quantity, unit_price, name, category)
            )
            flash(f'Updated existing stock for {name}', 'success')
        else:
            # Add new stock
            cursor.execute(
                "INSERT INTO stocks (name, category, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                (name, category, quantity, unit_price)
            )
            flash(f'Added new stock item: {name}', 'success')
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('stocks'))
    
    # Get existing categories for dropdown
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
        
        cursor.execute(
            "UPDATE stocks SET name = %s, category = %s, quantity = %s, unit_price = %s WHERE id = %s",
            (name, category, quantity, unit_price, stock_id)
        )
        connection.commit()
        flash('Stock updated successfully', 'success')
        return redirect(url_for('stocks'))
    
    # Get stock item
    cursor.execute("SELECT * FROM stocks WHERE id = %s", (stock_id,))
    stock = cursor.fetchone()
    
    # Get categories for dropdown
    cursor.execute("SELECT DISTINCT category FROM stocks")
    categories = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('edit_stock.html', stock=stock, categories=categories)

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
@login_required
def delete_stock(stock_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM stocks WHERE id = %s", (stock_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Stock item deleted successfully', 'success')
    return redirect(url_for('stocks'))

@app.route('/get_categories')
def get_categories():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT category FROM stocks")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify({'categories': [cat['category'] for cat in categories]})

@app.route('/get_items_by_category/<category>')
def get_items_by_category(category):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT name, unit_price FROM stocks WHERE category = %s", (category,))
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
    total_amount = data['totalAmount']

    connection = get_db_connection()
    cursor = connection.cursor()

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
        SELECT b.*, DATE_FORMAT(b.bill_date, '%%d/%%m/%%Y %%H:%%i') as formatted_date 
        FROM bills b 
        WHERE b.id = %s
    """, (bill_id,))
    bill = cursor.fetchone()
    
    # Get bill items
    cursor.execute("""
        SELECT item_name, category, quantity, price, (quantity * price) as item_total 
        FROM bill_items 
        WHERE bill_id = %s
    """, (bill_id,))
    items = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('bill_receipt.html', bill=bill, items=items)

@app.route('/suppliers')
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
        cursor.execute(
            "INSERT INTO supplier (name, address, category, phone, email) VALUES (%s, %s, %s, %s, %s)",
            (name, address, category, phone, email)
        )
        connection.commit()
        cursor.close()
        connection.close()
        
        flash('Supplier added successfully', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('add_supplier.html')

@app.route('/edit_supplier/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        category = request.form['category']
        phone = request.form['phone']
        email = request.form['email']
        
        cursor.execute(
            "UPDATE supplier SET name = %s, address = %s, category = %s, phone = %s, email = %s WHERE id = %s",
            (name, address, category, phone, email, supplier_id)
        )
        connection.commit()
        flash('Supplier updated successfully', 'success')
        return redirect(url_for('suppliers'))
    
    cursor.execute("SELECT * FROM supplier WHERE id = %s", (supplier_id,))
    supplier = cursor.fetchone()
    cursor.close()
    connection.close()
    
    return render_template('edit_supplier.html', supplier=supplier)

@app.route('/delete_supplier/<int:supplier_id>', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM supplier WHERE id = %s", (supplier_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Supplier deleted successfully', 'success')
    return redirect(url_for('suppliers'))

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/sales_report', methods=['POST'])
@login_required
def sales_report():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Get sales summary
    cursor.execute("""
        SELECT COUNT(*) as total_bills, 
               SUM(total_amount) as total_sales,
               AVG(total_amount) as average_sale
        FROM bills
        WHERE bill_date BETWEEN %s AND %s
    """, (start_date, end_date))
    summary = cursor.fetchone()
    
    # Get sales by category
    cursor.execute("""
        SELECT bi.category, 
               SUM(bi.quantity) as total_quantity,
               SUM(bi.quantity * bi.price) as total_amount
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        WHERE b.bill_date BETWEEN %s AND %s
        GROUP BY bi.category
        ORDER BY total_amount DESC
    """, (start_date, end_date))
    sales_by_category = cursor.fetchall()
    
    # Get top selling products
    cursor.execute("""
        SELECT bi.item_name, bi.category,
               SUM(bi.quantity) as total_quantity,
               SUM(bi.quantity * bi.price) as total_amount
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        WHERE b.bill_date BETWEEN %s AND %s
        GROUP BY bi.item_name, bi.category
        ORDER BY total_quantity DESC
        LIMIT 10
    """, (start_date, end_date))
    top_products = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('sales_report.html', 
                          start_date=start_date, 
                          end_date=end_date,
                          summary=summary,
                          sales_by_category=sales_by_category,
                          top_products=top_products)

@app.route('/setup_database')
def setup_database():
    """Initialize the database with sample data (for demonstration purposes)"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Create tables if they don't exist
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(100) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        role ENUM('admin', 'manager', 'staff') DEFAULT 'staff',
        created_at DATETIME NOT NULL
    )
    """)
    
    # Login history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        login_time DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Stocks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        UNIQUE KEY name_category (name, category)
    )
    """)
    
    # Supplier table
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
    
    # Bills table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INT AUTO_INCREMENT PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        customer_phone VARCHAR(20) NOT NULL,
        bill_date DATETIME NOT NULL,
        total_amount DECIMAL(10,2) DEFAULT 0
    )
    """)
    
    # Bill items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bill_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        bill_id INT NOT NULL,
        item_name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (bill_id) REFERENCES bills(id)
    )
    """)
    
    # Insert sample data
    
    # Sample admin user
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password, email, full_name, role, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            ('admin', generate_password_hash('admin123'), 'admin@bakery.com', 'Admin User', 'admin', datetime.now())
        )
        cursor.execute(
            "INSERT INTO users (username, password, email, full_name, role, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            ('staff', generate_password_hash('staff123'), 'staff@bakery.com', 'Staff User', 'staff', datetime.now())
        )
    
    # Sample stock categories and items
    stock_categories = ['Cakes', 'Pastries', 'Bread', 'Cookies', 'Beverages']
    stock_items = [
        # Cakes
        ('Chocolate Cake', 'Cakes', 20, 450.00),
        ('Vanilla Cake', 'Cakes', 15, 400.00),
        ('Red Velvet Cake', 'Cakes', 10, 500.00),
        ('Black Forest Cake', 'Cakes', 8, 550.00),
        ('Pineapple Cake', 'Cakes', 12, 400.00),
        # Pastries
        ('Croissant', 'Pastries', 30, 60.00),
        ('Danish', 'Pastries', 25, 70.00),
        ('Eclair', 'Pastries', 20, 80.00),
        ('Cinnamon Roll', 'Pastries', 15, 90.00),
        # Bread
        ('White Bread', 'Bread', 40, 40.00),
        ('Wheat Bread', 'Bread', 35, 45.00),
        ('Baguette', 'Bread', 20, 60.00),
        ('Multigrain Bread', 'Bread', 15, 55.00),
        # Cookies
        ('Chocolate Chip Cookie', 'Cookies', 50, 20.00),
        ('Oatmeal Cookie', 'Cookies', 40, 25.00),
        ('Peanut Butter Cookie', 'Cookies', 35, 30.00),
        # Beverages
        ('Coffee', 'Beverages', 100, 50.00),
        ('Tea', 'Beverages', 100, 40.00),
        ('Hot Chocolate', 'Beverages', 50, 60.00),
    ]
    
    cursor.execute("SELECT COUNT(*) FROM stocks")
    if cursor.fetchone()[0] == 0:
        for item in stock_items:
            cursor.execute(
                "INSERT INTO stocks (name, category, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                item
            )
    
    # Sample suppliers
    suppliers = [
        ('Flour Supplies Inc.', '123 Baker Street, Flour City', 'Bread', '555-1234', 'flour@example.com'),
        ('Sweet Ingredients Co.', '456 Sugar Lane, Sweet Town', 'Cakes', '555-5678', 'sweet@example.com'),
        ('Dairy Fresh', '789 Milk Road, Cream City', 'Pastries', '555-9012', 'dairy@example.com'),
        ('Coffee Beans Ltd.', '321 Bean Avenue, Coffee Town', 'Beverages', '555-3456', 'coffee@example.com'),
    ]
    
    cursor.execute("SELECT COUNT(*) FROM supplier")
    if cursor.fetchone()[0] == 0:
        for supplier in suppliers:
            cursor.execute(
                "INSERT INTO supplier (name, address, category, phone, email) VALUES (%s, %s, %s, %s, %s)",
                supplier
            )
    
    # Sample bills and bill items
    cursor.execute("SELECT COUNT(*) FROM bills")
    if cursor.fetchone()[0] == 0:
        # Generate sample customers
        customers = [
            ('John Doe', '9876543210'),
            ('Jane Smith', '8765432109'),
            ('Robert Johnson', '7654321098'),
            ('Emily Davis', '6543210987'),
            ('Michael Wilson', '5432109876')
        ]
        
        # Generate sample bills for the past 30 days
        for i in range(30):
            bill_date = datetime.now() - timedelta(days=i)
            
            # Generate 1-3 bills per day
            for j in range(random.randint(1, 3)):
                customer = random.choice(customers)
                
                # Insert bill
                cursor.execute(
                    "INSERT INTO bills (customer_name, customer_phone, bill_date, total_amount) VALUES (%s, %s, %s, %s)",
                    (customer[0], customer[1], bill_date, 0)
                )
                bill_id = cursor.lastrowid
                
                # Generate 1-5 items per bill
                total_amount = 0
                for k in range(random.randint(1, 5)):
                    # Select random item from stock
                    item = random.choice(stock_items)
                    quantity = random.randint(1, 3)
                    price = item[3]
                    item_total = quantity * price
                    total_amount += item_total
                    
                    # Insert bill item
                    cursor.execute(
                        "INSERT INTO bill_items (bill_id, item_name, category, quantity, price) VALUES (%s, %s, %s, %s, %s)",
                        (bill_id, item[0], item[1], quantity, price)
                    )
                
                # Update bill total
                cursor.execute(
                    "UPDATE bills SET total_amount = %s WHERE id = %s",
                    (total_amount, bill_id)
                )
    
    connection.commit()
    cursor.close()
    connection.close()
    
    return "Database setup complete with sample data!"

if __name__ == '__main__':
    app.run(debug=True)
