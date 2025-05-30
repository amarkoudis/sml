import os
import sys
import pymysql
from werkzeug.security import generate_password_hash

def create_directory_structure():
    # Create directories
    directories = [
        'static/css',
        'templates'
    ]
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

def write_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created file: {file_path}")

def create_database_and_tables():
    try:
        # Connect to MySQL without selecting a database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS sml")
            cursor.execute("USE sml")
            
            # Create users table with hashed password
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    full_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    role VARCHAR(20) DEFAULT 'user'
                )
            """)
            
            # Create a default admin user (username: admin, password: admin123)
            admin_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            try:
                cursor.execute("""
                    INSERT INTO users (username, password, email, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, ('admin', admin_password, 'admin@sml.com', 'System Administrator', 'admin'))
                print("Default admin user created successfully!")
            except pymysql.err.IntegrityError:
                print("Admin user already exists.")
            
            connection.commit()
            print("Database and tables created successfully!")
            
    except Exception as e:
        print(f"Error creating database and tables: {str(e)}")
        sys.exit(1)
    finally:
        connection.close()

def get_updated_config_content():
    return '''from flask import Flask
from flaskext.mysql import MySQL
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'V0sp0r0si968!'
app.config['MYSQL_DATABASE_DB'] = 'sml'
app.config['MYSQL_DATABASE_PORT'] = 3306

# Secret key for session management
app.config['SECRET_KEY'] = '4256ccebf2245cc9e3651352e4540c16a42dade9250b9408e3dff75e40ddaa2d'

# Initialize MySQL
mysql.init_app(app)

def get_mysql_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            port=3306,
            cursorclass=pymysql.cursors.DictCursor
        )
        if connection:
            cursor = connection.cursor()
            return connection, cursor
    except Exception as e:
        print(f"Error connecting to MySQL: {str(e)}")
        return None, None'''

def get_updated_app_content():
    return '''from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import app, get_mysql_connection
from werkzeug.security import check_password_hash
from datetime import datetime

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        conn, cursor = get_mysql_connection()
        if conn and cursor:
            try:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                account = cursor.fetchone()
                
                if account and check_password_hash(account['password'], password):
                    # Update last login time
                    cursor.execute('UPDATE users SET last_login = %s WHERE id = %s', 
                                 (datetime.now(), account['id']))
                    conn.commit()
                    
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']
                    session['role'] = account['role']
                    return redirect(url_for('home'))
                else:
                    msg = 'Incorrect username/password!'
            except Exception as e:
                msg = f'An error occurred: {str(e)}'
            finally:
                cursor.close()
                conn.close()
        else:
            msg = 'Database connection error!'
            
    return render_template('login.html', msg=msg)

@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', 
                             username=session['username'], 
                             role=session['role'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)'''

def setup_project():
    # Create database and tables first
    create_database_and_tables()
    
    # Create directories
    directories = [
        'static/css',
        'templates'
    ]
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Write updated files
    write_file('config.py', get_updated_config_content())
    write_file('app.py', get_updated_app_content())
    
    # Login template
    login_template = '''<!DOCTYPE html>
<html>
<head>
    <title>Login - SML System</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="login-form">
        <h2>Login</h2>
        <form action="{{ url_for('login') }}" method="post">
            <div class="msg">{{ msg }}</div>
            <div class="form-group">
                <input type="text" name="username" placeholder="Username" required>
            </div>
            <div class="form-group">
                <input type="password" name="password" placeholder="Password" required>
            </div>
            <div class="form-group">
                <input type="submit" value="Login">
            </div>
        </form>
    </div>
</body>
</html>'''

    # Home template
    home_template = '''<!DOCTYPE html>
<html>
<head>
    <title>Home - SML System</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="home">
        <h1>Welcome to SML System</h1>
        <h2>Hello, {{ username }}!</h2>
        <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
    </div>
</body>
</html>'''

    # CSS file
    css_content = '''body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    margin: 0;
    padding: 0;
}

.login-form {
    width: 300px;
    margin: 100px auto;
    padding: 20px;
    background: white;
    border-radius: 5px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 15px;
}

input[type="text"],
input[type="password"] {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-sizing: border-box;
}

input[type="submit"] {
    width: 100%;
    padding: 10px;
    background: #4CAF50;
    border: none;
    color: white;
    border-radius: 4px;
    cursor: pointer;
}

input[type="submit"]:hover {
    background: #45a049;
}

.msg {
    margin-bottom: 15px;
    padding: 10px;
    border-radius: 4px;
    color: #721c24;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    display: none;
}

.msg:not(:empty) {
    display: block;
}

.home {
    text-align: center;
    padding: 50px;
}

.logout-btn {
    display: inline-block;
    padding: 10px 20px;
    background: #f44336;
    color: white;
    text-decoration: none;
    border-radius: 4px;
}

.logout-btn:hover {
    background: #da190b;
}'''

    # Requirements file
    requirements_content = '''Flask==2.0.1
Werkzeug==2.0.3
flask-mysql==1.5.2
PyMySQL==1.0.2'''

    # Write all files
    write_file('templates/login.html', login_template)
    write_file('templates/home.html', home_template)
    write_file('static/css/style.css', css_content)
    write_file('requirements.txt', requirements_content)

if __name__ == "__main__":
    try:
        setup_project()
        print("\nProject setup completed!")
        print("\nDefault admin credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("\nTo run the project:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Run the application: python app.py")
        print("\nThe application will be available at http://localhost:8080")
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        sys.exit(1) 