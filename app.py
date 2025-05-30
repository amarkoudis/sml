import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Create logger
logger = logging.getLogger(__name__)

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, send_file
from config import app, get_mysql_connection
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, date, timezone
import pymysql
from werkzeug.utils import secure_filename
from flask_mail import Mail
import secrets
from pymysql.cursors import DictCursor
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_cors import CORS
import json
from functools import wraps
import random
import string
import decimal
import math
import os
import csv
from io import StringIO
from models.system_settings import ContributionSettings
import re
import uuid
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import io
import base64
import pythoncom
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)

# Set a strong secret key for the application
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-default-secret-key')  # Change this to a secure random key
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']  # Use the same secret key

# MySQL configurations - update with correct database name
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'V0sp0r0si968!'
app.config['MYSQL_DB'] = 'sml'  # Changed to the correct database name

# Initialize MySQL
mysql = MySQL(app)

# Secret key and other configurations
app.secret_key = '4256ccebf2245cc9e3651352e4540c16a42dade9250b9408e3dff75e40ddaa2d'
app.permanent_session_lifetime = timedelta(hours=5)

# Initialize other extensions (CSRF, CORS, etc.)
csrf = CSRFProtect(app)
CORS(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-app-specific-password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')

mail = Mail(app)

# Add a custom JSON encoder to handle Decimal objects and None values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        elif obj is None:
            return ""
        elif obj == "undefined" or obj == "null":
            return ""
        return super(CustomJSONEncoder, self).default(obj)

# Set the custom JSON encoder for Flask app
app.json_encoder = CustomJSONEncoder

# Template filter to convert None to empty string
@app.template_filter('default_if_none')
def default_if_none(value, default_value=""):
    if value is None:
        return default_value
    return value

# Template filter to safely convert to JSON
@app.template_filter('tojson_safe')
def tojson_safe(obj):
    def preprocess(item):
        if item is None:
            return ""
        elif isinstance(item, dict):
            return {k: preprocess(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [preprocess(i) for i in item]
        elif isinstance(item, decimal.Decimal):
            return float(item)
        elif isinstance(item, (datetime, date)):
            return item.isoformat()
        else:
            return item
    
    processed = preprocess(obj)
    return json.dumps(processed)

# Additional helper function to handle serialization
def safe_serialize(obj):
    """Convert object to JSON-serializable format, handling Null and other problematic values."""
    if obj is None:
        return ""
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # For ID fields, ensure they're converted to integers where possible
            if k.lower().endswith('id') and isinstance(v, str) and v.isdigit():
                try:
                    result[k] = int(v)
                except ValueError:
                    result[k] = v
            # Handle common field names for roles
            elif k in ['role', 'employeerolename'] and v is None:
                result[k] = ""
            elif isinstance(v, (dict, list)):
                result[k] = safe_serialize(v)
            elif isinstance(v, decimal.Decimal):
                result[k] = float(v)
            elif isinstance(v, (datetime, date)):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result
    elif isinstance(obj, list):
        return [safe_serialize(i) for i in obj]
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    else:
        return str(obj) if obj is not None else ""

def generate_reset_token():
    """Generate a secure token for password reset."""
    return secrets.token_urlsafe(32)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_request():
    if request.method == 'POST':
        email = request.form.get('email')
        
        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                # Check if user exists
                cursor.execute('SELECT id, username FROM users WHERE email = %s', (email,))
                user = cursor.fetchone()
                
                if user:
                    # Generate reset token
                    token = generate_reset_token()
                    expiry = datetime.now() + timedelta(hours=1)
                    
                    # Store token in database
                    cursor.execute('''
                        INSERT INTO password_reset_tokens 
                        (user_id, token, expiry) 
                        VALUES (%s, %s, %s)
                    ''', (user['id'], token, expiry))
                    
                    conn.commit()
                    
                    # Send reset email
                    reset_url = url_for(
                        'reset_password_with_token',
                        token=token,
                        _external=True
                    )
                    
                    msg = Message(
                        'Password Reset Request',
                        recipients=[email]
                    )
                    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.

This link will expire in 1 hour.
'''
                    mail.send(msg)
                    
                flash('If an account exists with that email, you will receive password reset instructions.', 'info')
                return redirect(url_for('login'))
                
        except Exception as e:
            flash(f'Error processing request: {str(e)}', 'error')
            
        finally:
            if 'conn' in locals():
                conn.close()
                
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_with_token(token):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Verify token and get user
            cursor.execute('''
                SELECT t.user_id, u.username, u.email 
                FROM password_reset_tokens t
                JOIN users u ON t.user_id = u.id
                WHERE t.token = %s AND t.expiry > NOW() AND t.used = 0
            ''', (token,))
            
            result = cursor.fetchone()
            
            if not result:
                flash('Invalid or expired reset token.', 'error')
                return redirect(url_for('login'))
            
            if request.method == 'POST':
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                
                if password != confirm_password:
                    flash('Passwords do not match.', 'error')
                    return render_template('auth/reset_password.html', token=token)
                
                # Update password and mark token as used
                cursor.execute('''
                    UPDATE users 
                    SET password = %s 
                    WHERE id = %s
                ''', (generate_password_hash(password), result['user_id']))
                
                cursor.execute('''
                    UPDATE password_reset_tokens 
                    SET used = 1 
                    WHERE token = %s
                ''', (token,))
                
                conn.commit()
                
                flash('Your password has been reset successfully.', 'success')
                return redirect(url_for('login'))
            
            return render_template('auth/reset_password.html', token=token)
            
    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'error')
        return redirect(url_for('login'))
        
    finally:
        if 'conn' in locals():
            conn.close()

# Add a custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Helper function to convert Decimal values to float in dictionaries
# while preserving exact string representations
def decimal_to_float(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if isinstance(v, decimal.Decimal):
                # Store the exact string value
                result[f"{k}_exact"] = str(v)
                # Also store the float value
                result[k] = float(v)
            elif isinstance(v, dict) or isinstance(v, list):
                result[k] = decimal_to_float(v)
            else:
                result[k] = v
        return result
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Template context processor to make 'now' available globally
@app.context_processor
def inject_now():
    return {
        'now': datetime.now(timezone.utc),
        'csrf_token': generate_csrf()
    }

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.info("Login route accessed.")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = None
        try:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            if not connection:
                flash('Database connection error', 'error')
                return render_template('login.html')
                
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password'], password):
                    session['logged_in'] = True
                    session['username'] = username
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    return redirect(url_for('home'))
                else:
                    flash('Invalid username or password', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            if connection:
                connection.close()
            
    return render_template('login.html')

@app.route('/home')
@login_required
def home():
    logging.info("Home route accessed.")
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get total counts
            cursor.execute('SELECT COUNT(*) as total FROM event')
            total_events = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM customer')
            total_customers = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM company')
            total_companies = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM employee')
            total_employees = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM invoice')
            total_invoices = cursor.fetchone()['total']
            
            # Get recent events with customer names
            cursor.execute('''
                SELECT 
                    e.EventID,
                    e.EventStart,
                    e.EventName,
                    e.EventStage as Status,
                    c.customername,
                    c.customerphone,
                    c.customeremail
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                ORDER BY e.EventStart DESC
                LIMIT 5
            ''')
            recent_events = cursor.fetchall()
            
            # Get upcoming events
            cursor.execute('''
                SELECT 
                    e.EventID,
                    e.EventStart,
                    e.EventName,
                    e.EventStage as Status,
                    c.customername,
                    c.customerphone,
                    c.customeremail
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                WHERE e.EventStart >= CURDATE()
                ORDER BY e.EventStart ASC
                LIMIT 5
            ''')
            upcoming_events = cursor.fetchall()
            
            # Get financial summary data for past 3 months and upcoming events
            today = datetime.now().date()
            three_months_ago = (today - timedelta(days=90)).strftime('%Y-%m-%d')
            
            # Query for financial summary of past events
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_events,
                    IFNULL(SUM(TotalCost), 0) as total_cost,
                    IFNULL(SUM(TotalSelling), 0) as total_selling,
                    IFNULL(SUM(TotalProfit), 0) as total_profit
                FROM event
                WHERE EventStart >= %s AND EventStart <= NOW()
            ''', (three_months_ago,))
            past_financial = cursor.fetchone()
            
            # Query for financial summary of upcoming events
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_events,
                    IFNULL(SUM(TotalCost), 0) as total_cost,
                    IFNULL(SUM(TotalSelling), 0) as total_selling,
                    IFNULL(SUM(TotalProfit), 0) as total_profit
                FROM event
                WHERE EventStart > NOW()
            ''')
            upcoming_financial = cursor.fetchone()
            
            # Get recent invoices
            cursor.execute('''
                SELECT 
                    i.invoice_id, 
                    i.invoice_number, 
                    i.invoice_date, 
                    i.status, 
                    i.total,
                    c.customername
                FROM invoice i
                LEFT JOIN customer c ON i.customer_id = c.customerid
                ORDER BY i.invoice_date DESC
                LIMIT 5
            ''')
            recent_invoices = cursor.fetchall()
            
            # Calculate invoice statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    IFNULL(SUM(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END), 0) as paid,
                    IFNULL(SUM(CASE WHEN status = 'Draft' THEN 1 ELSE 0 END), 0) as draft,
                    IFNULL(SUM(CASE WHEN status = 'Sent' THEN 1 ELSE 0 END), 0) as sent,
                    IFNULL(SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END), 0) as cancelled,
                    IFNULL(SUM(total), 0) as total_value,
                    IFNULL(SUM(CASE WHEN status = 'Paid' THEN total ELSE 0 END), 0) as paid_value
                FROM invoice
            ''')
            invoice_stats = cursor.fetchone()
            
            # Get events by status
            cursor.execute('''
                SELECT 
                    EventStage as status,
                    COUNT(*) as count
                FROM event
                GROUP BY EventStage
            ''')
            event_status = cursor.fetchall()
            
            # Get employees by role
            cursor.execute('''
                SELECT 
                    er.employeerolename as role,
                    COUNT(e.employeeid) as count
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                GROUP BY er.employeerolename
            ''')
            employee_roles = cursor.fetchall()
            
            # Format the financial data
            if past_financial:
                past_financial['total_cost'] = float(past_financial['total_cost'] or 0)
                past_financial['total_selling'] = float(past_financial['total_selling'] or 0)
                past_financial['total_profit'] = float(past_financial['total_profit'] or 0)
            
            if upcoming_financial:
                upcoming_financial['total_cost'] = float(upcoming_financial['total_cost'] or 0)
                upcoming_financial['total_selling'] = float(upcoming_financial['total_selling'] or 0)
                upcoming_financial['total_profit'] = float(upcoming_financial['total_profit'] or 0)
            
            # Format invoice data
            for invoice in recent_invoices:
                if 'total' in invoice and invoice['total'] is not None:
                    invoice['total'] = float(invoice['total'])
                else:
                    invoice['total'] = 0.0
                
                if 'invoice_date' in invoice and invoice['invoice_date']:
                    if isinstance(invoice['invoice_date'], datetime):
                        invoice['invoice_date_formatted'] = invoice['invoice_date'].strftime('%Y-%m-%d')
                    else:
                        invoice['invoice_date_formatted'] = str(invoice['invoice_date'])
                else:
                    invoice['invoice_date_formatted'] = ''
            
            if invoice_stats:
                invoice_stats['total_value'] = float(invoice_stats['total_value'] or 0)
                invoice_stats['paid_value'] = float(invoice_stats['paid_value'] or 0)
            
            return render_template('home.html',
                                 username=session.get('username'),
                                 total_events=total_events,
                                 total_customers=total_customers,
                                 total_companies=total_companies,
                                 total_employees=total_employees,
                                 total_invoices=total_invoices,
                                 recent_events=recent_events,
                                 upcoming_events=upcoming_events,
                                 past_financial=past_financial,
                                 upcoming_financial=upcoming_financial,
                                 recent_invoices=recent_invoices,
                                 invoice_stats=invoice_stats,
                                 event_status=event_status,
                                 employee_roles=employee_roles)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('home.html',
                             username=session.get('username'),
                             total_events=0,
                             total_customers=0,
                             total_companies=0,
                             total_employees=0,
                             total_invoices=0,
                             recent_events=[],
                             upcoming_events=[],
                             past_financial={
                                 'total_events': 0,
                                 'total_cost': 0,
                                 'total_selling': 0,
                                 'total_profit': 0
                             },
                             upcoming_financial={
                                 'total_events': 0,
                                 'total_cost': 0,
                                 'total_selling': 0,
                                 'total_profit': 0
                             },
                             recent_invoices=[],
                             invoice_stats={
                                 'total': 0,
                                 'paid': 0,
                                 'draft': 0,
                                 'sent': 0,
                                 'cancelled': 0,
                                 'total_value': 0,
                                 'paid_value': 0
                             },
                             event_status=[],
                             employee_roles=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/logout')
def logout():
    logging.info("Logout route accessed.")
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    logging.info("Dashboard route accessed.")
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
        
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute('SELECT COUNT(*) as count FROM users')
        user_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM event')
        event_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM customer')
        customer_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM company')
        company_count = cursor.fetchone()['count']
        
        # Get today's events with the correct column names
        today = datetime.now().date()
        cursor.execute('''
            SELECT 
                e.EventID,
                e.EventName,
                c.customername,
                e.EventStart,
                e.EventStage as status,
                e.notes
            FROM event e 
            LEFT JOIN customer c ON e.Customerid = c.customerid 
            WHERE DATE(e.EventStart) = %s
            ORDER BY e.EventStart ASC
        ''', (today,))
        todays_events = cursor.fetchall()
        
        # Get next week's events
        week_start = today + timedelta(days=1)
        week_end = today + timedelta(days=7)
        cursor.execute('''
            SELECT 
                e.EventID,
                e.EventName,
                c.customername,
                e.EventStart,
                e.EventStage as status,
                e.notes
            FROM event e 
            LEFT JOIN customer c ON e.Customerid = c.customerid 
            WHERE DATE(e.EventStart) BETWEEN %s AND %s
            ORDER BY e.EventStart ASC
        ''', (week_start, week_end))
        upcoming_events = cursor.fetchall()
        
        # Get recent customers
        cursor.execute('''
            SELECT 
                c.customername,
                c.customeremail as email,
                c.customerphone as phone,
                c.contactpersonname
            FROM customer c 
            ORDER BY c.customerid DESC 
            LIMIT 5
        ''')
        recent_customers = cursor.fetchall()
        
        # Get financial summary data for past 3 months and upcoming events
        three_months_ago = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Query for financial summary of past events
        cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                IFNULL(SUM(TotalCost), 0) as total_cost,
                IFNULL(SUM(TotalSelling), 0) as total_selling,
                IFNULL(SUM(TotalProfit), 0) as total_profit
            FROM event
            WHERE EventStart >= %s AND EventStart <= NOW()
        ''', (three_months_ago,))
        past_financial = cursor.fetchone()
        
        # Query for financial summary of upcoming events
        cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                IFNULL(SUM(TotalCost), 0) as total_cost,
                IFNULL(SUM(TotalSelling), 0) as total_selling,
                IFNULL(SUM(TotalProfit), 0) as total_profit
            FROM event
            WHERE EventStart > NOW()
        ''')
        upcoming_financial = cursor.fetchone()
        
        # Get top 5 most profitable upcoming events
        cursor.execute('''
            SELECT 
                e.EventID,
                e.EventName,
                c.customername,
                e.EventStart,
                e.TotalCost,
                e.TotalSelling,
                e.TotalProfit,
                e.EventStage as status
            FROM event e
            LEFT JOIN customer c ON e.Customerid = c.customerid
            WHERE e.EventStart > NOW() AND e.TotalProfit > 0
            ORDER BY e.TotalProfit DESC
            LIMIT 5
        ''')
        top_profitable_events = cursor.fetchall()
        
        return render_template('dashboard.html',
                             username=session.get('username'),
                             user_count=user_count,
                             event_count=event_count,
                             customer_count=customer_count,
                             company_count=company_count,
                             todays_events=todays_events,
                             upcoming_events=upcoming_events,
                             recent_customers=recent_customers,
                             past_financial=past_financial,
                             upcoming_financial=upcoming_financial,
                             top_profitable_events=top_profitable_events)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html',
                             username=session.get('username'),
                             user_count=0,
                             event_count=0,
                             customer_count=0,
                             company_count=0,
                             todays_events=[],
                             upcoming_events=[],
                             recent_customers=[],
                             past_financial={
                                 'total_events': 0,
                                 'total_cost': 0,
                                 'total_selling': 0,
                                 'total_profit': 0
                             },
                             upcoming_financial={
                                 'total_events': 0,
                                 'total_cost': 0,
                                 'total_selling': 0,
                                 'total_profit': 0
                             },
                             top_profitable_events=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/admin/users')
@login_required
def user_list():
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
        
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # First, let's check what columns exist in the users table
            cursor.execute("SHOW COLUMNS FROM users")
            columns = [column['Field'] for column in cursor.fetchall()]
            
            # Build the SELECT query based on existing columns
            select_columns = ['id', 'username', 'role']  # These are the basic columns we know exist
            
            if 'email' in columns:
                select_columns.append('email')
            if 'status' in columns:
                select_columns.append('status')
            if 'created_at' in columns:
                select_columns.append('created_at')
            if 'last_login' in columns:
                select_columns.append('last_login')
            
            query = f"SELECT {', '.join(select_columns)} FROM users ORDER BY id DESC"
            cursor.execute(query)
            users = cursor.fetchall()
            
            # Add default values for missing columns
            for user in users:
                if 'email' not in user:
                    user['email'] = None
                if 'status' not in user:
                    user['status'] = 'active'
                if 'created_at' not in user:
                    user['created_at'] = None
                if 'last_login' not in user:
                    user['last_login'] = None
            
            return render_template('admin/users.html',
                                 username=session.get('username'),
                                 users=users)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('admin/users.html',
                             username=session.get('username'),
                             users=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/user/add', methods=['GET', 'POST'])
def user_add():
    if 'logged_in' in session and session['role'] == 'admin':
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            full_name = request.form['full_name']
            role = request.form['role']
            
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            if conn:
                try:
                    cursor = conn.cursor()
                    hashed_password = generate_password_hash(password)
                    cursor.execute('''
                        INSERT INTO users (username, password, email, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (username, hashed_password, email, full_name, role))
                    conn.commit()
                    flash('User added successfully!', 'success')
                    return redirect(url_for('user_list'))
                except Exception as e:
                    flash(f'Error: {str(e)}', 'error')
                finally:
                    cursor.close()
                    conn.close()
        return render_template('admin/user_add.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/user/edit/<int:id>', methods=['GET', 'POST'])
def user_edit(id):
    print('SESSION:', dict(session))
    if 'logged_in' in session and session['role'] == 'admin':
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = None
        if conn:
            try:
                cursor = conn.cursor()
                if request.method == 'POST':
                    email = request.form['email']
                    full_name = request.form['full_name']
                    role = request.form['role']
                    is_active = 1 if 'is_active' in request.form else 0

                    cursor.execute('''
                        UPDATE users 
                        SET email = %s, full_name = %s, role = %s, is_active = %s
                        WHERE id = %s
                    ''', (email, full_name, role, is_active, id))

                    if 'password' in request.form and request.form['password']:
                        hashed_password = generate_password_hash(request.form['password'])
                        cursor.execute('UPDATE users SET password = %s WHERE id = %s', 
                                     (hashed_password, id))

                    conn.commit()
                    flash('User updated successfully!', 'success')
                    return redirect(url_for('user_list'))

                cursor.execute('SELECT * FROM users WHERE id = %s', (id,))
                user = cursor.fetchone()
                if user:
                    return render_template('admin/user_edit.html', 
                                         username=session['username'],
                                         user=user)
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
            finally:
                if cursor:
                    cursor.close()
                conn.close()
    return redirect(url_for('login'))

@app.route('/user/delete/<int:id>')
def user_delete(id):
    if 'logged_in' in session and session['role'] == 'admin':
        if id != session['id']:  # Prevent self-deletion
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM users WHERE id = %s', (id,))
                    conn.commit()
                    flash('User deleted successfully!', 'success')
                except Exception as e:
                    flash(f'Error: {str(e)}', 'error')
                finally:
                    cursor.close()
                    conn.close()
        else:
            flash('Cannot delete your own account!', 'error')
    return redirect(url_for('user_list'))

@app.route('/user/reset_password/<int:id>', methods=['GET', 'POST'])
def reset_password(id):
    if 'logged_in' in session and session['role'] == 'admin':
        if request.method == 'POST':
            new_password = request.form['password']
            if not new_password:
                flash('Password cannot be empty.', 'error')
                return redirect(request.url)
            hashed_password = generate_password_hash(new_password)
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, id))
                conn.commit()
                flash('Password reset successfully!', 'success')
                return redirect(url_for('user_list'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
            finally:
                cursor.close()
                conn.close()
        return render_template('admin/reset_password.html', user_id=id)
    return redirect(url_for('login'))

@app.route('/event_list')
@login_required
def event_list():
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
        
        cursor = conn.cursor()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        sort_by = request.args.get('sort', 'EventStart')
        sort_dir = request.args.get('dir', 'DESC')
        customer_id = request.args.get('customer_id', type=int)
        
        # Validate and sanitize sort parameters
        allowed_columns = ['EventID', 'EventName', 'customername', 'EventLocation', 
                           'EventStart', 'EventStage', 'totalprofit']
        if sort_by not in allowed_columns:
            sort_by = 'EventStart'
        
        if sort_dir not in ['ASC', 'DESC']:
            sort_dir = 'DESC'
        
        # Build the query with search functionality
        query = '''
            SELECT 
                e.EventID,
                e.Customerid,
                e.EventName,
                e.EventLocation,
                e.EventStart,
                e.EventEnd,
                e.notes,
                e.WaitersNeeded,
                e.BartendersNeeded,
                e.MaleEmployees,
                e.FemaleEmployees,
                e.TotalEmployees,
                e.EventDurationHours,
                e.EventTotalHours,
                e.EventPerHourcost,
                e.EventPerHourselling,
                e.EventStage,
                e.totalhours,
                e.totalcost,
                e.totalselling,
                e.totalprofit,
                e.totalshifthours,
                c.customername
            FROM event e 
            LEFT JOIN customer c ON e.Customerid = c.customerid 
        '''
        
        params = []
        where_clauses = []
        # Add search condition if search term provided
        if search:
            where_clauses.append('(' + ' OR '.join([
                'e.EventName LIKE %s',
                'c.customername LIKE %s',
                'e.EventLocation LIKE %s',
                'e.notes LIKE %s',
                'e.EventStage LIKE %s']) + ')')
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term, search_term, search_term])
        # Add customer filter if provided
        if customer_id:
            where_clauses.append('e.Customerid = %s')
            params.append(customer_id)
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
        
        # Count total records for pagination
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as t"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        
        # Add sorting and pagination
        query += f' ORDER BY {sort_by} {sort_dir}'
        query += ' LIMIT %s OFFSET %s'
        
        # Calculate offset
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        # Execute final query
        cursor.execute(query, params)
        events_raw = cursor.fetchall()
        
        # Convert Decimal values to float and ensure consistent handling of profit
        events = []
        for event in events_raw:
            event_dict = {}
            for key, value in event.items():
                if isinstance(value, decimal.Decimal):
                    # For financial values, ensure consistent rounding to 2 decimal places
                    if key in ['totalcost', 'totalselling', 'totalprofit', 'EventPerHourcost', 'EventPerHourselling']:
                        event_dict[key] = round(float(value), 2)
                    else:
                        event_dict[key] = float(value)
                elif key in ['EventStart', 'EventEnd'] and value:
                    # Convert string dates to datetime objects
                    if isinstance(value, str):
                        try:
                            event_dict[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                event_dict[key] = datetime.strptime(value, '%Y-%m-%d %H:%M')
                            except ValueError:
                                event_dict[key] = None
                    else:
                        event_dict[key] = value
                else:
                    event_dict[key] = value
            
            # Recalculate totalprofit to ensure it's consistent
            if 'totalcost' in event_dict and 'totalselling' in event_dict:
                event_dict['totalprofit'] = round(event_dict['totalselling'] - event_dict['totalcost'], 2)
                
            events.append(event_dict)
        
        # Calculate page count
        total_pages = (total_count + per_page - 1) // per_page
        
        # Get customers for filtering
        cursor.execute('SELECT customerid, customername FROM customer ORDER BY customername')
        customers = cursor.fetchall()
        
        return render_template(
            'events/list.html', 
            events=events,
            customers=customers,
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
            per_page=per_page,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
            selected_customer_id=customer_id
        )
        
    except Exception as e:
        flash(f'Error loading events: {str(e)}', 'error')
        return render_template('events/list.html', 
                             events=[], 
                             current_page=1,
                             total_pages=1,
                             total_count=0,
                             per_page=10,
                             search='',
                             sort_by='EventStart',
                             sort_dir='DESC')
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_event/<int:event_id>')
@login_required
def view_event(event_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT 
                    e.*, 
                    c.customername, 
                    c.customerphone, 
                    c.customeremail,
                    CAST(e.totalhours AS CHAR) as totalhours_exact,
                    CAST(e.totalcost AS CHAR) as totalcost_exact,
                    CAST(e.totalselling AS CHAR) as totalselling_exact
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                WHERE e.EventID = %s
            ''', (event_id,))
            event = cursor.fetchone()
            
            if not event:
                flash('Event not found.', 'error')
                return redirect(url_for('event_list'))
            
            # Ensure consistent handling of financial values
            event_dict = {}
            for key, value in event.items():
                if isinstance(value, decimal.Decimal):
                    # For financial values, ensure consistent rounding to 2 decimal places
                    if key in ['totalcost', 'totalselling', 'totalprofit', 'EventPerHourcost', 'EventPerHourselling']:
                        event_dict[key] = round(float(value), 2)
                    else:
                        event_dict[key] = float(value)
                else:
                    event_dict[key] = value
            
            # Recalculate totalprofit to ensure it's consistent with the list view
            if 'totalcost' in event_dict and 'totalselling' in event_dict:
                event_dict['totalprofit'] = round(event_dict['totalselling'] - event_dict['totalcost'], 2)
                
            # Make sure we have the original string values for proper display
            if 'totalhours_exact' in event and event['totalhours_exact']:
                event_dict['totalhours'] = event['totalhours_exact']
            else:
                # Ensure totalhours is a float
                event_dict['totalhours'] = float(event['totalhours']) if event['totalhours'] else 0
                
            if 'totalcost_exact' in event and event['totalcost_exact']:
                event_dict['totalcost'] = float(event['totalcost_exact'])
            else:
                # Ensure totalcost is a float
                event_dict['totalcost'] = float(event['totalcost']) if event['totalcost'] else 0
                
            if 'totalselling_exact' in event and event['totalselling_exact']:
                event_dict['totalselling'] = float(event['totalselling_exact'])
            else:
                # Ensure totalselling is a float
                event_dict['totalselling'] = float(event['totalselling']) if event['totalselling'] else 0
                
            return render_template('events/view.html',
                                 event=event_dict,
                                 username=session.get('username'))
    except Exception as e:
        flash(f'Error viewing event: {str(e)}', 'error')
        return redirect(url_for('event_list'))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # First delete associated records from employee_shifts and shifts tables
            cursor.execute("""
                DELETE FROM employee_shifts 
                WHERE shiftid IN (
                    SELECT shiftid FROM shifts WHERE eventid = %s
                )
            """, (event_id,))
            
            # Delete shifts
            cursor.execute('DELETE FROM shifts WHERE eventid = %s', (event_id,))
            
            # Delete the event
            cursor.execute('DELETE FROM event WHERE EventID = %s', (event_id,))
            conn.commit()
            flash('Event deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting event: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('event_list'))

@app.route('/delete_multiple_events', methods=['POST'])
@login_required
def delete_multiple_events():
    """Handle deletion of multiple events at once."""
    if request.method == 'POST':
        try:
            # Get the list of event IDs to delete
            event_ids_json = request.form.get('event_ids', '[]')
            event_ids = json.loads(event_ids_json)
            
            if not event_ids:
                flash('No events selected for deletion.', 'warning')
                return redirect(url_for('event_list'))
            
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with conn.cursor() as cursor:
                    # Format the IDs for the SQL IN clause
                    id_placeholder = ','.join(['%s'] * len(event_ids))
                    
                    # First delete associated records from employee_shifts and shifts tables
                    cursor.execute(f"""
                        DELETE FROM employee_shifts 
                        WHERE shiftid IN (
                            SELECT shiftid FROM shifts WHERE eventid IN ({id_placeholder})
                        )
                    """, event_ids)
                    
                    # Delete shifts associated with these events
                    cursor.execute(f"""
                        DELETE FROM shifts 
                        WHERE eventid IN ({id_placeholder})
                    """, event_ids)
                    
                    # Finally delete the events
                    cursor.execute(f"""
                        DELETE FROM event 
                        WHERE EventID IN ({id_placeholder})
                    """, event_ids)
                    
                    # Get number of deleted rows
                    deleted_count = cursor.rowcount
                    
                    conn.commit()
                    flash(f'Successfully deleted {deleted_count} events.', 'success')
                    
            except Exception as e:
                conn.rollback()
                flash(f'Error deleting events: {str(e)}', 'danger')
            
            finally:
                conn.close()
                
        except Exception as e:
            flash(f'Error processing request: {str(e)}', 'danger')
        
    return redirect(url_for('event_list'))

@app.before_request
def before_request():
    if 'logged_in' in session:
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=5)

# Add a function to check if user is logged in
def is_logged_in():
    return session.get('logged_in', False)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
        
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get total counts
            cursor.execute('SELECT COUNT(*) as total FROM users')
            total_users = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM event')
            total_events = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM customer')
            total_customers = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM company')
            total_companies = cursor.fetchone()['total']
            
            # Get recent users
            cursor.execute('''
                SELECT id, username, role, last_login 
                FROM users 
                ORDER BY id DESC 
                LIMIT 5
            ''')
            recent_users = cursor.fetchall()
            
            # Get recent events
            cursor.execute('''
                SELECT 
                    e.EventID,
                    e.EventStart,
                    e.EventName,
                    e.EventStage as Status,
                    c.customername
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                ORDER BY e.EventStart DESC
                LIMIT 5
            ''')
            recent_events = cursor.fetchall()
            
            return render_template('admin/dashboard.html',
                                 username=session.get('username'),
                                 total_users=total_users,
                                 total_events=total_events,
                                 total_customers=total_customers,
                                 total_companies=total_companies,
                                 recent_users=recent_users,
                                 recent_events=recent_events)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('admin/dashboard.html',
                             username=session.get('username'),
                             total_users=0,
                             total_events=0,
                             total_customers=0,
                             total_companies=0,
                             recent_users=[],
                             recent_events=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role']
            
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                # Check if username already exists
                cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
                if cursor.fetchone():
                    flash('Username already exists!', 'error')
                    return redirect(url_for('user_list'))
                
                # Insert new user without the status column
                cursor.execute('''
                    INSERT INTO users (username, email, password, role, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                ''', (username, email, generate_password_hash(password), role))
                
                conn.commit()
                flash('User created successfully!', 'success')
                
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'error')
        finally:
            conn.close()
            
        return redirect(url_for('user_list'))
        
    return redirect(url_for('user_list'))

@app.route('/customer_list')
@login_required
def customer_list():
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        sort_by = request.args.get('sort', 'customername')
        sort_dir = request.args.get('dir', 'ASC')
        
        # Validate sort parameters
        allowed_columns = ['customername', 'contactpersonname', 'customerphone', 'customeremail']
        if sort_by not in allowed_columns:
            sort_by = 'customername'
        
        if sort_dir not in ['ASC', 'DESC']:
            sort_dir = 'ASC'
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Count total customers for pagination (with search filter if applicable)
            count_query = 'SELECT COUNT(*) as total FROM customer'
            count_params = []
            
            if search:
                count_query += ''' WHERE 
                    customername LIKE %s OR 
                    contactpersonname LIKE %s OR 
                    customerphone LIKE %s OR 
                    customeremail LIKE %s'''
                search_term = f'%{search}%'
                count_params = [search_term, search_term, search_term, search_term]
            
            cursor.execute(count_query, count_params if count_params else None)
            total_count = cursor.fetchone()['total']
            
            # Calculate total pages
            total_pages = math.ceil(total_count / per_page)
            
            # Prepare main query with search, sort and pagination
            main_query = '''
                SELECT c.*, b.bankname 
                FROM customer c
                LEFT JOIN banks b ON c.bankid = b.bankid
            '''
            
            params = []
            if search:
                main_query += ''' WHERE 
                    c.customername LIKE %s OR 
                    c.contactpersonname LIKE %s OR 
                    c.customerphone LIKE %s OR 
                    c.customeremail LIKE %s'''
                params = [search_term, search_term, search_term, search_term]
            
            main_query += f' ORDER BY c.{sort_by} {sort_dir}'
            main_query += ' LIMIT %s OFFSET %s'
            
            offset = (page - 1) * per_page
            params.extend([per_page, offset])
            
            cursor.execute(main_query, params)
            customers = cursor.fetchall()
            
            # Get banks for dropdown
            cursor.execute('SELECT bankid, bankname FROM banks ORDER BY bankname')
            banks = cursor.fetchall()
            
            return render_template('customers/list.html',
                                 username=session.get('username'),
                                 customers=customers,
                                 banks=banks,
                                 current_page=page,
                                 total_pages=total_pages,
                                 total_count=total_count,
                                 per_page=per_page,
                                 search=search,
                                 sort_by=sort_by,
                                 sort_dir=sort_dir)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('customers/list.html',
                             username=session.get('username'),
                             customers=[],
                             banks=[],
                             current_page=1,
                             total_pages=1,
                             total_count=0,
                             per_page=10,
                             search='',
                             sort_by='customername',
                             sort_dir='ASC')
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/customers/add', methods=['GET'])
@login_required
def create_customer_unified():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
        
        with conn.cursor() as cursor:
            # Get banks for dropdown
            cursor.execute('SELECT bankid, bankname FROM banks ORDER BY bankname')
            banks = cursor.fetchall()
            
            return render_template(
                'customers/unified/customer_form.html',
                is_edit_mode=False,
                banks=banks
            )
    except Exception as e:
        flash(f'Error loading form: {str(e)}', 'error')
        return redirect(url_for('customer_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/customers/<int:customer_id>/edit', methods=['GET'])
@login_required
def edit_customer_unified(customer_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
        
        with conn.cursor() as cursor:
            # Get customer details
            cursor.execute('SELECT * FROM customer WHERE customerid = %s', (customer_id,))
            customer = cursor.fetchone()
            
            if not customer:
                flash('Customer not found', 'error')
                return redirect(url_for('customer_list'))
            
            # Get banks for dropdown
            cursor.execute('SELECT bankid, bankname FROM banks ORDER BY bankname')
            banks = cursor.fetchall()
            
            return render_template(
                'customers/unified/customer_form.html',
                is_edit_mode=True,
                customer=customer,
                banks=banks
            )
    except Exception as e:
        flash(f'Error loading customer: {str(e)}', 'error')
        return redirect(url_for('customer_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/customers/create', methods=['POST'])
@login_required
def create_customer():
    try:
        customername = request.form['customername']
        customeraddress = request.form['customeraddress']
        customerphone = request.form['customerphone']
        customeremail = request.form['customeremail']
        contactpersonname = request.form['contactpersonname']
        bankid = request.form['bankid'] if request.form['bankid'] else None
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO customer (customername, customeraddress, customerphone, 
                                    customeremail, contactpersonname, bankid)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (customername, customeraddress, customerphone, 
                  customeremail, contactpersonname, bankid))
            
            conn.commit()
            flash('Customer created successfully!', 'success')
            
    except Exception as e:
        flash(f'Error creating customer: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('customer_list'))

@app.route('/customers/<int:customer_id>/edit', methods=['POST'])
@login_required
def edit_customer(customer_id):
    try:
        customername = request.form['customername']
        customeraddress = request.form['customeraddress']
        customerphone = request.form['customerphone']
        customeremail = request.form['customeremail']
        contactpersonname = request.form['contactpersonname']
        bankid = request.form['bankid'] if request.form['bankid'] else None
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('''
                UPDATE customer 
                SET customername = %s, customeraddress = %s, customerphone = %s,
                    customeremail = %s, contactpersonname = %s, bankid = %s
                WHERE customerid = %s
            ''', (customername, customeraddress, customerphone, 
                  customeremail, contactpersonname, bankid, customer_id))
            
            conn.commit()
            flash('Customer updated successfully!', 'success')
            
    except Exception as e:
        flash(f'Error updating customer: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('customer_list'))

@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM customer WHERE customerid = %s', (customer_id,))
            conn.commit()
            flash('Customer deleted successfully!', 'success')
            
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('customer_list'))

@app.route('/delete_multiple_customers', methods=['POST'])
@login_required
def delete_multiple_customers():
    """Handle deletion of multiple customers at once."""
    if request.method == 'POST':
        try:
            # Get the list of customer IDs to delete
            customer_ids = request.form.getlist('customer_ids[]')
            if not customer_ids:
                flash('No customers selected for deletion.', 'warning')
                return redirect(url_for('customer_list'))
            
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with conn.cursor() as cursor:
                    # Check if any of these customers have associated events
                    id_placeholder = ','.join(['%s'] * len(customer_ids))
                    cursor.execute(f'''
                        SELECT c.customerid, c.customername, COUNT(e.EventID) as event_count
                        FROM customer c
                        LEFT JOIN event e ON c.customerid = e.Customerid
                        WHERE c.customerid IN ({id_placeholder})
                        GROUP BY c.customerid, c.customername
                        HAVING COUNT(e.EventID) > 0
                    ''', customer_ids)
                    
                    customers_with_events = cursor.fetchall()
                    if customers_with_events:
                        # Some customers have events, show error message
                        customer_names = ', '.join([c['customername'] for c in customers_with_events])
                        flash(f'Cannot delete customers with associated events: {customer_names}', 'error')
                        return redirect(url_for('customer_list'))
                    
                    # Delete customers
                    cursor.execute(f'''
                        DELETE FROM customer
                        WHERE customerid IN ({id_placeholder})
                    ''', customer_ids)
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    flash(f'Successfully deleted {deleted_count} customers.', 'success')
                
            except Exception as e:
                conn.rollback()
                flash(f'Error deleting customers: {str(e)}', 'error')
            finally:
                conn.close()
        except Exception as e:
            flash(f'Error processing request: {str(e)}', 'error')
    
    return redirect(url_for('customer_list'))

@app.route('/api/customers/<int:customer_id>')
@login_required
def get_customer(customer_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM customer WHERE customerid = %s', (customer_id,))
            customer = cursor.fetchone()
            
            if customer:
                return jsonify(customer)
            
            return jsonify({'error': 'Customer not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/bank_list')
@login_required
def bank_list():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT bankid, bankname, biccode 
                FROM banks 
                ORDER BY bankname
            ''')
            banks = cursor.fetchall()
            
            return render_template('banks/list.html',
                                 banks=banks,
                                 username=session.get('username'),
                                 # Add pagination variables to avoid undefined errors
                                 current_page=1,
                                 per_page=len(banks),
                                 total_count=len(banks),
                                 total_pages=1,
                                 search='',
                                 sort_by='bankname',
                                 sort_dir='ASC')
    except Exception as e:
        flash(f'Error loading banks: {str(e)}', 'error')
        return render_template('banks/list.html',
                             banks=[],
                             username=session.get('username'),
                             # Add pagination variables to avoid undefined errors
                             current_page=1,
                             per_page=10,
                             total_count=0,
                             total_pages=1,
                             search='',
                             sort_by='bankname',
                             sort_dir='ASC')
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/create_bank', methods=['POST'])
@login_required
def create_bank():
    try:
        bankname = request.form.get('bankname')
        biccode = request.form.get('biccode')
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
        
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO banks (bankname, biccode) VALUES (%s, %s)', 
                         (bankname, biccode))
            conn.commit()
            
        flash('Bank added successfully!', 'success')
        
    except Exception as e:
        flash(f'Error adding bank: {str(e)}', 'error')
        
    finally:
        if 'conn' in locals():
            conn.close()
            
    return redirect(url_for('bank_list'))

@app.route('/banks/<int:bank_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bank(bank_id):
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
        
        cursor = conn.cursor()
        
        if request.method == 'POST':
            # Handle the form submission
            bankname = request.form.get('bankname')
            biccode = request.form.get('biccode')
            
            cursor.execute('''
                UPDATE banks 
                SET bankname = %s, biccode = %s 
                WHERE bankid = %s
            ''', (bankname, biccode, bank_id))
            
            conn.commit()
            flash('Bank updated successfully!', 'success')
            return redirect(url_for('bank_list'))
            
        else:
            # GET request - show edit form
            cursor.execute('SELECT * FROM banks WHERE bankid = %s', (bank_id,))
            bank = cursor.fetchone()
            
            if bank is None:
                flash('Bank not found.', 'error')
                return redirect(url_for('bank_list'))
                
            return render_template('banks/edit.html', bank=bank)
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('bank_list'))
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@app.route('/banks/<int:bank_id>/delete', methods=['POST'])
@login_required
def delete_bank(bank_id):
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
        
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if bank has associated customers
            cursor.execute('SELECT COUNT(*) as count FROM customer WHERE bankid = %s', (bank_id,))
            if cursor.fetchone()['count'] > 0:
                flash('Cannot delete bank: It has associated customers', 'error')
                return redirect(url_for('bank_list'))
                
            cursor.execute('DELETE FROM banks WHERE bankid = %s', (bank_id,))
            conn.commit()
            flash('Bank deleted successfully!', 'success')
            
    except Exception as e:
        flash(f'Error deleting bank: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('bank_list'))

@app.route('/delete_multiple_banks', methods=['POST'])
@login_required
def delete_multiple_banks():
    """Handle deletion of multiple banks at once."""
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        try:
            # Get the list of bank IDs to delete
            bank_ids = request.form.getlist('bank_ids[]')
            if not bank_ids:
                flash('No banks selected for deletion.', 'warning')
                return redirect(url_for('bank_list'))
            
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with conn.cursor() as cursor:
                    # Check if any banks have associated customers
                    id_placeholder = ','.join(['%s'] * len(bank_ids))
                    cursor.execute(f'''
                        SELECT b.bankid, b.bankname, COUNT(c.customerid) as customer_count
                        FROM banks b
                        LEFT JOIN customer c ON b.bankid = c.bankid
                        WHERE b.bankid IN ({id_placeholder})
                        GROUP BY b.bankid, b.bankname
                        HAVING COUNT(c.customerid) > 0
                    ''', bank_ids)
                    
                    banks_with_customers = cursor.fetchall()
                    if banks_with_customers:
                        # Some banks have customers, show error message
                        bank_names = ', '.join([b['bankname'] for b in banks_with_customers])
                        flash(f'Cannot delete banks with associated customers: {bank_names}', 'error')
                        return redirect(url_for('bank_list'))
                    
                    # Delete banks without associated customers
                    cursor.execute(f'''
                        DELETE FROM banks
                        WHERE bankid IN ({id_placeholder})
                    ''', bank_ids)
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    flash(f'Successfully deleted {deleted_count} banks.', 'success')
                
            except Exception as e:
                conn.rollback()
                flash(f'Error deleting banks: {str(e)}', 'error')
            finally:
                conn.close()
        except Exception as e:
            flash(f'Error processing request: {str(e)}', 'error')
    
    return redirect(url_for('bank_list'))

@app.route('/api/banks/<int:bank_id>')
@login_required
def get_bank(bank_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
        
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM banks WHERE bankid = %s', (bank_id,))
            bank = cursor.fetchone()
            
            if bank:
                return jsonify(bank)
            
            return jsonify({'error': 'Bank not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/companies')
@login_required
def company_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            # Get total count
            cursor.execute('SELECT COUNT(*) as total FROM company')
            total_count = cursor.fetchone()['total']
            
            # Check if there are multiple companies and show a warning
            if total_count > 1:
                flash('Warning: Multiple company records detected. The system is designed to work with only one company. Please keep only one record.', 'warning')
                
            total_pages = (total_count + per_page - 1) // per_page
            # Join with banks table to get bank information, paginated
            cursor.execute('''
                SELECT 
                    c.companyid,
                    c.companyname,
                    c.companyaddress,
                    c.companyphone,
                    c.companyemail,
                    c.companyweb,
                    c.vatno,
                    c.companydebitaccount,
                    c.companyiban,
                    c.beneficiary,
                    c.paymentpolicy,
                    c.transactiontype,
                    b.bankname,
                    b.biccode
                FROM company c
                LEFT JOIN banks b ON c.bankid = b.bankid
                ORDER BY c.companyname
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
            companies = cursor.fetchall()
            print('Companies:', companies)
            return render_template('companies/list.html',
                                 companies=companies,
                                 username=session.get('username'),
                                 current_page=page,
                                 total_pages=total_pages,
                                 total_count=total_count,
                                 per_page=per_page)
    except Exception as e:
        flash(f'Error loading companies: {str(e)}', 'error')
        return render_template('companies/list.html',
                             companies=[],
                             username=session.get('username'),
                             current_page=1,
                             total_pages=1,
                             total_count=0,
                             per_page=10)
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/create_company', methods=['POST'])
@login_required
def create_company():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
        
        with conn.cursor() as cursor:
            # Check if a company already exists
            cursor.execute('SELECT COUNT(*) as count FROM company')
            company_count = cursor.fetchone()['count']
            
            if company_count >= 1:
                flash('Cannot create a new company: Only one company is allowed in the system.', 'error')
                return redirect(url_for('company_list'))
            
            # Extract form data
            companyname = request.form.get('companyname')
            companyaddress = request.form.get('companyaddress')
            companyphone = request.form.get('companyphone')
            companyemail = request.form.get('companyemail')
            companyweb = request.form.get('companyweb')
            vatno = request.form.get('vatno')
            companydebitaccount = request.form.get('companydebitaccount')
            companyiban = request.form.get('companyiban')
            beneficiary = request.form.get('beneficiary')
            paymentpolicy = request.form.get('paymentpolicy')
            transactiontype = request.form.get('transactiontype')
            bankid = request.form.get('bankid') if request.form.get('bankid') else None
            
            # Handle logo upload
            company_logo = None
            if 'company_logo' in request.files:
                logo_file = request.files['company_logo']
                if logo_file and logo_file.filename:
                    # Securely save the filename
                    logo_filename = secure_filename(logo_file.filename)
                    # Add timestamp to filename to avoid conflicts
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    logo_filename = f"{timestamp}_{logo_filename}"
                    # Create directory if it doesn't exist
                    os.makedirs('static/uploads/logos', exist_ok=True)
                    # Save the file
                    logo_file.save(os.path.join('static/uploads/logos', logo_filename))
                    company_logo = logo_filename
            
            cursor.execute('''
                INSERT INTO company (
                    companyname, 
                    companyaddress, 
                    companyphone, 
                    companyemail, 
                    companyweb,
                    vatno,
                    companydebitaccount, 
                    companyiban,
                    beneficiary,
                    paymentpolicy,
                    transactiontype, 
                    bankid,
                    company_logo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                companyname, 
                companyaddress, 
                companyphone, 
                companyemail, 
                companyweb,
                vatno,
                companydebitaccount, 
                companyiban,
                beneficiary,
                paymentpolicy,
                transactiontype, 
                bankid,
                company_logo
            ))
            conn.commit()
            
        flash('Company added successfully!', 'success')
        
    except Exception as e:
        flash(f'Error adding company: {str(e)}', 'error')
        
    finally:
        if 'conn' in locals():
            conn.close()
            
    return redirect(url_for('company_list'))

@app.route('/companies/<int:company_id>/edit', methods=['GET'])
@login_required
def edit_company_page(company_id):
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM company WHERE companyid = %s', (company_id,))
        company = cursor.fetchone()
        cursor.execute('SELECT bankid, bankname FROM banks ORDER BY bankname')
        banks = cursor.fetchall()
    conn.close()
    if not company:
        flash('Company not found.', 'error')
        return redirect(url_for('company_list'))
    return render_template('companies/unified/company_form.html', is_edit_mode=True, company=company, banks=banks)

@app.route('/companies/<int:company_id>/edit', methods=['POST'])
@login_required
def edit_company(company_id):
    try:
        # Extract form data
        companyname = request.form.get('companyname')
        companyaddress = request.form.get('companyaddress')
        companyphone = request.form.get('companyphone')
        companyemail = request.form.get('companyemail')
        companyweb = request.form.get('companyweb')
        vatno = request.form.get('vatno')
        companydebitaccount = request.form.get('companydebitaccount')
        companyiban = request.form.get('companyiban')
        beneficiary = request.form.get('beneficiary')
        paymentpolicy = request.form.get('paymentpolicy')
        transactiontype = request.form.get('transactiontype')
        bankid = request.form.get('bankid') if request.form.get('bankid') else None
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get current company logo
            cursor.execute('SELECT company_logo FROM company WHERE companyid = %s', (company_id,))
            current_company = cursor.fetchone()
            current_logo = current_company.get('company_logo') if current_company else None
            
            # Handle logo upload
            company_logo = current_logo
            if 'company_logo' in request.files:
                logo_file = request.files['company_logo']
                if logo_file and logo_file.filename:
                    # Securely save the filename
                    logo_filename = secure_filename(logo_file.filename)
                    # Add timestamp to filename to avoid conflicts
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    logo_filename = f"{timestamp}_{logo_filename}"
                    # Create directory if it doesn't exist
                    os.makedirs('static/uploads/logos', exist_ok=True)
                    # Save the file
                    logo_file.save(os.path.join('static/uploads/logos', logo_filename))
                    company_logo = logo_filename
                    
                    # Remove old logo if exists
                    if current_logo and os.path.exists(os.path.join('static/uploads/logos', current_logo)):
                        try:
                            os.remove(os.path.join('static/uploads/logos', current_logo))
                        except:
                            # Don't fail if old file can't be removed
                            pass
            
            cursor.execute('''
                UPDATE company 
                SET companyname = %s, 
                    companyaddress = %s, 
                    companyphone = %s,
                    companyemail = %s, 
                    companyweb = %s,
                    vatno = %s,
                    companydebitaccount = %s, 
                    companyiban = %s,
                    beneficiary = %s,
                    paymentpolicy = %s,
                    transactiontype = %s, 
                    bankid = %s,
                    company_logo = %s
                WHERE companyid = %s
            ''', (
                companyname, 
                companyaddress, 
                companyphone, 
                companyemail, 
                companyweb,
                vatno,
                companydebitaccount, 
                companyiban,
                beneficiary,
                paymentpolicy,
                transactiontype, 
                bankid,
                company_logo,
                company_id
            ))
            
            conn.commit()
            flash('Company updated successfully!', 'success')
            
    except Exception as e:
        flash(f'Error updating company: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
        
    return redirect(url_for('company_list'))

@app.route('/companies/<int:company_id>/delete', methods=['POST'])
@login_required
def delete_company(company_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if company has associated employees
            cursor.execute('SELECT COUNT(*) as count FROM employee WHERE companyid = %s', (company_id,))
            employee_count = cursor.fetchone()['count']
            
            if employee_count > 0:
                flash(f'Cannot delete company: There are {employee_count} employees associated with this company. Please reassign or delete these employees first.', 'error')
                return redirect(url_for('company_list'))
                
            # If no employees, proceed with deletion
            cursor.execute('DELETE FROM company WHERE companyid = %s', (company_id,))
            conn.commit()
            flash('Company deleted successfully!', 'success')
            
    except Exception as e:
        flash(f'Error deleting company: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('company_list'))

@app.route('/api/companies/<int:company_id>')
@login_required
def get_company(company_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM company WHERE companyid = %s', (company_id,))
            company = cursor.fetchone()
            
            if company:
                return jsonify(company)
            
            return jsonify({'error': 'Company not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/employee_list')
@login_required
def employee_list():
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'employeename')
    sort_dir = request.args.get('dir', 'ASC')
    
    # Validate sort parameters
    allowed_columns = ['employeename', 'employeerolename']
    if sort_by not in allowed_columns:
        sort_by = 'employeename'
    if sort_dir not in ['ASC', 'DESC']:
        sort_dir = 'ASC'
    
    # Fix sort_by to use the actual column name
    sort_column = sort_by
    
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get total count first
            count_sql = """
                SELECT COUNT(*) as count
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE 1=1
            """
            
            # Build the main query
            sql = """
                SELECT 
                    e.employeeid,
                    COALESCE(e.employeename, '') as employeename,
                    COALESCE(e.gender, '') as gender,
                    COALESCE(e.email, '') as email,
                    COALESCE(e.tel, '') as phone,
                    COALESCE(er.employeerolename, '') as employeerolename
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE 1=1
            """
            
            params = []
            
            # Add search condition if provided
            if search:
                search_param = f"%{search}%"
                count_sql += """ AND (
                    e.employeename LIKE %s OR
                    e.email LIKE %s OR
                    e.tel LIKE %s OR
                    er.employeerolename LIKE %s
                )"""
                sql += """ AND (
                    e.employeename LIKE %s OR
                    e.email LIKE %s OR
                    e.tel LIKE %s OR
                    er.employeerolename LIKE %s
                )"""
                params.extend([search_param, search_param, search_param, search_param])
            
            # Get total count
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['count']
            total_pages = math.ceil(total_count / per_page)
            
            # Add sorting
            sql += f" ORDER BY {sort_column} {sort_dir}"
            
            # Add pagination
            sql += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            
            cursor.execute(sql, params)
            employees = cursor.fetchall()
            
            # Get employee roles for the dropdown
            cursor.execute("SELECT employeeroleid, employeerolename FROM employeerole ORDER BY employeerolename")
            roles = cursor.fetchall()
            
            return render_template(
                'employees/list.html',
                employees=employees,
                roles=roles,
                current_page=page,
                per_page=per_page,
                total_count=total_count,
                total_pages=total_pages,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
            
    except Exception as e:
        print(f"Error in employee_list: {str(e)}")  # Debug print
        flash(f'Error retrieving employees: {str(e)}', 'error')
        return render_template('employees/list.html', 
                             employees=[], 
                             roles=[], 
                             current_page=1, 
                             per_page=10, 
                             total_count=0, 
                             total_pages=0,
                             search='',
                             sort_by='employeename',
                             sort_dir='ASC')
    finally:
        if conn:
            conn.close()

@app.route('/create_employee', methods=['POST'])
@login_required
def create_employee():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get form data with default values for all fields
            data = {
                'employeename': request.form.get('employeename', ''),
                'transactiontype': request.form.get('transactiontype', 'S'),
                'address': request.form.get('address', ''),
                'address2': request.form.get('address2', ''),
                'zipcode': request.form.get('zipcode', ''),
                'city': request.form.get('city', 'Nicosia'),
                'age': request.form.get('age', '0'),
                'gender': request.form.get('gender', 'Male'),
                'tel': request.form.get('tel', ''),
                'nationality': request.form.get('nationality', 'Cypriot'),
                'email': request.form.get('email', ''),
                'currentworkplace': request.form.get('currentworkplace', 'No'),
                'SocialInsuranceno': request.form.get('SocialInsuranceno', ''),
                'Tattoo': request.form.get('Tattoo', 'No'),
                'AgreementStatus': request.form.get('AgreementStatus', 'No'),
                'CriminalRecordStatus': request.form.get('CriminalRecordStatus', 'No'),
                'TrainingStatus': request.form.get('TrainingStatus', 'No'),
                'Interestforfulltime': request.form.get('Interestforfulltime', 'No'),
                'Repeater': request.form.get('Repeater', 'No'),
                'status': request.form.get('status', 'Active'),
                'passportid': request.form.get('passportid', ''),
                'EmploymentAgreement': request.form.get('EmploymentAgreement', ''),
                'employeeidno': request.form.get('employeeidno', '0'),
                'employeeroleid': request.form.get('employeeroleid', '1'),
                'employeeenglishrating': request.form.get('employeeenglishrating', '1'),
                'employeeExperienceRating': request.form.get('employeeExperienceRating', '1'),
                'contactmethod': request.form.get('contactmethod', 'email'),
                'companyid': request.form.get('companyid', ''),
                'bankid': request.form.get('bankid', ''),
                'swiftno': request.form.get('swiftno', '')
            }

            # Convert numeric fields
            try:
                data['age'] = int(data['age']) if data['age'] else 0
                data['employeeidno'] = int(data['employeeidno']) if data['employeeidno'] else 0
                data['employeeroleid'] = int(data['employeeroleid']) if data['employeeroleid'] else 1
                if data['companyid']:
                    data['companyid'] = int(data['companyid'])
                if data['bankid']:
                    data['bankid'] = int(data['bankid'])
            except ValueError:
                flash('Invalid numeric value provided', 'error')
                return redirect(url_for('employee_list'))

            # Validate enum fields
            enums = {
                'transactiontype': ['S', 'B'],
                'city': ['Nicosia', 'Limassol', 'Larnaca', 'Famagusta', 'Paphos'],
                'gender': ['Male', 'Female'],
                'nationality': ['Cypriot', 'EU', 'Foreigner'],
                'currentworkplace': ['Yes', 'No'],
                'Tattoo': ['Yes', 'No'],
                'AgreementStatus': ['Yes', 'No'],
                'CriminalRecordStatus': ['Yes', 'No'],
                'TrainingStatus': ['Yes', 'No'],
                'Interestforfulltime': ['Yes', 'No'],
                'Repeater': ['Yes', 'No'],
                'status': ['Active', 'Inactive'],
                'employeeenglishrating': ['1', '2', '3', '4', '5'],
                'employeeExperienceRating': ['1', '2', '3', '4', '5'],
                'contactmethod': ['email', 'sms']
            }

            # Validate and set default values for enum fields
            for field, valid_values in enums.items():
                if data[field] not in valid_values:
                    data[field] = valid_values[0]  # Set to first valid value if invalid

            # Check which fields exist in the employee table
            cursor.execute("DESCRIBE employee")
            valid_fields = [column['Field'] for column in cursor.fetchall()]
            
            # Filter data to include only valid fields
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            
            # Build the INSERT query
            fields = list(filtered_data.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            columns = ', '.join(fields)
            query = f"INSERT INTO employee ({columns}) VALUES ({placeholders})"
            values = list(filtered_data.values())
            
            cursor.execute(query, values)
            conn.commit()
            flash('Employee created successfully!', 'success')
            
    except Exception as e:
        print(f"Error in create_employee: {str(e)}")  # Debug print
        flash(f'Error creating employee: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('employee_list'))

@app.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            if request.method == 'POST':
                # Get form data with default values for all fields
                data = {
                    'employeename': request.form.get('employeename', ''),
                    'transactiontype': request.form.get('transactiontype', 'S'),
                    'address': request.form.get('address', ''),
                    'address2': request.form.get('address2', ''),
                    'zipcode': request.form.get('zipcode', ''),
                    'city': request.form.get('city', 'Nicosia'),
                    'age': request.form.get('age', '0'),
                    'gender': request.form.get('gender', 'Male'),
                    'tel': request.form.get('tel', ''),
                    'nationality': request.form.get('nationality', 'Cypriot'),
                    'email': request.form.get('email', ''),
                    'currentworkplace': request.form.get('currentworkplace', 'No'),
                    'SocialInsuranceno': request.form.get('SocialInsuranceno', ''),
                    'Tattoo': request.form.get('Tattoo', 'No'),
                    'AgreementStatus': request.form.get('AgreementStatus', 'No'),
                    'CriminalRecordStatus': request.form.get('CriminalRecordStatus', 'No'),
                    'TrainingStatus': request.form.get('TrainingStatus', 'No'),
                    'Interestforfulltime': request.form.get('Interestforfulltime', 'No'),
                    'Repeater': request.form.get('Repeater', 'No'),
                    'status': request.form.get('status', 'Active'),
                    'passportid': request.form.get('passportid', ''),
                    'EmploymentAgreement': request.form.get('EmploymentAgreement', ''),
                    'employeeidno': request.form.get('employeeidno', '0'),
                    'employeeroleid': request.form.get('employeeroleid', '1'),
                    'employeeenglishrating': request.form.get('employeeenglishrating', '1'),
                    'employeeExperienceRating': request.form.get('employeeExperienceRating', '1'),
                    'contactmethod': request.form.get('contactmethod', 'email'),
                    'companyid': request.form.get('companyid', ''),
                    'bankid': request.form.get('bankid', ''),
                    'swiftno': request.form.get('swiftno', '')
                }

                # Convert numeric fields
                try:
                    data['age'] = int(data['age']) if data['age'] else 0
                    data['employeeidno'] = int(data['employeeidno']) if data['employeeidno'] else 0
                    data['employeeroleid'] = int(data['employeeroleid']) if data['employeeroleid'] else 1
                    if data['companyid']:
                        data['companyid'] = int(data['companyid'])
                    if data['bankid']:
                        data['bankid'] = int(data['bankid'])
                except ValueError:
                    flash('Invalid numeric value provided', 'error')
                    return redirect(url_for('employee_list'))

                # Validate enum fields
                enums = {
                    'transactiontype': ['S', 'B'],
                    'city': ['Nicosia', 'Limassol', 'Larnaca', 'Famagusta', 'Paphos'],
                    'gender': ['Male', 'Female'],
                    'nationality': ['Cypriot', 'EU', 'Foreigner'],
                    'currentworkplace': ['Yes', 'No'],
                    'Tattoo': ['Yes', 'No'],
                    'AgreementStatus': ['Yes', 'No'],
                    'CriminalRecordStatus': ['Yes', 'No'],
                    'TrainingStatus': ['Yes', 'No'],
                    'Interestforfulltime': ['Yes', 'No'],
                    'Repeater': ['Yes', 'No'],
                    'status': ['Active', 'Inactive'],
                    'employeeenglishrating': ['1', '2', '3', '4', '5'],
                    'employeeExperienceRating': ['1', '2', '3', '4', '5'],
                    'contactmethod': ['email', 'sms']
                }

                # Validate and set default values for enum fields
                for field, valid_values in enums.items():
                    if data[field] not in valid_values:
                        data[field] = valid_values[0]  # Set to first valid value if invalid

                # Build and execute update query - only update fields that exist in the employee table
                cursor.execute("DESCRIBE employee")
                valid_fields = [column['Field'] for column in cursor.fetchall()]
                
                # Filter data to include only valid fields
                filtered_data = {k: v for k, v in data.items() if k in valid_fields}
                
                # Build the update query
                fields = list(filtered_data.keys())
                placeholders = ', '.join([f"{field} = %s" for field in fields])
                query = f"UPDATE employee SET {placeholders} WHERE employeeid = %s"
                values = list(filtered_data.values()) + [employee_id]
                
                cursor.execute(query, values)
                conn.commit()
                flash('Employee updated successfully!', 'success')
                return redirect(url_for('employee_list'))
            
            # GET request - fetch employee data
            cursor.execute('''
                SELECT 
                    e.*,
                    COALESCE(er.employeerolename, '') as employeerolename
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE e.employeeid = %s
            ''', (employee_id,))
            
            employee = cursor.fetchone()
            if not employee:
                flash('Employee not found.', 'error')
                return redirect(url_for('employee_list'))

            # Convert all values to strings and handle None values
            serializable_employee = {}
            for key, value in employee.items():
                if value is None:
                    if key in ['age', 'employeeidno', 'employeeroleid']:
                        serializable_employee[key] = '0'
                    elif key in ['currentworkplace', 'Tattoo', 'AgreementStatus', 
                               'CriminalRecordStatus', 'TrainingStatus', 
                               'Interestforfulltime', 'Repeater']:
                        serializable_employee[key] = 'No'
                    elif key == 'status':
                        serializable_employee[key] = 'Active'
                    elif key in ['employeeenglishrating', 'employeeExperienceRating']:
                        serializable_employee[key] = '1'
                    elif key == 'contactmethod':
                        serializable_employee[key] = 'email'
                    elif key == 'nationality':
                        serializable_employee[key] = 'Cypriot'
                    elif key == 'gender':
                        serializable_employee[key] = 'Male'
                    elif key == 'city':
                        serializable_employee[key] = 'Nicosia'
                    elif key == 'transactiontype':
                        serializable_employee[key] = 'S'
                    else:
                        serializable_employee[key] = ''
                elif isinstance(value, (int, float, decimal.Decimal)):
                    serializable_employee[key] = str(value)
                else:
                    serializable_employee[key] = str(value)

            # Get roles for dropdown
            cursor.execute('SELECT employeeroleid, employeerolename FROM employeerole ORDER BY employeerolename')
            roles = cursor.fetchall()
            serializable_roles = []
            for role in roles:
                serializable_roles.append({
                    'employeeroleid': str(role['employeeroleid']),
                    'employeerolename': role['employeerolename'] if role['employeerolename'] else ''
                })
                
            # Get companies for dropdown
            cursor.execute('SELECT companyid, companyname, bankid FROM company ORDER BY companyname')
            companies = cursor.fetchall()
            serializable_companies = []
            for company in companies:
                serializable_companies.append({
                    'companyid': str(company['companyid']),
                    'companyname': company['companyname'] if company['companyname'] else '',
                    'bankid': str(company['bankid']) if company['bankid'] else ''
                })

            # Get banks for dropdown
            cursor.execute('SELECT bankid, bankname, biccode FROM banks ORDER BY bankname')
            banks = cursor.fetchall()
            serializable_banks = []
            for bank in banks:
                serializable_banks.append({
                    'bankid': str(bank['bankid']),
                    'bankname': bank['bankname'] if bank['bankname'] else '',
                    'biccode': bank['biccode'] if bank['biccode'] else ''
                })

            # Define enum values for the template
            template_enums = {
                'cities': ['Nicosia', 'Limassol', 'Larnaca', 'Famagusta', 'Paphos'],
                'genders': ['Male', 'Female'],
                'nationalities': ['Cypriot', 'EU', 'Foreigner'],
                'yes_no': ['Yes', 'No'],
                'ratings': ['1', '2', '3', '4', '5'],
                'contact_methods': ['email', 'sms'],
                'transaction_types': ['S', 'B'],
                'statuses': ['Active', 'Inactive']
            }

            return render_template('employees/unified/employee_form.html',
                                 is_edit_mode=True,
                                 employee=serializable_employee,
                                 roles=serializable_roles,
                                 companies=serializable_companies,
                                 banks=serializable_banks,
                                 enums=template_enums)
            
    except Exception as e:
        print(f"Error in edit_employee: {str(e)}")  # Debug print
        flash(f'Error editing employee: {str(e)}', 'error')
        return redirect(url_for('employee_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/employees/<int:employee_id>/delete', methods=['POST'])
@login_required
def delete_employee(employee_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if employee has associated shifts
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM employee_shifts 
                WHERE employeeid = %s
            ''', (employee_id,))
            
            shift_count = cursor.fetchone()['count']
            if shift_count > 0:
                flash(f'Cannot delete employee: They have {shift_count} assigned shifts. Please remove these assignments first.', 'error')
                return redirect(url_for('employee_list'))
            
            # If no shifts, proceed with deletion
            cursor.execute('DELETE FROM employee WHERE employeeid = %s', (employee_id,))
            conn.commit()
            flash('Employee deleted successfully!', 'success')
            
    except Exception as e:
        print(f"Error in delete_employee: {str(e)}")  # Debug print
        flash(f'Error deleting employee: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('employee_list'))

@app.route('/delete_multiple_employees', methods=['POST'])
@login_required
def delete_multiple_employees():
    try:
        # Get the list of employee IDs to delete
        employee_ids_json = request.form.get('employee_ids', '[]')
        employee_ids = json.loads(employee_ids_json)
        
        if not employee_ids:
            flash('No employees selected for deletion.', 'warning')
            return redirect(url_for('employee_list'))
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        try:
            with conn.cursor() as cursor:
                # Format the IDs for the SQL IN clause
                id_placeholder = ','.join(['%s'] * len(employee_ids))
                
                # Check if any employees have associated shifts
                cursor.execute(f'''
                    SELECT e.employeeid, e.employeename, COUNT(es.shiftid) as shift_count
                    FROM employee e
                    LEFT JOIN employee_shifts es ON e.employeeid = es.employeeid
                    WHERE e.employeeid IN ({id_placeholder})
                    GROUP BY e.employeeid, e.employeename
                    HAVING COUNT(es.shiftid) > 0
                ''', employee_ids)
                
                employees_with_shifts = cursor.fetchall()
                if employees_with_shifts:
                    # Some employees have shifts, show error message
                    employee_names = ', '.join([f"{e['employeename']} ({e['shift_count']} shifts)" for e in employees_with_shifts])
                    flash(f'Cannot delete employees with assigned shifts: {employee_names}', 'error')
                    return redirect(url_for('employee_list'))
                
                # Delete employees without shifts
                cursor.execute(f'''
                    DELETE FROM employee
                    WHERE employeeid IN ({id_placeholder})
                ''', employee_ids)
                
                deleted_count = cursor.rowcount
                conn.commit()
                flash(f'Successfully deleted {deleted_count} employees.', 'success')
            
        except Exception as e:
            conn.rollback()
            flash(f'Error deleting employees: {str(e)}', 'error')
        finally:
            conn.close()
    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'error')
    
    return redirect(url_for('employee_list'))

@app.route('/employees/<int:employee_id>/agreement', methods=['GET'])
@login_required
def view_employee_agreement(employee_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get employee details
            cursor.execute('''
                SELECT 
                    e.*,
                    COALESCE(er.employeerolename, '') as employeerolename
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE e.employeeid = %s
            ''', (employee_id,))
            
            employee = cursor.fetchone()
            if not employee:
                flash('Employee not found.', 'error')
                return redirect(url_for('employee_list'))
            
            # Check if agreement exists
            if not employee.get('EmploymentAgreement'):
                flash('No employment agreement found for this employee.', 'warning')
                return redirect(url_for('edit_employee', employee_id=employee_id))
            
            # Get company details
            company = None
            if employee.get('companyid'):
                cursor.execute('SELECT * FROM company WHERE companyid = %s', (employee['companyid'],))
                company = cursor.fetchone()
            
            # For demonstration, we're rendering a template with the agreement details
            # In a real system, this might serve a PDF file
            return render_template('employees/agreement.html',
                                 employee=safe_serialize(employee),
                                 company=safe_serialize(company) if company else None,
                                 current_date=datetime.now().strftime('%Y-%m-%d'))
    
    except Exception as e:
        print(f"Error in view_employee_agreement: {str(e)}")  # Debug print
        flash(f'Error viewing agreement: {str(e)}', 'error')
        return redirect(url_for('employee_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/employees/<int:employee_id>/agreement/generate', methods=['POST'])
@login_required
def generate_employee_agreement(employee_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get form data
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            hourly_rate = request.form.get('hourly_rate')
            terms = request.form.get('terms')
            
            # Create agreement text
            agreement_text = f"""Start Date: {start_date}
End Date: {end_date}
Hourly Rate: €{hourly_rate}

Terms and Conditions:
{terms}"""
            
            # Update employee with new agreement
            cursor.execute('''
                UPDATE employee 
                SET EmploymentAgreement = %s
                WHERE employeeid = %s
            ''', (agreement_text, employee_id))
            
            conn.commit()
            flash('Employee agreement updated successfully!', 'success')
            
            return redirect(url_for('view_employee_agreement', employee_id=employee_id))
            
    except Exception as e:
        flash(f'Error generating employee agreement: {str(e)}', 'error')
        return redirect(url_for('view_employee_agreement', employee_id=employee_id))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice_list')
@login_required
def invoice_list():
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        sort_by = request.args.get('sort', 'invoice_date')
        sort_dir = request.args.get('dir', 'DESC')
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Build the base query
            query = '''
                SELECT 
                    i.*,
                    c.customername,
                    e.EventName as event_name
                FROM invoice i
                LEFT JOIN customer c ON i.customer_id = c.customerid
                LEFT JOIN event e ON i.event_id = e.EventID
                WHERE 1=1
            '''
            
            params = []
            
            # Add search condition if provided
            if search:
                query += ''' AND (
                    i.invoice_number LIKE %s OR
                    c.customername LIKE %s OR
                    e.EventName LIKE %s OR
                    i.status LIKE %s
                )'''
                search_term = f'%{search}%'
                params.extend([search_term, search_term, search_term, search_term])
            
            # Get total count for pagination
            count_query = f"SELECT COUNT(*) as total FROM ({query}) as t"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['total']
            
            # Add sorting
            if sort_by in ['invoice_date', 'invoice_number', 'status', 'total']:
                query += f' ORDER BY i.{sort_by} {sort_dir}'
            elif sort_by == 'customername':
                query += f' ORDER BY c.customername {sort_dir}'
            elif sort_by == 'event_name':
                query += f' ORDER BY e.EventName {sort_dir}'
            
            # Add pagination
            query += ' LIMIT %s OFFSET %s'
            offset = (page - 1) * per_page
            params.extend([per_page, offset])
            
            # Execute final query
            cursor.execute(query, params)
            invoices = cursor.fetchall()
            
            # Calculate total pages
            total_pages = (total_count + per_page - 1) // per_page
            
            # Get customers for filtering
            cursor.execute('SELECT customerid, customername FROM customer ORDER BY customername')
            customers = cursor.fetchall()
            
            return render_template('invoices/list.html',
                                 invoices=invoices,
                                 customers=customers,
                                 current_page=page,
                                 total_pages=total_pages,
                                 total_count=total_count,
                                 per_page=per_page,
                                 search=search,
                                 sort_by=sort_by,
                                 sort_dir=sort_dir)
                                 
    except Exception as e:
        flash(f'Error loading invoices: {str(e)}', 'error')
        return render_template('invoices/list.html',
                             invoices=[],
                             customers=[],
                             current_page=1,
                             total_pages=1,
                             total_count=0,
                             per_page=10,
                             search='',
                             sort_by='invoice_date',
                             sort_dir='DESC')
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice/create', methods=['GET', 'POST'])
@login_required
def invoice_create():
    if request.method == 'POST':
        try:
            data = request.form
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                # Insert invoice
                cursor.execute('''
                    INSERT INTO invoice (
                        customer_id, event_id, invoice_date, due_date,
                        invoice_number, status, vat_rate, notes,
                        subtotal, vat_amount, total
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    data['customer_id'],
                    data['event_id'] if data['event_id'] else None,
                    data['invoice_date'],
                    data['due_date'] if data['due_date'] else None,
                    data['invoice_number'],
                    'Draft',
                    data['vat_rate'],
                    data['notes'],
                    data['subtotal'],
                    data['vat_amount'],
                    data['total']
                ))
                
                invoice_id = cursor.lastrowid
                
                # Insert invoice items
                items = json.loads(data['items'])
                for item in items:
                    cursor.execute('''
                        INSERT INTO invoice_item (
                            invoice_id, description, quantity,
                            unit_price, total
                        ) VALUES (%s, %s, %s, %s, %s)
                    ''', (
                        invoice_id,
                        item['description'],
                        item['quantity'],
                        item['unit_price'],
                        item['total']
                    ))
                
                conn.commit()
                flash('Invoice created successfully', 'success')
                return redirect(url_for('invoice_view', invoice_id=invoice_id))
                
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            flash(f'Error creating invoice: {str(e)}', 'error')
            return redirect(url_for('invoice_create'))
        finally:
            if 'conn' in locals():
                conn.close()
    
    # GET request - show create form
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get customers
            cursor.execute('SELECT customerid, customername FROM customer ORDER BY customername')
            customers = cursor.fetchall()
            
            # Get events
            cursor.execute('SELECT EventID, EventName FROM event ORDER BY EventName')
            events = cursor.fetchall()
            
            return render_template('invoices/form.html',
                                 customers=customers,
                                 events=events,
                                 invoice=None,
                                 items=[],
                                 mode='create')
    except Exception as e:
        flash(f'Error loading form data: {str(e)}', 'error')
        return redirect(url_for('invoice_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice/<int:invoice_id>')
@login_required
def invoice_view(invoice_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get invoice details
            cursor.execute('''
                SELECT 
                    i.*,
                    c.customername,
                    e.EventName as event_name
                FROM invoice i
                LEFT JOIN customer c ON i.customer_id = c.customerid
                LEFT JOIN event e ON i.event_id = e.EventID
                WHERE i.invoice_id = %s
            ''', (invoice_id,))
            invoice = cursor.fetchone()
            
            if not invoice:
                flash('Invoice not found', 'error')
                return redirect(url_for('invoice_list'))
            
            # Get invoice items
            cursor.execute('SELECT * FROM invoice_item WHERE invoice_id = %s', (invoice_id,))
            items = cursor.fetchall()
            
            # Debug: Print the structure of the first item
            if items and len(items) > 0:
                print("Invoice Item Keys:", items[0].keys())
                print("First Item:", items[0])
            
            return render_template('invoices/view.html',
                                 invoice=invoice,
                                 items=items)
    except Exception as e:
        flash(f'Error loading invoice: {str(e)}', 'error')
        return redirect(url_for('invoice_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def invoice_edit(invoice_id):
    if request.method == 'POST':
        try:
            data = request.form
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                # Update invoice
                cursor.execute('''
                    UPDATE invoice SET
                        customer_id = %s,
                        event_id = %s,
                        invoice_date = %s,
                        due_date = %s,
                        invoice_number = %s,
                        status = %s,
                        vat_rate = %s,
                        notes = %s,
                        subtotal = %s,
                        vat_amount = %s,
                        total = %s
                    WHERE invoice_id = %s
                ''', (
                    data['customer_id'],
                    data['event_id'] if data['event_id'] else None,
                    data['invoice_date'],
                    data['due_date'] if data['due_date'] else None,
                    data['invoice_number'],
                    data['status'],
                    data['vat_rate'],
                    data['notes'],
                    data['subtotal'],
                    data['vat_amount'],
                    data['total'],
                    invoice_id
                ))
                
                # Delete existing items
                cursor.execute('DELETE FROM invoice_item WHERE invoice_id = %s', (invoice_id,))
                
                # Insert updated items
                items = json.loads(data['items'])
                for item in items:
                    cursor.execute('''
                        INSERT INTO invoice_item (
                            invoice_id, description, quantity,
                            unit_price, total
                        ) VALUES (%s, %s, %s, %s, %s)
                    ''', (
                        invoice_id,
                        item['description'],
                        item['quantity'],
                        item['unit_price'],
                        item['total']
                    ))
                
                conn.commit()
                flash('Invoice updated successfully', 'success')
                return redirect(url_for('invoice_view', invoice_id=invoice_id))
                
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            flash(f'Error updating invoice: {str(e)}', 'error')
            return redirect(url_for('invoice_edit', invoice_id=invoice_id))
        finally:
            if 'conn' in locals():
                conn.close()
    
    # GET request - show edit form
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get invoice details
            cursor.execute('''
                SELECT * FROM invoice WHERE invoice_id = %s
            ''', (invoice_id,))
            invoice = cursor.fetchone()
            
            if not invoice:
                flash('Invoice not found', 'error')
                return redirect(url_for('invoice_list'))
            
            # Get invoice items
            cursor.execute('SELECT * FROM invoice_item WHERE invoice_id = %s', (invoice_id,))
            items = cursor.fetchall()
            
            # Debug: Print the column names and sample data
            if items and len(items) > 0:
                print("Invoice Item Keys:", items[0].keys())
                print("Sample Item Data:", items[0])
            
            # Get customers
            cursor.execute('SELECT customerid, customername FROM customer ORDER BY customername')
            customers = cursor.fetchall()
            
            # Get events
            cursor.execute('SELECT EventID, EventName FROM event ORDER BY EventName')
            events = cursor.fetchall()
            
            return render_template('invoices/form.html',
                                 invoice=invoice,
                                 items=items,
                                 customers=customers,
                                 events=events,
                                 mode='edit')
    except Exception as e:
        flash(f'Error loading invoice: {str(e)}', 'error')
        return redirect(url_for('invoice_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice/<int:invoice_id>', methods=['DELETE'])
@login_required
def invoice_delete(invoice_id):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if invoice exists and is in Draft status
            cursor.execute('SELECT status FROM invoice WHERE invoice_id = %s', (invoice_id,))
            invoice = cursor.fetchone()
            
            if not invoice:
                return jsonify({'success': False, 'message': 'Invoice not found'})
            
            if invoice['status'] != 'Draft':
                return jsonify({'success': False, 'message': 'Only draft invoices can be deleted'})
            
            # Delete invoice (invoice_items will be deleted automatically due to CASCADE)
            cursor.execute('DELETE FROM invoice WHERE invoice_id = %s', (invoice_id,))
            conn.commit()
            
            return jsonify({'success': True})
            
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/employees/add', methods=['GET'])
@login_required
def add_employee():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get roles for dropdown
            cursor.execute('SELECT employeeroleid, employeerolename FROM employeerole ORDER BY employeerolename')
            roles = cursor.fetchall()
            serializable_roles = []
            for role in roles:
                serializable_roles.append({
                    'employeeroleid': str(role['employeeroleid']),
                    'employeerolename': role['employeerolename'] if role['employeerolename'] else ''
                })
                
            # Get companies for dropdown
            cursor.execute('SELECT companyid, companyname, bankid FROM company ORDER BY companyname')
            companies = cursor.fetchall()
            serializable_companies = []
            for company in companies:
                serializable_companies.append({
                    'companyid': str(company['companyid']),
                    'companyname': company['companyname'] if company['companyname'] else '',
                    'bankid': str(company['bankid']) if company['bankid'] else ''
                })

            # Get banks for dropdown
            cursor.execute('SELECT bankid, bankname, biccode FROM banks ORDER BY bankname')
            banks = cursor.fetchall()
            serializable_banks = []
            for bank in banks:
                serializable_banks.append({
                    'bankid': str(bank['bankid']),
                    'bankname': bank['bankname'] if bank['bankname'] else '',
                    'biccode': bank['biccode'] if bank['biccode'] else ''
                })

            # Define enum values for the template
            template_enums = {
                'cities': ['Nicosia', 'Limassol', 'Larnaca', 'Famagusta', 'Paphos'],
                'genders': ['Male', 'Female'],
                'nationalities': ['Cypriot', 'EU', 'Foreigner'],
                'yes_no': ['Yes', 'No'],
                'ratings': ['1', '2', '3', '4', '5'],
                'contact_methods': ['email', 'sms'],
                'transaction_types': ['S', 'B'],
                'statuses': ['Active', 'Inactive']
            }

            # Create default employee for the form
            default_employee = {
                'employeename': '',
                'transactiontype': 'S',
                'address': '',
                'address2': '',
                'zipcode': '',
                'city': 'Nicosia',
                'age': '0',
                'gender': 'Male',
                'tel': '',
                'nationality': 'Cypriot',
                'email': '',
                'currentworkplace': 'No',
                'SocialInsuranceno': '',
                'Tattoo': 'No',
                'AgreementStatus': 'No',
                'CriminalRecordStatus': 'No',
                'TrainingStatus': 'No',
                'Interestforfulltime': 'No',
                'Repeater': 'No',
                'status': 'Active',
                'passportid': '',
                'EmploymentAgreement': '',
                'employeeidno': '0',
                'employeeroleid': '1',
                'employeeenglishrating': '1',
                'employeeExperienceRating': '1',
                'contactmethod': 'email',
                'bankid': '',
                'companyid': '',
                'swiftno': ''
            }

            return render_template('employees/unified/employee_form.html',
                                 is_edit_mode=False,
                                 employee=default_employee,
                                 roles=serializable_roles,
                                 companies=serializable_companies,
                                 banks=serializable_banks,
                                 enums=template_enums)
            
    except Exception as e:
        print(f"Error in add_employee: {str(e)}")  # Debug print
        flash(f'Error preparing employee form: {str(e)}', 'error')
        return redirect(url_for('employee_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/companies/add', methods=['GET'])
@login_required
def add_company_page():
    """Display the add company page."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get the count of existing companies
            cursor.execute('SELECT COUNT(*) as count FROM company')
            company_count = cursor.fetchone()['count']
            
            if company_count >= 1:
                flash('Cannot create a new company: Only one company is allowed in the system.', 'error')
                return redirect(url_for('company_list'))
            
            # Get banks for dropdown
            cursor.execute('SELECT bankid, bankname FROM banks ORDER BY bankname')
            banks = cursor.fetchall()
            
            return render_template('companies/unified/company_form.html', 
                                  is_edit_mode=False, 
                                  banks=banks)
    except Exception as e:
        flash(f'Error loading form: {str(e)}', 'error')
        return redirect(url_for('company_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/companies/<int:company_id>/employees')
@login_required
def company_employees(company_id):
    """Display employees for a specific company."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get company details
            cursor.execute('SELECT * FROM company WHERE companyid = %s', (company_id,))
            company = cursor.fetchone()
            
            if not company:
                flash('Company not found.', 'error')
                return redirect(url_for('company_list'))
            
            # Get employees for this company
            cursor.execute('''
                SELECT 
                    e.employeeid,
                    e.employeename,
                    e.gender,
                    e.email,
                    e.tel,
                    e.status,
                    COALESCE(er.employeerolename, '') as role
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE e.companyid = %s
                ORDER BY e.employeename
            ''', (company_id,))
            
            employees = cursor.fetchall()
            
            return render_template('companies/employees.html',
                                 company=company,
                                 employees=employees)
    except Exception as e:
        flash(f'Error loading company employees: {str(e)}', 'error')
        return redirect(url_for('company_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/events/create', methods=['GET'])
@login_required
def create_event_page():
    """Display the create event page."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get customers for dropdown
            cursor.execute('SELECT customerid, customername FROM customer ORDER BY customername')
            customers = cursor.fetchall()
            
            # Get default company
            cursor.execute('SELECT * FROM company LIMIT 1')
            company = cursor.fetchone()
            
            # Get all employees for potential assignment
            cursor.execute('''
                SELECT 
                    e.employeeid,
                    e.employeename,
                    e.gender,
                    e.email,
                    e.tel,
                    e.age,
                    e.nationality,
                    e.employeeidno,
                    e.passportid,
                    e.employeeenglishrating,
                    e.employeeExperienceRating,
                    er.employeerolename as role
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE e.status = 'Active'
                ORDER BY e.employeename
            ''')
            
            employees_raw = cursor.fetchall()
            
            # Format employees for JavaScript
            employees = []
            for emp in employees_raw:
                role_value = emp['role'] or ''  # Use empty string instead of None
                employees.append({
                    'employeeid': int(emp['employeeid']),
                    'employeename': emp['employeename'],
                    'gender': emp['gender'],
                    'email': emp['email'],
                    'tel': emp['tel'],
                    'age': emp['age'],
                    'nationality': emp['nationality'],
                    'employeeidno': emp['employeeidno'],
                    'passportid': emp['passportid'],
                    'employeeenglishrating': emp['employeeenglishrating'],
                    'employeeExperienceRating': emp['employeeExperienceRating'],
                    'englishrating': emp['employeeenglishrating'],
                    'experiencerating': emp['employeeExperienceRating'],
                    'role': role_value,
                    'employeerolename': role_value  # Add both fields for consistency
                })
            
            # Default event details
            event = {
                'EventName': '',
                'EventStart': '',
                'EventEnd': '',
                'EventLocation': '',
                'notes': '',
                'Customerid': '',
                'EventStage': 'Draft',
                'WaitersNeeded': '0',
                'BartendersNeeded': '0',
                'MaleEmployees': '0',
                'FemaleEmployees': '0',
                'TotalEmployees': '0',
                'EventDurationHours': '0',
                'EventTotalHours': '0',
                'EventPerHourcost': '0',
                'EventPerHourselling': '0',
                'totalhours': '0',
                'totalcost': '0',
                'totalselling': '0',
                'totalprofit': '0',
                'totalshifthours': '0'
            }
            
            # Empty shifts array for new events
            formatted_shifts = []
            
            return render_template('events/unified/event_form.html',
                                 is_edit_mode=False,
                                 event=event,
                                 customers=customers,
                                 company=company,
                                 shifts=formatted_shifts,
                                 employees=employees)
                                 
    except Exception as e:
        flash(f'Error loading create event form: {str(e)}', 'error')
        return redirect(url_for('event_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/events/<int:event_id>/edit', methods=['GET'])
@login_required
def edit_event_unified(event_id):
    """Display the edit event page."""
    try:
        # Set up logging
        import logging
        logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Debug: Get all employee assignments for this event
            cursor.execute('''
                SELECT 
                    s.shiftid,
                    s.shiftname,
                    e.employeeid,
                    e.employeename,
                    es.hours
                FROM shifts s
                JOIN employee_shifts es ON s.shiftid = es.shiftid
                JOIN employee e ON es.employeeid = e.employeeid
                WHERE s.eventid = %s
                ORDER BY s.shiftid, e.employeename
            ''', (event_id,))
            all_assignments = cursor.fetchall()
            logging.debug("=== All employee assignments ===")
            for assignment in all_assignments:
                logging.debug(f"Shift {assignment['shiftid']} ({assignment['shiftname']}): Employee {assignment['employeeid']} ({assignment['employeename']}) - {assignment['hours']} hours")

            # Get event details with total unique employees
            cursor.execute('''
                SELECT 
                    e.*,
                    c.customername,
                    (SELECT COUNT(DISTINCT es.employeeid)
                     FROM shifts s
                     JOIN employee_shifts es ON s.shiftid = es.shiftid
                     WHERE s.eventid = e.EventID) as total_unique_employees
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                WHERE e.EventID = %s
            ''', (event_id,))
            
            event = cursor.fetchone()
            if not event:
                flash('Event not found.', 'error')
                return redirect(url_for('event_list'))
            
            # Get customers for dropdown
            cursor.execute('SELECT customerid, customername FROM customer ORDER BY customername')
            customers = cursor.fetchall()
            
            # Get company details
            cursor.execute('SELECT * FROM company LIMIT 1')
            company = cursor.fetchone()
            
            # Format dates for display in form
            if event['EventStart']:
                if isinstance(event['EventStart'], str):
                    try:
                        event['EventStart'] = datetime.strptime(event['EventStart'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            event['EventStart'] = datetime.strptime(event['EventStart'], '%Y-%m-%d %H:%M')
                        except ValueError:
                            event['EventStart'] = None
                if isinstance(event['EventStart'], datetime):
                    event['EventStart'] = event['EventStart'].strftime('%Y-%m-%dT%H:%M')
            
            if event['EventEnd']:
                if isinstance(event['EventEnd'], str):
                    try:
                        event['EventEnd'] = datetime.strptime(event['EventEnd'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            event['EventEnd'] = datetime.strptime(event['EventEnd'], '%Y-%m-%d %H:%M')
                        except ValueError:
                            event['EventEnd'] = None
                if isinstance(event['EventEnd'], datetime):
                    event['EventEnd'] = event['EventEnd'].strftime('%Y-%m-%dT%H:%M')
            
            # Get all shifts for this event with correct employee count and full employee details
            cursor.execute('''
                WITH ShiftAssignments AS (
                    SELECT 
                        s.shiftid,
                        GROUP_CONCAT(DISTINCT es.employeeid) as assigned_employee_ids,
                        COUNT(DISTINCT es.employeeid) as assigned_employees_count,
                        COALESCE(SUM(es.hours), 0) as total_assigned_hours,
                        JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'employeeid', e.employeeid,
                                'employeename', e.employeename,
                                'employeerolename', er.employeerolename,
                                'gender', e.gender,
                                'hours', es.hours
                            )
                        ) as employees
                    FROM shifts s
                    LEFT JOIN employee_shifts es ON s.shiftid = es.shiftid
                    LEFT JOIN employee e ON es.employeeid = e.employeeid
                    LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                    WHERE s.eventid = %s
                    GROUP BY s.shiftid
                )
                SELECT 
                    s.*,
                    COALESCE(sa.assigned_employee_ids, '') as assigned_employee_ids,
                    COALESCE(sa.assigned_employees_count, 0) as assigned_employees_count,
                    COALESCE(sa.total_assigned_hours, 0) as total_assigned_hours,
                    COALESCE(sa.employees, '[]') as employees
                FROM shifts s
                LEFT JOIN ShiftAssignments sa ON s.shiftid = sa.shiftid
                WHERE s.eventid = %s
                ORDER BY s.shiftstart
            ''', (event_id, event_id))
            
            shifts = cursor.fetchall()
            
            # Debug: Print shift assignments
            logging.debug("\n=== Shift assignments after processing ===")
            for shift in shifts:
                logging.debug(f"Shift {shift['shiftid']} ({shift['shiftname']}): {shift['assigned_employees_count']} employees, IDs: {shift['assigned_employee_ids']}")
            
            # Format shift dates and convert to serializable format
            for shift in shifts:
                if shift['shiftstart']:
                    if isinstance(shift['shiftstart'], str):
                        try:
                            shift['shiftstart'] = datetime.strptime(shift['shiftstart'], '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                shift['shiftstart'] = datetime.strptime(shift['shiftstart'], '%Y-%m-%d %H:%M')
                            except ValueError:
                                shift['shiftstart'] = None
                    if isinstance(shift['shiftstart'], datetime):
                        shift['shiftstart'] = shift['shiftstart'].strftime('%Y-%m-%dT%H:%M')
                
                if shift['shiftend']:
                    if isinstance(shift['shiftend'], str):
                        try:
                            shift['shiftend'] = datetime.strptime(shift['shiftend'], '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                shift['shiftend'] = datetime.strptime(shift['shiftend'], '%Y-%m-%d %H:%M')
                            except ValueError:
                                shift['shiftend'] = None
                    if isinstance(shift['shiftend'], datetime):
                        shift['shiftend'] = shift['shiftend'].strftime('%Y-%m-%dT%H:%M')
                
                # Convert assigned_employee_ids string to array
                if shift['assigned_employee_ids']:
                    shift['assigned_employee_ids'] = [int(id) for id in shift['assigned_employee_ids'].split(',')]
                else:
                    shift['assigned_employee_ids'] = []
            
            # Get all employees for assignment
            cursor.execute('''
                SELECT 
                    e.employeeid,
                    e.employeename,
                    e.gender,
                    e.status as employeestatus,
                    e.age,
                    e.nationality,
                    e.passportid,
                    e.employeeenglishrating,
                    e.employeeExperienceRating,
                    er.employeerolename
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE e.status = 'Active'
                ORDER BY e.employeename
            ''')
            employees = cursor.fetchall()
            
            # Convert Decimal values to float
            event = safe_serialize(event)
            shifts = safe_serialize(shifts)
            employees = safe_serialize(employees)
            
            return render_template('events/unified/event_form.html',
                                 is_edit_mode=True,
                                 event=event,
                                 customers=customers,
                                 company=company,
                                 shifts=shifts,
                                 employees=employees)
                                 
    except Exception as e:
        flash(f'Error loading edit event form: {str(e)}', 'error')
        return redirect(url_for('event_list'))
    finally:
        if conn:
            conn.close()

@app.route('/events/<int:event_id>/edit', methods=['POST'])
@login_required
def update_event(event_id):
    """Update an existing event."""
    try:
        # Get form data
        event_name = request.form.get('EventName')
        customer_id = request.form.get('Customerid')
        event_location = request.form.get('EventLocation')
        event_start_date = request.form.get('EventStart_date')
        event_start_time = request.form.get('EventStart_time')
        event_end_date = request.form.get('EventEnd_date')
        event_end_time = request.form.get('EventEnd_time')
        notes = request.form.get('notes')
        event_stage = request.form.get('EventStage')
        waiters_needed = request.form.get('WaitersNeeded', '0')
        bartenders_needed = request.form.get('BartendersNeeded', '0')
        male_employees = request.form.get('MaleEmployees', '0')
        female_employees = request.form.get('FemaleEmployees', '0')
        
        # Calculate derived fields
        total_employees = int(waiters_needed) + int(bartenders_needed)
        
        # Parse dates and times
        event_start = None
        event_end = None
        
        if event_start_date and event_start_time:
            event_start = f"{event_start_date} {event_start_time}"
        
        if event_end_date and event_end_time:
            event_end = f"{event_end_date} {event_end_time}"
        
        # Connect to database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Update event
            cursor.execute('''
                UPDATE event
                SET 
                    EventName = %s,
                    Customerid = %s,
                    EventLocation = %s,
                    EventStart = %s,
                    EventEnd = %s,
                    notes = %s,
                    EventStage = %s,
                    WaitersNeeded = %s,
                    BartendersNeeded = %s,
                    MaleEmployees = %s,
                    FemaleEmployees = %s,
                    TotalEmployees = %s
                WHERE EventID = %s
            ''', (
                event_name,
                customer_id,
                event_location,
                event_start,
                event_end,
                notes,
                event_stage,
                waiters_needed,
                bartenders_needed,
                male_employees,
                female_employees,
                total_employees,
                event_id
            ))
            
            conn.commit()
            flash('Event updated successfully!', 'success')
            
    except Exception as e:
        flash(f'Error updating event: {str(e)}', 'error')
    
    return redirect(url_for('edit_event_unified', event_id=event_id))

@app.route('/events/create', methods=['POST'])
@login_required
def create_event():
    """Create a new event."""
    try:
        # Get form data
        event_name = request.form.get('EventName')
        customer_id = request.form.get('Customerid')
        event_location = request.form.get('EventLocation')
        event_start_date = request.form.get('EventStart_date')
        event_start_time = request.form.get('EventStart_time')
        event_end_date = request.form.get('EventEnd_date')
        event_end_time = request.form.get('EventEnd_time')
        notes = request.form.get('notes')
        event_stage = request.form.get('EventStage', 'Draft')
        waiters_needed = request.form.get('WaitersNeeded', '0')
        bartenders_needed = request.form.get('BartendersNeeded', '0')
        male_employees = request.form.get('MaleEmployees', '0')
        female_employees = request.form.get('FemaleEmployees', '0')
        
        # Calculate derived fields
        total_employees = int(waiters_needed) + int(bartenders_needed)
        
        # Parse dates and times
        event_start = None
        event_end = None
        
        if event_start_date and event_start_time:
            event_start = f"{event_start_date} {event_start_time}"
        
        if event_end_date and event_end_time:
            event_end = f"{event_end_date} {event_end_time}"
        
        # Connect to database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Insert new event
            cursor.execute('''
                INSERT INTO event (
                    EventName,
                    Customerid,
                    EventLocation,
                    EventStart,
                    EventEnd,
                    notes,
                    EventStage,
                    WaitersNeeded,
                    BartendersNeeded,
                    MaleEmployees,
                    FemaleEmployees,
                    TotalEmployees,
                    totalhours,
                    totalcost,
                    totalselling,
                    totalprofit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 0, 0)
            ''', (
                event_name,
                customer_id,
                event_location,
                event_start,
                event_end,
                notes,
                event_stage,
                waiters_needed,
                bartenders_needed,
                male_employees,
                female_employees,
                total_employees
            ))
            
            # Get the ID of the newly created event
            event_id = conn.insert_id()
            
            conn.commit()
            flash('Event created successfully!', 'success')
            
            # Redirect to edit page for the new event
            return redirect(url_for('edit_event_unified', event_id=event_id))
            
    except Exception as e:
        flash(f'Error creating event: {str(e)}', 'error')
        return redirect(url_for('create_event_page'))
    
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/shifts/add', methods=['POST'])
@login_required
def add_shift():
    """Add a new shift to an event."""
    try:
        # Get form data
        event_id = request.form.get('event_id')
        shift_name = request.form.get('shift_name')
        shift_type = request.form.get('shift_type', 'Full')  # Default to 'Full' as per the enum
        shift_start = request.form.get('shift_start')
        shift_end = request.form.get('shift_end')
        
        # Add debug logging
        logger.debug(f"Form data received: event_id={event_id}, shift_name={shift_name}, shift_type={shift_type}, shift_start={shift_start}, shift_end={shift_end}")
        logger.debug(f"All form data: {request.form}")
        
        if not event_id:
            logger.error("Event ID is missing from form data")
            flash('Event ID is required.', 'error')
            return redirect(url_for('event_list'))
        
        # Parse dates
        if shift_start:
            shift_start_datetime = datetime.strptime(shift_start, '%Y-%m-%dT%H:%M')
        else:
            flash('Shift start time is required.', 'error')
            return redirect(url_for('event_list'))
            
        if shift_end:
            shift_end_datetime = datetime.strptime(shift_end, '%Y-%m-%dT%H:%M')
        else:
            flash('Shift end time is required.', 'error')
            return redirect(url_for('event_list'))
        
        # Calculate shift duration
        # If end time is before start time, assume it's the next day
        if shift_end_datetime < shift_start_datetime:
            shift_end_datetime = shift_end_datetime + timedelta(days=1)
            
        shift_duration = (shift_end_datetime - shift_start_datetime).total_seconds() / 3600  # Duration in hours
        
        # Connect to database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if event exists
            cursor.execute('SELECT * FROM event WHERE EventID = %s', (event_id,))
            event = cursor.fetchone()
            
            if not event:
                flash('Event not found.', 'error')
                return redirect(url_for('event_list'))
            
            # Insert shift
            cursor.execute('''
                INSERT INTO shifts (
                    eventid,
                    shiftname,
                    shifttype,
                    shiftstart,
                    shiftend,
                    total_hours
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                event_id,
                shift_name,
                shift_type,
                shift_start_datetime,
                shift_end_datetime,
                shift_duration
            ))
            
            conn.commit()
            flash('Shift added successfully!', 'success')
            
    except Exception as e:
        flash(f'Error adding shift: {str(e)}', 'error')
    
    # Redirect to event edit page if we came from there
    referrer = request.referrer
    if referrer and 'edit' in referrer and str(event_id) in referrer:
        return redirect(url_for('edit_event_unified', event_id=event_id))
    
    # Otherwise, redirect to event list
    return redirect(url_for('event_list'))

@app.route('/shifts/<int:shift_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_shift(shift_id):
    """Edit an existing shift."""
    if request.method == 'POST':
        try:
            # Get form data
            shift_name = request.form.get('shiftname')
            shift_type = request.form.get('shifttype', 'Full')  # Default to 'Full' as per the enum
            shift_start = request.form.get('shiftstart')
            shift_end = request.form.get('shiftend')
            
            # Parse dates
            if shift_start:
                shift_start_datetime = datetime.strptime(shift_start, '%Y-%m-%dT%H:%M')
            else:
                flash('Shift start time is required.', 'error')
                return redirect(url_for('edit_shift', shift_id=shift_id))
                
            if shift_end:
                shift_end_datetime = datetime.strptime(shift_end, '%Y-%m-%dT%H:%M')
            else:
                flash('Shift end time is required.', 'error')
                return redirect(url_for('edit_shift', shift_id=shift_id))
            
            # If end time is before start time, assume it's the next day
            if shift_end_datetime < shift_start_datetime:
                shift_end_datetime = shift_end_datetime + timedelta(days=1)
                
            shift_duration = (shift_end_datetime - shift_start_datetime).total_seconds() / 3600  # Duration in hours
            
            # Connect to database
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                # Check if shift exists
                cursor.execute('SELECT * FROM shifts WHERE shiftid = %s', (shift_id,))
                shift = cursor.fetchone()
                
                if not shift:
                    flash('Shift not found.', 'error')
                    return redirect(url_for('event_list'))
                
                # Update shift
                cursor.execute('''
                    UPDATE shifts
                    SET 
                        shiftname = %s,
                        shifttype = %s,
                        shiftstart = %s,
                        shiftend = %s,
                        total_hours = %s
                    WHERE shiftid = %s
                ''', (
                    shift_name,
                    shift_type,
                    shift_start_datetime,
                    shift_end_datetime,
                    shift_duration,
                    shift_id
                ))
                
                conn.commit()
                flash('Shift updated successfully!', 'success')
                
                # Redirect to event edit page
                return redirect(url_for('edit_event_unified', event_id=shift['eventid']))
                
        except Exception as e:
            flash(f'Error updating shift: {str(e)}', 'error')
            return redirect(url_for('edit_shift', shift_id=shift_id))
    
    # GET request - show edit form
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get shift details
            cursor.execute('''
                SELECT 
                    s.*,
                    e.EventName
                FROM shifts s
                LEFT JOIN event e ON s.eventid = e.EventID
                WHERE s.shiftid = %s
            ''', (shift_id,))
            
            shift = cursor.fetchone()
            if not shift:
                flash('Shift not found.', 'error')
                return redirect(url_for('event_list'))
            
            return render_template('shifts/edit.html',
                                 shift=shift)
                                 
    except Exception as e:
        flash(f'Error loading shift: {str(e)}', 'error')
        return redirect(url_for('event_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/shifts/<int:shift_id>/delete', methods=['POST'])
@login_required
def delete_shift(shift_id):
    """Delete a shift."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get shift details
            cursor.execute('SELECT * FROM shifts WHERE shiftid = %s', (shift_id,))
            shift = cursor.fetchone()
            
            if not shift:
                return jsonify({'success': False, 'message': 'Shift not found.'}), 404
            
            event_id = shift['eventid']
            
            # Check if shift has assigned employees
            cursor.execute('SELECT COUNT(*) as count FROM employee_shifts WHERE shiftid = %s', (shift_id,))
            count = cursor.fetchone()['count']
            
            if count > 0:
                # First remove employee assignments
                cursor.execute('DELETE FROM employee_shifts WHERE shiftid = %s', (shift_id,))
            
            # Delete shift
            cursor.execute('DELETE FROM shifts WHERE shiftid = %s', (shift_id,))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Shift deleted successfully!',
                'event_id': event_id
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/delete_shift_manage', methods=['POST'])
@login_required
def delete_shift_manage():
    """Delete a shift from the manage shifts page."""
    shift_id = request.form.get('shift_id')
    event_id = request.form.get('event_id')
    
    if not shift_id:
        flash('Shift ID is required.', 'error')
        return redirect(url_for('manage_all_shifts', event_id=event_id))
    
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # First delete related employee assignments
            cursor.execute('DELETE FROM employee_shifts WHERE shiftid = %s', (shift_id,))
            
            # Then delete the shift
            cursor.execute('DELETE FROM shifts WHERE shiftid = %s', (shift_id,))
            
            conn.commit()
            
            flash('Shift deleted successfully.', 'success')
            
    except Exception as e:
        flash(f'Error deleting shift: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('manage_all_shifts', event_id=event_id))



@app.route('/create_event_submit_unified', methods=['POST'])
@login_required
def create_event_submit_unified():
    """Handle the form submission for creating a new event."""
    try:
        # Get form data
        event_name = request.form.get('EventName')
        customer_id = request.form.get('Customerid')
        event_location = request.form.get('EventLocation')
        event_start = request.form.get('EventStart')
        event_end = request.form.get('EventEnd')
        notes = request.form.get('notes', '')
        event_stage = request.form.get('EventStage', 'Draft')
        waiters_needed = request.form.get('WaitersNeeded', '0')
        bartenders_needed = request.form.get('BartendersNeeded', '0')
        male_employees = request.form.get('MaleEmployees', '0')
        female_employees = request.form.get('FemaleEmployees', '0')
        
        # Get financial data
        event_per_hour_cost = request.form.get('EventPerHourcost', '0')
        event_per_hour_selling = request.form.get('EventPerHourselling', '0')
        total_hours = request.form.get('totalhours', '0')
        total_cost = request.form.get('totalcost', '0')
        total_selling = request.form.get('totalselling', '0')
        
        # Calculate derived fields
        total_employees = int(waiters_needed) + int(bartenders_needed)
        
        # Calculate totalprofit based on totalselling and totalcost
        try:
            total_cost = float(total_cost)
            total_selling = float(total_selling)
            # Use round to 2 decimal places to avoid floating point precision issues
            total_profit = round(total_selling - total_cost, 2) 
        except ValueError:
            total_profit = 0
        
        # Connect to database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Create event
            cursor.execute('''
                INSERT INTO event (
                    EventName,
                    Customerid,
                    EventLocation,
                    EventStart,
                    EventEnd,
                    notes,
                    EventStage,
                    WaitersNeeded,
                    BartendersNeeded,
                    MaleEmployees,
                    FemaleEmployees,
                    TotalEmployees,
                    EventPerHourcost,
                    EventPerHourselling,
                    totalhours,
                    totalcost,
                    totalselling,
                    totalprofit
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            ''', (
                event_name,
                customer_id,
                event_location,
                event_start,
                event_end,
                notes,
                event_stage,
                waiters_needed,
                bartenders_needed,
                male_employees,
                female_employees,
                total_employees,
                event_per_hour_cost,
                event_per_hour_selling,
                total_hours,
                total_cost,
                total_selling,
                total_profit
            ))
            
            # Get the new event ID
            event_id = cursor.lastrowid
            
            # Handle shifts data if provided
            shifts_data = request.form.get('shifts_data')
            if shifts_data:
                shifts = json.loads(shifts_data)
                for shift in shifts:
                    # Only process add operations for new events
                    if shift.get('operation') == 'add':
                        cursor.execute('''
                            INSERT INTO shifts (
                                eventid, shiftname, shifttype, shiftstart, shiftend, total_hours
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (
                            event_id,
                            shift.get('name', 'New Shift'),
                            shift.get('type', 'Full'),
                            shift.get('start'),
                            shift.get('end'),
                            shift.get('hours', 0)
                        ))
            
            conn.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('edit_event_unified', event_id=event_id))
            
    except Exception as e:
        flash(f'Error creating event: {str(e)}', 'error')
        if 'conn' in locals() and conn:
            conn.rollback()
        return redirect(url_for('create_event_page'))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%dT%H:%M'):
    """Format a datetime object for display in HTML datetime-local input."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M')
            except ValueError:
                return value
    if isinstance(value, datetime):
        return value.strftime(format)
    return ""

@app.template_filter('format_hours')
def format_hours(value):
    """Format decimal hours as HH:MM."""
    if value is None:
        return "0:00"
    
    # If value is a string, convert to float
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return "0:00"
    
    # Calculate hours and minutes
    hours = int(value)
    minutes = int((value - hours) * 60)
    
    return f"{hours}:{minutes:02d}"

@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML breaks."""
    if not value:
        return ""
    return value.replace('\n', '<br>')

@app.route('/manage_all_shifts')
@login_required
def manage_all_shifts():
    """Display a page to manage all shifts for an event."""
    event_id = request.args.get('event_id')
    if not event_id:
        app.logger.error('Event ID is missing from manage_all_shifts request')
        flash('Event ID is required.', 'error')
        return redirect(url_for('event_list'))
        
    try:
        app.logger.info(f'Loading shifts for event {event_id}')
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get event details
            cursor.execute('''
                SELECT 
                    e.*,
                    c.customername
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                WHERE e.EventID = %s
            ''', (event_id,))
            
            event = cursor.fetchone()
            if not event:
                app.logger.error(f'Event not found: {event_id}')
                flash('Event not found.', 'error')
                return redirect(url_for('event_list'))
            
            # Get shifts for this event
            cursor.execute('''
                SELECT 
                    s.*,
                    COUNT(es.employeeid) as assigned_employees_count,
                    SUM(es.hours) as total_assigned_hours
                FROM shifts s
                LEFT JOIN employee_shifts es ON s.shiftid = es.shiftid
                WHERE s.eventid = %s
                GROUP BY s.shiftid
                ORDER BY s.shiftstart
            ''', (event_id,))
            
            shifts = cursor.fetchall()
            
            # Get all employees
            cursor.execute('''
                SELECT 
                    e.employeeid,
                    e.employeename,
                    e.gender,
                    er.employeerolename
                FROM employee e
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
                WHERE e.status = 'Active'
                ORDER BY e.employeename
            ''')
            
            employees = cursor.fetchall()
            
            app.logger.info(f'Successfully loaded shifts for event {event_id}')
            return render_template('events/manage_shifts.html',
                                  event=event,
                                  shifts=shifts,
                                  employees=employees)
            
    except Exception as e:
        app.logger.error(f'Error in manage_all_shifts: {str(e)}')
        flash(f'Error loading shifts: {str(e)}', 'error')
        return redirect(url_for('event_list'))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/event_invoices/<int:event_id>')
@login_required
def event_invoices(event_id):
    """Display invoices related to a specific event."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get event details
            cursor.execute('''
                SELECT 
                    e.*,
                    c.customerid,
                    c.customername,
                    c.customerphone,
                    c.customeremail
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                WHERE e.EventID = %s
            ''', (event_id,))
            
            event = cursor.fetchone()
            if not event:
                flash('Event not found.', 'error')
                return redirect(url_for('event_list'))
            
            # Convert string dates to datetime objects
            if 'EventStart' in event and event['EventStart'] and isinstance(event['EventStart'], str):
                try:
                    event['EventStart'] = datetime.strptime(event['EventStart'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        event['EventStart'] = datetime.strptime(event['EventStart'], '%Y-%m-%d %H:%M')
                    except ValueError:
                        event['EventStart'] = None
            
            if 'EventEnd' in event and event['EventEnd'] and isinstance(event['EventEnd'], str):
                try:
                    event['EventEnd'] = datetime.strptime(event['EventEnd'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        event['EventEnd'] = datetime.strptime(event['EventEnd'], '%Y-%m-%d %H:%M')
                    except ValueError:
                        event['EventEnd'] = None
            
            # Get invoices related to this event
            cursor.execute('''
                SELECT 
                    i.*,
                    c.customername
                FROM invoice i
                LEFT JOIN customer c ON i.customer_id = c.customerid
                WHERE i.event_id = %s
                ORDER BY i.invoice_date DESC
            ''', (event_id,))
            
            invoices = cursor.fetchall()
            
            # Convert decimal values to float and dates to datetime objects
            for invoice in invoices:
                if 'total' in invoice and invoice['total'] is not None:
                    invoice['total'] = float(invoice['total'])
                else:
                    invoice['total'] = 0.0
                    
                if 'invoice_date' in invoice and invoice['invoice_date'] and isinstance(invoice['invoice_date'], str):
                    try:
                        invoice['invoice_date'] = datetime.strptime(invoice['invoice_date'], '%Y-%m-%d')
                    except ValueError:
                        invoice['invoice_date'] = None
                        
                if 'due_date' in invoice and invoice['due_date'] and isinstance(invoice['due_date'], str):
                    try:
                        invoice['due_date'] = datetime.strptime(invoice['due_date'], '%Y-%m-%d')
                    except ValueError:
                        invoice['due_date'] = None
            
            # Create customer object from event data for the template
            customer = {
                'customerid': event.get('customerid'),
                'customername': event.get('customername', 'Unknown Customer')
            }
            
            return render_template('events/invoices.html',
                                 event=event,
                                 invoices=invoices,
                                 customer=customer)
                                 
    except Exception as e:
        flash(f'Error loading event invoices: {str(e)}', 'error')
        return redirect(url_for('event_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/new_invoice')
@login_required
def new_invoice():
    """Display the form to create a new invoice, optionally pre-filled with event data."""
    try:
        # Get optional event_id from query parameters
        event_id = request.args.get('event_id')
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get customers for dropdown
            cursor.execute('SELECT customerid, customername FROM customer ORDER BY customername')
            customers = cursor.fetchall()
            
            # Get events for dropdown
            cursor.execute('''
                SELECT 
                    e.EventID, 
                    e.EventName,
                    e.totalhours,
                    e.EventPerHourselling,
                    e.totalselling,
                    c.customername 
                FROM event e
                LEFT JOIN customer c ON e.Customerid = c.customerid
                ORDER BY e.EventStart DESC
            ''')
            events = cursor.fetchall()
            
            # Get company details
            cursor.execute('SELECT * FROM company LIMIT 1')
            company = cursor.fetchone()
            
            # Generate next invoice number
            cursor.execute('SELECT MAX(CAST(SUBSTRING(invoice_number, 4) AS UNSIGNED)) as max_num FROM invoice WHERE invoice_number LIKE "INV%"')
            max_num = cursor.fetchone()['max_num']
            next_num = 1 if not max_num else max_num + 1
            next_invoice_number = f"INV{next_num:04d}"
            
            # Create datetime objects for invoice dates
            invoice_date = datetime.now()
            due_date = datetime.now() + timedelta(days=30)
            
            # Initialize invoice object with default values
            invoice = {
                'invoice_number': next_invoice_number,
                'invoice_date': invoice_date,
                'due_date': due_date,
                'status': 'Draft',
                'vat_rate': 19,  # Default VAT rate
                'notes': '',
                'subtotal': 0,
                'vat_amount': 0,
                'total': 0,
                'customer_id': None,
                'event_id': event_id if event_id else None,
                'items': []
            }
            
            selected_event = None
            selected_customer = None
            
            # If event_id was provided, get that event's details
            if event_id:
                cursor.execute('''
                    SELECT 
                        e.*,
                        c.customerid,
                        c.customername,
                        c.customeraddress,
                        c.customerphone,
                        c.customeremail
                    FROM event e
                    LEFT JOIN customer c ON e.Customerid = c.customerid
                    WHERE e.EventID = %s
                ''', (event_id,))
                selected_event = cursor.fetchone()
                
                if selected_event:
                    # Pre-fill invoice with event data
                    invoice['customer_id'] = selected_event['Customerid']
                    invoice['event_id'] = selected_event['EventID']
                    selected_customer = {
                        'customerid': selected_event['Customerid'],
                        'customername': selected_event['customername']
                    }
                    
                    # Convert datetime objects to strings for JSON serialization
                    for key, value in selected_event.items():
                        if isinstance(value, datetime):
                            selected_event[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        
        # Format dates as strings
        invoice['invoice_date'] = invoice['invoice_date'].strftime('%Y-%m-%d')
        invoice['due_date'] = invoice['due_date'].strftime('%Y-%m-%d')
        
        return render_template(
            'invoices/form.html',
            title='Create Invoice',
            invoice=invoice,
            customers=customers,
            events=events,
            company=company,
            selected_event=selected_event,
            selected_customer=selected_customer,
            mode='create',
            items=[]
        )
    
    except Exception as e:
        print(f"Error loading new invoice form: {str(e)}")
        flash(f"Error loading new invoice form: {str(e)}", 'error')
        return redirect(url_for('invoice_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/shift_assignments/<int:shift_id>')
@login_required
def get_shift_assignments(shift_id):
    """Get employee assignments for a shift."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get shift details
            cursor.execute('''
                SELECT 
                    s.*,
                    e.EventName
                FROM shifts s
                LEFT JOIN event e ON s.eventid = e.EventID
                WHERE s.shiftid = %s
            ''', (shift_id,))
            
            shift = cursor.fetchone()
            if not shift:
                return jsonify({'success': False, 'error': 'Shift not found'}), 404
            
            # Get assigned employees
            cursor.execute('''
                SELECT 
                    e.*,
                    es.hours
                FROM employee e
                INNER JOIN employee_shifts es ON e.employeeid = es.employeeid
                WHERE es.shiftid = %s
                ORDER BY e.employeename
            ''', (shift_id,))
            
            employees = cursor.fetchall()
            
            # Convert hours to HH:MM format
            for emp in employees:
                if emp['hours'] is not None:
                    hours = int(emp['hours'])
                    minutes = int((emp['hours'] - hours) * 60)
                    emp['hours'] = f"{hours:02d}:{minutes:02d}"
            
            return jsonify({
                'success': True,
                'shift': shift,
                'employees': employees
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/save_shift_assignments', methods=['POST'])
@login_required
def save_shift_assignments():
    """Save employee assignments for a shift."""
    try:
        shift_id = request.form.get('shift_id')
        event_id = request.form.get('event_id')
        
        if not shift_id:
            return jsonify({'success': False, 'error': 'Shift ID is required'}), 400
        if not event_id:
            return jsonify({'success': False, 'error': 'Event ID is required'}), 400

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # Verify shift belongs to event
            cursor.execute('''
                SELECT shiftid FROM shifts 
                WHERE shiftid = %s AND eventid = %s
            ''', (shift_id, event_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Invalid shift or event ID'}), 400

            # Start transaction
            conn.begin()

            try:
                # Handle explicit removals first
                remove_employees = request.form.getlist('remove_employees[]')
                if remove_employees:
                    placeholders = ','.join(['%s'] * len(remove_employees))
                    cursor.execute(f'''
                        DELETE FROM employee_shifts 
                        WHERE shiftid = %s AND employeeid IN ({placeholders})
                    ''', [shift_id] + remove_employees)
                    
                    # Update earnings for removed employees
                    for emp_id in remove_employees:
                        cursor.execute("CALL update_employee_event_earnings_for_shift(%s, %s)", 
                                     (emp_id, event_id))

                # Handle existing assignments updates
                for key, value in request.form.items():
                    if key.startswith('hours_'):
                        employee_id = key.split('_')[1]
                        try:
                            hours = float(value) if value else 0
                            
                            if hours > 0:
                                # Update existing assignment
                                cursor.execute('''
                                    UPDATE employee_shifts 
                                    SET hours = %s 
                                    WHERE shiftid = %s AND employeeid = %s
                                ''', (hours, shift_id, employee_id))
                            else:
                                # Remove assignment if hours is 0
                                cursor.execute('''
                                    DELETE FROM employee_shifts 
                                    WHERE shiftid = %s AND employeeid = %s
                                ''', (shift_id, employee_id))
                            
                            # Update earnings for this employee
                            cursor.execute("CALL update_employee_event_earnings_for_shift(%s, %s)", 
                                         (employee_id, event_id))
                        except ValueError:
                            raise ValueError(f'Invalid hours value for employee {employee_id}')

                # Handle new assignments
                new_employees = request.form.getlist('selected_employees[]')
                new_hours = request.form.get('new_hours', '0')
                
                if new_employees:
                    try:
                        hours = float(new_hours)
                        for employee_id in new_employees:
                            if hours > 0:
                                cursor.execute('''
                                    INSERT INTO employee_shifts (shiftid, employeeid, hours)
                                    VALUES (%s, %s, %s)
                                ''', (shift_id, employee_id, hours))
                                
                                # Update earnings for new employee
                                cursor.execute("CALL update_employee_event_earnings_for_shift(%s, %s)", 
                                             (employee_id, event_id))
                    except ValueError:
                        raise ValueError('Invalid hours value for new employee')

                # Commit transaction
                conn.commit()
                return jsonify({'success': True})

            except Exception as e:
                # Rollback transaction on error
                conn.rollback()
                return jsonify({'success': False, 'error': str(e)}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Route removed to avoid conflicts

@app.route('/events/<int:event_id>/update_financials', methods=['POST'])
@login_required
def update_event_financials(event_id):
    """API endpoint to update financial information for an event."""
    try:
        data = request.json
        totalhours = float(data.get('totalhours', 0))
        totalcost = float(data.get('totalcost', 0)) 
        totalselling = float(data.get('totalselling', 0))
        
        # Calculate totalprofit based on totalselling and totalcost
        # Using round to 2 decimal places to avoid floating point precision issues
        totalprofit = round(totalselling - totalcost, 2)
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Update the event's financial information in the database
            cursor.execute('''
                UPDATE event
                SET 
                    totalhours = %s,
                    totalcost = %s,
                    totalselling = %s,
                    totalprofit = %s
                WHERE EventID = %s
            ''', (totalhours, totalcost, totalselling, totalprofit, event_id))
            
            conn.commit()
            
            # After updating, retrieve the updated values to verify they were stored correctly
            cursor.execute('''
                SELECT totalcost, totalselling, totalprofit
                FROM event
                WHERE EventID = %s
            ''', (event_id,))
            
            updated_event = cursor.fetchone()
            
            # Return the updated values to ensure consistency
            return jsonify({
                'success': True, 
                'updated_values': {
                    'totalcost': float(updated_event['totalcost']),
                    'totalselling': float(updated_event['totalselling']),
                    'totalprofit': float(updated_event['totalprofit'])
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice/<int:invoice_id>/pdf')
@login_required
def invoice_pdf(invoice_id):
    """Generate PDF for an invoice."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get invoice details
            cursor.execute('''
                SELECT 
                    i.*,
                    c.CustomerName,
                    c.CustomerAddress,
                    c.CustomerPhone,
                    c.CustomerEmail
                FROM invoice i
                LEFT JOIN customer c ON i.Customerid = c.Customerid
                WHERE i.InvoiceID = %s
            ''', (invoice_id,))
            
            invoice = cursor.fetchone()
            if not invoice:
                flash('Invoice not found.', 'error')
                return redirect(url_for('invoice_list'))
            
            # Get invoice items
            cursor.execute('''
                SELECT *
                FROM invoice_items
                WHERE InvoiceID = %s
                ORDER BY ItemID
            ''', (invoice_id,))
            
            items = cursor.fetchall()
            
            # Generate PDF
            pdf = generate_invoice_pdf(invoice, items)
            
            # Save PDF to file
            pdf_path = os.path.join(app.static_folder, 'invoices', f'invoice_{invoice_id}.pdf')
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            pdf.output(pdf_path)
            
            return send_file(pdf_path, as_attachment=True, download_name=f'invoice_{invoice_id}.pdf')
            
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('invoice_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice/<int:invoice_id>/send', methods=['GET', 'POST'])
@login_required
def send_invoice_email(invoice_id):
    """Send invoice to client via email."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get invoice details with customer information
            cursor.execute('''
                SELECT 
                    i.*,
                    c.customername,
                    c.customeraddress,
                    c.customerphone,
                    c.customeremail,
                    e.EventName as event_name
                FROM invoice i
                LEFT JOIN customer c ON i.customer_id = c.customerid
                LEFT JOIN event e ON i.event_id = e.EventID
                WHERE i.invoice_id = %s
            ''', (invoice_id,))
            invoice = cursor.fetchone()
            
            if not invoice:
                flash('Invoice not found', 'error')
                return redirect(url_for('invoice_list'))
            
            # Get invoice items
            cursor.execute('SELECT * FROM invoice_item WHERE invoice_id = %s', (invoice_id,))
            items = cursor.fetchall()
            
            # Get company details for the email
            cursor.execute('SELECT * FROM company LIMIT 1')
            company = cursor.fetchone()
            
            # Get email settings
            cursor.execute('SELECT * FROM email_settings LIMIT 1')
            email_settings = cursor.fetchone()
            
            if request.method == 'POST':
                # Process email sending
                recipient_email = request.form.get('recipient_email', invoice['customeremail'])
                subject = request.form.get('subject', f"Invoice {invoice['invoice_number']} from {company['companyname']}")
                message = request.form.get('message', '')
                include_pdf = 'include_pdf' in request.form
                
                # Generate invoice URL for viewing online
                invoice_url = url_for('invoice_view', invoice_id=invoice_id, _external=True)
                
                # Create PDF invoice if needed
                pdf_content = None
                pdf_path = None
                pdf_filename = f"Invoice_{invoice['invoice_number']}.pdf"
                temp_dir = os.path.join(os.getcwd(), 'temp')
                
                # Make sure temp directory exists
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                
                if include_pdf:
                    try:
                        # Generate HTML content for PDF
                        html_content = render_template(
                            'invoices/pdf.html',
                            invoice=invoice,
                            items=items,
                            company=company
                        )
                        
                        # Save HTML to temp file
                        html_path = os.path.join(temp_dir, f"invoice_{invoice_id}.html")
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        # Try to use pdfkit if available (requires wkhtmltopdf installed)
                        pdf_path = os.path.join(temp_dir, pdf_filename)
                        try:
                            import pdfkit
                            config = pdfkit.configuration()
                            pdfkit.from_file(html_path, pdf_path, configuration=config)
                        except (ImportError, Exception) as e:
                            # If pdfkit fails, just use the HTML file
                            pdf_path = html_path
                            pdf_filename = f"Invoice_{invoice['invoice_number']}.html"
                            print(f"Falling back to HTML file: {str(e)}")
                        
                        # Read the file contents for direct email sending
                        with open(pdf_path, 'rb') as f:
                            pdf_content = f.read()
                        
                    except Exception as e:
                        flash(f'Error generating PDF: {str(e)}', 'warning')
                        print(f"PDF generation error: {str(e)}")
                        pdf_content = None
                        pdf_path = None
                
                # Check if direct sending is enabled and configured
                if email_settings and email_settings['direct_send']:
                    # Set up email content
                    html_email = render_template(
                        'emails/invoice_email.html',
                        invoice=invoice,
                        company=company,
                        message=message.replace('\n', '<br>'),  # Convert newlines to HTML breaks
                        invoice_url=invoice_url
                    )
                    
                    # Determine which method to use (SMTP or Exchange)
                    server_type = email_settings.get('server_type', 'smtp')
                    
                    if server_type == 'exchange' and email_settings['exchange_server'] and email_settings['username']:
                        try:
                            # Check if pywin32 is installed
                            try:
                                import win32com.client
                                import pythoncom
                            except ImportError:
                                flash('Microsoft Exchange/Outlook integration requires pywin32. Please install it with: pip install pywin32', 'error')
                                return render_template(
                                    'invoices/email_form.html',
                                    invoice=invoice,
                                    items=items,
                                    company=company,
                                    email_settings=email_settings,
                                    recipient_email=recipient_email,
                                    subject=subject,
                                    message=message,
                                    error="pywin32 module is not installed"
                                )
                            
                            # Initialize COM for this thread
                            pythoncom.CoInitialize()
                            
                            try:
                                # Use Outlook COM objects to send email via Exchange
                                outlook = win32com.client.Dispatch('Outlook.Application')
                                mail = outlook.CreateItem(0)  # 0 = olMailItem
                                
                                mail.Subject = subject
                                mail.To = recipient_email
                                mail.HTMLBody = html_email
                                
                                # Add PDF attachment if needed
                                if include_pdf and pdf_path:
                                    mail.Attachments.Add(pdf_path)
                                
                                # Send or display based on setting
                                mail.Send()
                                
                                # Update invoice status to 'Sent'
                                cursor.execute('UPDATE invoice SET status = %s WHERE invoice_id = %s', ('Sent', invoice_id))
                                conn.commit()
                                
                                # Update event status to 'Completed' if there's an associated event
                                if invoice['event_id']:
                                    cursor.execute('UPDATE event SET EventStage = %s WHERE EventID = %s', ('Completed', invoice['event_id']))
                                    conn.commit()
                                    flash(f'Event status updated to Completed', 'success')
                                
                                flash(f'Email sent to {recipient_email} via Outlook/Exchange', 'success')
                                return redirect(url_for('invoice_view', invoice_id=invoice_id))
                            finally:
                                # Make sure to uninitialize COM when done
                                pythoncom.CoUninitialize()
                            
                        except Exception as e:
                            flash(f'Error sending email via Exchange: {str(e)}', 'error')
                            return render_template(
                                'invoices/email_form.html',
                                invoice=invoice,
                                items=items,
                                company=company,
                                email_settings=email_settings,
                                recipient_email=recipient_email,
                                subject=subject,
                                message=message,
                                error=f"Exchange send failed: {str(e)}"
                            )
                    
                    else:  # SMTP
                        # Check if SMTP settings are configured
                        if (email_settings['smtp_server'] and 
                            (not email_settings['auth_required'] or 
                             (email_settings['username'] and email_settings['password']))):
                            try:
                                import smtplib
                                from email.mime.multipart import MIMEMultipart
                                from email.mime.text import MIMEText
                                from email.mime.base import MIMEBase
                                from email import encoders
                                
                                # Create message
                                msg = MIMEMultipart('alternative')
                                msg['Subject'] = subject
                                msg['From'] = f"{email_settings['from_name']} <{email_settings['from_email']}>"
                                msg['To'] = recipient_email
                                
                                # Add HTML and plain text parts
                                # Convert the HTML message to plain text by stripping tags
                                plain_text = message.replace('<br>', '\n')
                                part1 = MIMEText(plain_text, 'plain')
                                part2 = MIMEText(html_email, 'html')
                                
                                # The last part attached is the preferred format
                                msg.attach(part1)  # First attach plain text (fallback)
                                msg.attach(part2)  # Then attach HTML (preferred)
                                
                                # Attach PDF if needed
                                if include_pdf and pdf_content:
                                    attachment = MIMEBase('application', 'octet-stream')
                                    attachment.set_payload(pdf_content)
                                    encoders.encode_base64(attachment)
                                    attachment.add_header(
                                        'Content-Disposition', 
                                        f'attachment; filename="{pdf_filename}"'
                                    )
                                    msg.attach(attachment)
                                
                                # Setup SMTP server
                                if email_settings['use_ssl']:
                                    smtp = smtplib.SMTP_SSL(email_settings['smtp_server'], email_settings['smtp_port'])
                                else:
                                    smtp = smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port'])
                                
                                if email_settings['use_tls']:
                                    smtp.starttls()
                                
                                if email_settings['auth_required']:
                                    smtp.login(email_settings['username'], email_settings['password'])
                                
                                # Send email
                                smtp.send_message(msg)
                                smtp.quit()
                                
                                # Update invoice status to 'Sent'
                                cursor.execute('UPDATE invoice SET status = %s WHERE invoice_id = %s', ('Sent', invoice_id))
                                conn.commit()
                                
                                # Update event status to 'Completed' if there's an associated event
                                if invoice['event_id']:
                                    cursor.execute('UPDATE event SET EventStage = %s WHERE EventID = %s', ('Completed', invoice['event_id']))
                                    conn.commit()
                                    flash(f'Event status updated to Completed', 'success')
                                
                                flash(f'Email sent to {recipient_email} via SMTP', 'success')
                                return redirect(url_for('invoice_view', invoice_id=invoice_id))
                                
                            except Exception as e:
                                flash(f'Error sending email via SMTP: {str(e)}', 'error')
                                return render_template(
                                    'invoices/email_form.html',
                                    invoice=invoice,
                                    items=items,
                                    company=company,
                                    email_settings=email_settings,
                                    recipient_email=recipient_email,
                                    subject=subject,
                                    message=message,
                                    error=f"SMTP send failed: {str(e)}"
                                )
                        else:
                            flash('SMTP settings are not fully configured. Please update them in Admin → Email Settings', 'warning')
                
                # If direct sending is disabled or failed, open in default email client
                desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
                
                # Save PDF to desktop for manual attachment
                if include_pdf and pdf_path:
                    desktop_file_path = os.path.join(desktop_path, pdf_filename)
                    try:
                        import shutil
                        shutil.copy2(pdf_path, desktop_file_path)
                        flash(f'Invoice saved to your desktop as {pdf_filename}', 'success')
                    except Exception as e:
                        flash(f'Could not save invoice to desktop: {str(e)}', 'warning')
                        desktop_file_path = None
                else:
                    desktop_file_path = None
                
                # Create email mailto link for the client's default email program
                import urllib.parse
                mailto_link = f"mailto:{recipient_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(message)}"
                
                # Update invoice status to 'Sent'
                cursor.execute('UPDATE invoice SET status = %s WHERE invoice_id = %s', ('Sent', invoice_id))
                conn.commit()
                
                # Update event status to 'Completed' if there's an associated event
                if invoice['event_id']:
                    cursor.execute('UPDATE event SET EventStage = %s WHERE EventID = %s', ('Completed', invoice['event_id']))
                    conn.commit()
                    flash(f'Event status updated to Completed', 'success')
                
                flash('Preparing to open your default email client...', 'info')
                return render_template(
                    'invoices/email_sent.html',
                    invoice=invoice,
                    recipient_email=recipient_email,
                    mailto_link=mailto_link,
                    pdf_saved=desktop_file_path is not None,
                    pdf_path=desktop_file_path
                )
            
            # GET request - show the email form
            return render_template(
                'invoices/email_form.html',
                invoice=invoice,
                items=items,
                company=company,
                email_settings=email_settings,
                recipient_email=invoice['customeremail'],
                subject=f"Invoice {invoice['invoice_number']} from {company['companyname'] if company else 'our company'}",
                message=f"Dear {invoice['customername']},\n\nPlease find attached the invoice {invoice['invoice_number']} for {invoice['event_name'] if invoice['event_name'] else 'our services'}.\n\nTotal amount: {invoice['total']} EUR\nDue date: {invoice['due_date'].strftime('%d.%m.%Y') if invoice['due_date'] else 'N/A'}\n\nPlease contact us if you have any questions.\n\nBest regards,\n{company['companyname'] if company else 'Our Company'}"
            )
        
    except Exception as e:
        flash(f'Error preparing invoice email: {str(e)}', 'error')
        return redirect(url_for('invoice_view', invoice_id=invoice_id))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/admin/email_settings')
@login_required
def admin_email_settings():
    # Check for admin privileges
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    # Get email settings
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    cursor = connection.cursor()
    
    try:
        # Get email settings
        cursor.execute('SELECT * FROM email_settings LIMIT 1')
        email_settings = cursor.fetchone()
        
        # Create default settings if none exist
        if not email_settings:
            try:
                # Insert default settings with Exchange/Outlook enabled
                cursor.execute('''
                    INSERT INTO email_settings (
                        server_type, direct_send, exchange_server, smtp_server, 
                        smtp_port, use_ssl, use_tls, auth_required
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    'exchange',  # Set Exchange as default
                    1,           # Enable direct send
                    'outlook.office365.com',  # Default Exchange server
                    'smtp-mail.outlook.com',  # Default SMTP server as fallback
                    587, 0, 1, 0  # Default SMTP settings as fallback
                ))
                connection.commit()
                
                # Fetch the new settings
                cursor.execute('SELECT * FROM email_settings LIMIT 1')
                email_settings = cursor.fetchone()
                
                flash('Default email settings created with Outlook/Exchange configuration', 'info')
            except Exception as e:
                flash(f'Error creating default email settings: {str(e)}', 'error')
        
        # Get company info for defaults
        cursor.execute('SELECT * FROM company LIMIT 1')
        company = cursor.fetchone()
        
        return render_template('admin/email_settings.html', 
                              email_settings=email_settings,
                              company=company)
    except Exception as e:
        flash(f'Error loading email settings: {str(e)}', 'error')
        return render_template('admin/email_settings.html', 
                              email_settings=None,
                              company=None)
    finally:
        cursor.close()
        connection.close()

@app.route('/admin/email_settings/update', methods=['POST'])
@login_required
def admin_email_settings_update():
    # Check for admin privileges
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    # Get form data
    smtp_server = request.form.get('smtp_server')
    smtp_port = request.form.get('smtp_port', 587)
    use_ssl = 1 if request.form.get('use_ssl') else 0
    use_tls = 1 if request.form.get('use_tls') else 0
    auth_required = 1 if request.form.get('auth_required') else 0
    username = request.form.get('username')
    password = request.form.get('password')
    from_email = request.form.get('from_email')
    from_name = request.form.get('from_name')
    direct_send = 1 if request.form.get('direct_send') else 0
    server_type = request.form.get('server_type', 'smtp')
    exchange_server = request.form.get('exchange_server')
    
    # For Outlook integration, we don't necessarily need username/password 
    # since we're using the local Outlook instance
    if server_type == 'exchange':
        # Set some reasonable defaults for Exchange
        if not exchange_server:
            exchange_server = 'outlook.office365.com'
    
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    cursor = connection.cursor()
    
    try:
        # Check if record exists
        cursor.execute('SELECT COUNT(*) as count FROM email_settings')
        count = cursor.fetchone()['count']
        
        if count > 0:
            # Update existing record
            cursor.execute('''
                UPDATE email_settings SET 
                smtp_server = %s, 
                smtp_port = %s,
                use_ssl = %s,
                use_tls = %s,
                auth_required = %s,
                username = %s,
                password = %s,
                from_email = %s,
                from_name = %s,
                direct_send = %s,
                server_type = %s,
                exchange_server = %s
                WHERE id = (SELECT id FROM (SELECT id FROM email_settings LIMIT 1) as t)
            ''', (
                smtp_server, smtp_port, use_ssl, use_tls, auth_required, 
                username, password, from_email, from_name, direct_send,
                server_type, exchange_server
            ))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO email_settings (
                    smtp_server, smtp_port, use_ssl, use_tls, auth_required,
                    username, password, from_email, from_name, direct_send,
                    server_type, exchange_server
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                smtp_server, smtp_port, use_ssl, use_tls, auth_required, 
                username, password, from_email, from_name, direct_send,
                server_type, exchange_server
            ))
        
        connection.commit()
        flash('Email settings updated successfully', 'success')
    except Exception as e:
        connection.rollback()
        flash(f'Error updating email settings: {str(e)}', 'error')
        
    try:
        # Get updated email settings
        cursor.execute('SELECT * FROM email_settings LIMIT 1')
        email_settings = cursor.fetchone()
        
        # Get company info for defaults
        cursor.execute('SELECT * FROM company LIMIT 1')
        company = cursor.fetchone()
        
        return render_template('admin/email_settings.html', 
                            email_settings=email_settings,
                            company=company)
    except Exception as e:
        flash(f'Error loading email settings: {str(e)}', 'error')
        return render_template('admin/email_settings.html')
    finally:
        cursor.close()
        connection.close()

@app.route('/admin/email_settings/test_connection', methods=['POST'])
@login_required
def test_email_connection():
    # Check for admin privileges
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Access denied. Admin privileges required.'})
    
    # Get form data
    server_type = request.form.get('server_type', 'smtp')
    
    result = {'success': False, 'message': ''}
    
    try:
        if server_type == 'exchange':
            # Test Outlook connection - we're using the local Outlook instance
            try:
                import win32com.client
                import pythoncom
                
                # Initialize COM for this thread
                pythoncom.CoInitialize()
                
                try:
                    # Try to create Outlook object
                    outlook = win32com.client.Dispatch('Outlook.Application')
                    
                    # Check if we can create a mail item
                    mail = outlook.CreateItem(0)  # 0 = olMailItem
                    if mail:
                        # If we can create a mail item, the connection is successful
                        result['success'] = True
                        result['message'] = 'Successfully connected to your local Outlook application. Your existing Outlook account will be used to send emails.'
                    else:
                        result['success'] = False
                        result['message'] = 'Could not create a mail item in Outlook. Make sure Outlook is installed and configured.'
                finally:
                    # Make sure to uninitialize COM when done
                    pythoncom.CoUninitialize()
                
            except ImportError:
                result['success'] = False
                result['message'] = 'Microsoft Outlook integration requires the pywin32 library. Please install it with: pip install pywin32'
            except Exception as e:
                result['success'] = False
                result['message'] = f"Failed to connect to Outlook: {str(e)}"
        else:
            # Test SMTP connection
            smtp_server = request.form.get('smtp_server')
            smtp_port = int(request.form.get('smtp_port', 587))
            use_ssl = bool(int(request.form.get('use_ssl', 0)))
            use_tls = bool(int(request.form.get('use_tls', 0)))
            auth_required = bool(int(request.form.get('auth_required', 0)))
            username = request.form.get('username')
            password = request.form.get('password')
            
            import smtplib
            
            # Choose the right SMTP class based on SSL setting
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=5)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=5)
            
            # Start TLS if needed
            if use_tls:
                server.starttls()
            
            # Try authentication if required
            if auth_required:
                if not username or not password:
                    result['success'] = False
                    result['message'] = 'Authentication is required but username or password is missing'
                else:
                    server.login(username, password)
                    result['success'] = True
                    result['message'] = 'Successfully connected and authenticated to SMTP server'
            else:
                result['success'] = True
                result['message'] = 'Successfully connected to SMTP server'
            
            # Close the connection
            server.quit()
            
    except Exception as e:
        result['success'] = False
        result['message'] = f"Connection test failed: {str(e)}"
    
    return jsonify(result)

@app.route('/customer_invoices/<int:customer_id>')
@login_required
def customer_invoices(customer_id):
    """Display invoices related to a specific customer."""
    try:
        # Get customer details
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM customer WHERE customerid = %s', (customer_id,))
            customer = cursor.fetchone()
            
            if not customer:
                flash('Customer not found', 'error')
                return redirect(url_for('invoice_list'))
            
            # Get invoices for this customer
            cursor.execute('''
                SELECT 
                    i.*,
                    e.EventName as event_name
                FROM invoice i
                LEFT JOIN event e ON i.event_id = e.EventID
                WHERE i.customer_id = %s
                ORDER BY i.invoice_date DESC
            ''', (customer_id,))
            
            invoices = cursor.fetchall()
            
            # Convert decimal values to float
            for invoice in invoices:
                if 'total' in invoice and invoice['total'] is not None:
                    invoice['total'] = float(invoice['total'])
                else:
                    invoice['total'] = 0.0
            
            return render_template('invoices/customer_invoices.html',
                                 customer=customer,
                                 invoices=invoices)
    except Exception as e:
        flash(f'Error loading customer invoices: {str(e)}', 'error')
        return redirect(url_for('invoice_list'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/admin/system-settings')
@login_required
def system_settings():
    # Get all settings
    settings = ContributionSettings.get_all_settings()
    return render_template('admin/system_settings.html', settings=settings)

@app.route('/admin/system-settings/update', methods=['POST'])
@login_required
def update_system_settings():
    # Get all settings
    settings = ContributionSettings.get_all_settings()
    
    # Update each setting
    for setting in settings:
        value = request.form.get(setting['name'])
        if value is not None:
            ContributionSettings.update_setting(
                setting['name'],
                value,
                setting['display_name'],
                setting['description'],
                setting['type']
            )
    
    flash('Settings updated successfully', 'success')
    return redirect(url_for('system_settings'))

@app.route('/admin/contribution_settings')
@login_required
def contribution_settings():
    # Get all contribution settings
    all_settings = ContributionSettings.get_all_settings()
    
    # Format settings for template
    contribution_settings = {
        'social_employee': float(all_settings.get('social_employee', {}).get('setting_value', 8.80)),
        'social_employer': float(all_settings.get('social_employer', {}).get('setting_value', 8.80)),
        'gesy_employee': float(all_settings.get('gesy_employee', {}).get('setting_value', 2.65)),
        'gesy_employer': float(all_settings.get('gesy_employer', {}).get('setting_value', 2.90)),
        'cohesion_employee': float(all_settings.get('cohesion_employee', {}).get('setting_value', 0)),
        'cohesion_employer': float(all_settings.get('cohesion_employer', {}).get('setting_value', 2.0)),
        'redundancy_employee': float(all_settings.get('redundancy_employee', {}).get('setting_value', 0)),
        'redundancy_employer': float(all_settings.get('redundancy_employer', {}).get('setting_value', 1.2)),
        'industrial_employee': float(all_settings.get('industrial_employee', {}).get('setting_value', 0)),
        'industrial_employer': float(all_settings.get('industrial_employer', {}).get('setting_value', 0.05))
    }
    
    # Calculate totals
    total_employee = (
        contribution_settings['social_employee'] +
        contribution_settings['gesy_employee'] +
        contribution_settings['cohesion_employee'] +
        contribution_settings['redundancy_employee'] +
        contribution_settings['industrial_employee']
    )
    
    total_employer = (
        contribution_settings['social_employer'] +
        contribution_settings['gesy_employer'] +
        contribution_settings['cohesion_employer'] +
        contribution_settings['redundancy_employer'] +
        contribution_settings['industrial_employer']
    )
    
    contribution_settings['total_employee'] = total_employee
    contribution_settings['total_employer'] = total_employer
    
    return render_template('admin/contribution_settings.html', contribution_settings=contribution_settings)

@app.route('/admin/update-contribution-settings', methods=['POST'])
@login_required
@admin_required
def update_contribution_settings():
    try:
        # Get form data with default values
        social_employee = float(request.form.get('social_employee', 8.80))
        social_employer = float(request.form.get('social_employer', 8.80))
        gesy_employee = float(request.form.get('gesy_employee', 2.65))
        gesy_employer = float(request.form.get('gesy_employer', 2.90))
        cohesion_employer = float(request.form.get('cohesion_employer', 2.0))
        redundancy_employer = float(request.form.get('redundancy_employer', 1.2))
        industrial_employer = float(request.form.get('industrial_employer', 0.05))
        
        # Update each setting
        ContributionSettings.update_setting('social_employee', social_employee,
            'Social Insurance Employee Contribution')
        ContributionSettings.update_setting('social_employer', social_employer,
            'Social Insurance Employer Contribution')
        ContributionSettings.update_setting('gesy_employee', gesy_employee,
            'GESY Employee Contribution')
        ContributionSettings.update_setting('gesy_employer', gesy_employer,
            'GESY Employer Contribution')
        ContributionSettings.update_setting('cohesion_employer', cohesion_employer,
            'Social Cohesion Fund')
        ContributionSettings.update_setting('redundancy_employer', redundancy_employer,
            'Redundancy Fund')
        ContributionSettings.update_setting('industrial_employer', industrial_employer,
            'Industrial Training Fund')
        
        flash('Contribution settings updated successfully', 'success')
        return redirect(url_for('contribution_settings'))
    except Exception as e:
        flash(f'Error updating contribution settings: {str(e)}', 'error')
        return redirect(url_for('contribution_settings'))

@app.route('/generate_employee_report/<int:employee_id>/<int:event_id>')
@login_required
def generate_employee_report(employee_id, event_id):
    try:
        EmployeeRevenueReport.generate_report(employee_id, event_id)
        flash('Report generated successfully', 'success')
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
    
    return redirect(url_for('employee_event_earnings', employee_id=employee_id, event_id=event_id))

@app.route('/generate_event_reports/<int:event_id>')
@login_required
def generate_event_reports(event_id):
    try:
        EmployeeRevenueReport.generate_reports_for_event(event_id)
        flash('Reports generated successfully for all employees in the event', 'success')
    except Exception as e:
        flash(f'Error generating reports: {str(e)}', 'error')
    
    return redirect(url_for('employee_event_earnings', event_id=event_id))

@app.template_filter('decimal_to_hhmm')
def decimal_to_hhmm_filter(value):
    """Convert decimal hours to HH:MM format"""
    if not value:
        return "00:00"
    
    hours = int(value)
    minutes = int((value - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"

def hhmm_to_decimal(time_str):
    """Convert HH:MM format to decimal hours"""
    if not time_str or ':' not in time_str:
        return 0.0
    try:
        hours, minutes = map(int, time_str.split(':'))
        return float(hours) + (float(minutes) / 60)
    except (ValueError, TypeError):
        return 0.0

@app.route('/events/<int:event_id>/edit/submit', methods=['POST'])
@login_required
def update_event_submit_unified(event_id):
    try:
        # Parse and validate form fields
        Customerid = request.form.get('Customerid')
        EventName = request.form.get('EventName')
        EventLocation = request.form.get('EventLocation')
        EventStart = request.form.get('EventStart')
        EventEnd = request.form.get('EventEnd')
        notes = request.form.get('notes')
        WaitersNeeded = request.form.get('WaitersNeeded', 0)
        BartendersNeeded = request.form.get('BartendersNeeded', 0)
        MaleEmployees = request.form.get('MaleEmployees', 0)
        FemaleEmployees = request.form.get('FemaleEmployees', 0)
        TotalEmployees = request.form.get('TotalEmployees', 0)
        EventPerHourcost = request.form.get('EventPerHourcost', 0.00)
        EventPerHourselling = request.form.get('EventPerHourselling', 0.00)
        
        # Get decimal values for hours
        totalhours = float(request.form.get('totalhours_decimal', 0.00))
        totalshifthours = float(request.form.get('totalshifthours_decimal', 0.00))
        
        # Convert cost and selling to float
        totalcost = float(request.form.get('totalcost', 0.00))
        totalselling = float(request.form.get('totalselling', 0.00))
        
        # Calculate totalprofit
        totalprofit = totalselling - totalcost
        EventStage = request.form.get('EventStage', 'Creation')

        # Convert datetimes
        try:
            EventStart_dt = datetime.strptime(EventStart, '%Y-%m-%dT%H:%M') if EventStart else None
            EventEnd_dt = datetime.strptime(EventEnd, '%Y-%m-%dT%H:%M') if EventEnd else None
        except Exception:
            EventStart_dt = None
            EventEnd_dt = None

        # Backend validation: End must be after Start
        if EventStart_dt and EventEnd_dt and EventEnd_dt <= EventStart_dt:
            flash('End Date & Time must be after Start Date & Time.', 'error')
            return redirect(request.referrer or url_for('event_list'))

        # Connect to DB and update event
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            # Get current event stage
            cursor.execute('SELECT EventStage FROM event WHERE EventID = %s', (event_id,))
            current_event = cursor.fetchone()
            current_stage = current_event['EventStage'] if current_event else None

            cursor.execute('''
                UPDATE event SET
                    Customerid=%s,
                    EventName=%s,
                    EventLocation=%s,
                    EventStart=%s,
                    EventEnd=%s,
                    notes=%s,
                    WaitersNeeded=%s,
                    BartendersNeeded=%s,
                    MaleEmployees=%s,
                    FemaleEmployees=%s,
                    TotalEmployees=%s,
                    EventPerHourcost=%s,
                    EventPerHourselling=%s,
                    totalhours=%s,
                    totalcost=%s,
                    totalselling=%s,
                    totalprofit=%s,
                    EventStage=%s,
                    totalshifthours=%s
                WHERE EventID=%s
            ''', (
                Customerid,
                EventName,
                EventLocation,
                EventStart_dt,
                EventEnd_dt,
                notes,
                WaitersNeeded,
                BartendersNeeded,
                MaleEmployees,
                FemaleEmployees,
                TotalEmployees,
                EventPerHourcost,
                EventPerHourselling,
                totalhours,
                totalcost,
                totalselling,
                totalprofit,
                EventStage,
                totalshifthours,
                event_id
            ))
            conn.commit()

            # If event is being marked as completed, generate revenue reports
            if EventStage == 'Completed' and current_stage != 'Completed':
                try:
                    from models.employee_revenue_report import EmployeeRevenueReport
                    EmployeeRevenueReport.generate_reports_for_event(event_id)
                    flash('Event marked as completed and revenue reports generated successfully!', 'success')
                except Exception as e:
                    flash(f'Event updated but error generating revenue reports: {str(e)}', 'warning')
            else:
                flash('Event updated successfully!', 'success')

    except Exception as e:
        flash(f'Error updating event: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()

    return redirect(url_for('event_list'))

@app.route('/shifts/create', methods=['POST'])
@login_required
def create_shift_unified():
    """Create a new shift."""
    try:
        data = request.get_json()
        logger.debug(f"Received shift creation request with data: {data}")
        
        if not data:
            logger.error("No data received in request")
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        # Check for both event_id and eventid
        event_id = data.get('event_id') or data.get('eventid')
        if not event_id:
            logger.error("Event ID is missing from request data")
            return jsonify({'success': False, 'error': 'Event ID is required'}), 400
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Insert shift
            cursor.execute('''
                INSERT INTO shifts (
                    eventid,
                    shiftname,
                    shifttype,
                    shiftstart,
                    shiftend
                ) VALUES (
                    %s, %s, %s, %s, %s
                )
            ''', (
                event_id,
                data.get('shiftname'),
                data.get('shifttype'),
                data.get('shiftstart'),
                data.get('shiftend')
            ))
            
            shift_id = cursor.lastrowid
            conn.commit()
            
            # Return the created shift with empty employees array
            return jsonify({
                'success': True,
                'shift': {
                    'id': shift_id,
                    'name': data.get('shiftname'),
                    'type': data.get('shifttype'),
                    'start': data.get('shiftstart'),
                    'end': data.get('shiftend'),
                    'employees': []  # Initialize empty employees array
                }
            })
            
    except Exception as e:
        logger.error(f"Error creating shift: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/shifts/<int:shift_id>/assign/<int:event_id>', methods=['GET', 'POST'])
@login_required
def assign_employees_to_shift(shift_id, event_id):
    try:
        # Log the received parameters
        app.logger.info(f"Received request for shift_id: {shift_id}, event_id: {event_id}")
        
        if not event_id:
            app.logger.error("Event ID is missing from assign_employees request")
            return jsonify({'success': False, 'error': 'Event ID is required'}), 400
            
        app.logger.info(f"Assigning employees to shift {shift_id} for event {event_id}")
        
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        # Get shift details and verify event_id matches
        cursor.execute("""
            SELECT s.*, e.EventName, e.EventLocation, e.EventStart, e.EventEnd
            FROM shifts s
            JOIN event e ON s.eventid = e.EventID
            WHERE s.shiftid = %s AND s.eventid = %s
        """, (shift_id, event_id))
        shift = cursor.fetchone()
        
        if not shift:
            app.logger.error(f"Shift {shift_id} not found or does not belong to event {event_id}")
            return jsonify({'success': False, 'error': 'Shift not found or does not belong to the specified event'}), 404
            
        # Get assigned employees
        cursor.execute("""
            SELECT e.*, 
                   er.employeerolename,
                   sa.hours as HoursAssigned
            FROM employee e
            LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
            JOIN employee_shifts sa ON e.employeeid = sa.employeeid
            WHERE sa.shiftid = %s
            GROUP BY e.employeeid, er.employeerolename, sa.hours
        """, (shift_id,))
        assigned_employees = cursor.fetchall()
        
        # Get all active employees
        cursor.execute("""
            SELECT e.*, 
                   er.employeerolename
            FROM employee e
            LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
            WHERE e.status = 'Active'
            ORDER BY e.employeename
        """)
        all_employees = cursor.fetchall()
        
        # Convert assigned employees to a set of IDs for easy lookup
        assigned_ids = {emp['employeeid'] for emp in assigned_employees}
        
        # Mark employees as assigned in the all_employees list
        for emp in all_employees:
            emp['is_assigned'] = emp['employeeid'] in assigned_ids
        
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                
                # Handle remove action
                if data.get('action') == 'remove':
                    employee_id = data.get('employee_id')
                    if employee_id:
                        cursor.execute("DELETE FROM employee_shifts WHERE shiftid = %s AND employeeid = %s", 
                                     (shift_id, employee_id))
                        # Update employee earnings after removal
                        cursor.execute("CALL update_employee_event_earnings_for_shift(%s, %s)", 
                                     (employee_id, event_id))
                        conn.commit()
                        app.logger.info(f"Successfully removed employee {employee_id} from shift {shift_id}")
                        return jsonify({'success': True, 'redirect': url_for('view_event', event_id=event_id)})
                    else:
                        return jsonify({'success': False, 'error': 'Employee ID is required for remove action'}), 400
                
                # Handle regular assignment update
                hours = data.get('hours', {})
                
                # For each employee in the hours data
                for emp_id, hours_assigned in hours.items():
                    if emp_id and hours_assigned:
                        # Check if employee is already assigned
                        cursor.execute("""
                            SELECT 1 FROM employee_shifts 
                            WHERE shiftid = %s AND employeeid = %s
                        """, (shift_id, emp_id))
                        exists = cursor.fetchone()
                        
                        if exists:
                            # Update existing assignment
                            cursor.execute("""
                                UPDATE employee_shifts 
                                SET hours = %s 
                                WHERE shiftid = %s AND employeeid = %s
                            """, (hours_assigned, shift_id, emp_id))
                        else:
                            # Add new assignment
                            cursor.execute("""
                                INSERT INTO employee_shifts (shiftid, employeeid, hours)
                                VALUES (%s, %s, %s)
                            """, (shift_id, emp_id, hours_assigned))
                        
                        # Update employee earnings after assignment change
                        cursor.execute("CALL update_employee_event_earnings_for_shift(%s, %s)", 
                                     (emp_id, event_id))
                
                conn.commit()
                app.logger.info(f"Successfully updated assignments for shift {shift_id}")
                return jsonify({'success': True, 'redirect': url_for('view_event', event_id=event_id)})
            else:
                # Handle form submission
                employee_ids = request.form.getlist('employees')
                hours = request.form.getlist('hours')
                
                # For each employee in the form data
                for emp_id, hours_assigned in zip(employee_ids, hours):
                    if emp_id and hours_assigned:
                        # Check if employee is already assigned
                        cursor.execute("""
                            SELECT 1 FROM employee_shifts 
                            WHERE shiftid = %s AND employeeid = %s
                        """, (shift_id, emp_id))
                        exists = cursor.fetchone()
                        
                        if exists:
                            # Update existing assignment
                            cursor.execute("""
                                UPDATE employee_shifts 
                                SET hours = %s 
                                WHERE shiftid = %s AND employeeid = %s
                            """, (hours_assigned, shift_id, emp_id))
                        else:
                            # Add new assignment
                            cursor.execute("""
                                INSERT INTO employee_shifts (shiftid, employeeid, hours)
                                VALUES (%s, %s, %s)
                            """, (shift_id, emp_id, hours_assigned))
                        
                        # Update employee earnings after assignment change
                        cursor.execute("CALL update_employee_event_earnings_for_shift(%s, %s)", 
                                     (emp_id, event_id))
                
                conn.commit()
                app.logger.info(f"Successfully updated assignments for shift {shift_id}")
                flash('Staff assignments updated successfully', 'success')
                return redirect(url_for('view_event', event_id=event_id))
        
        return render_template('events/assign_employees.html',
                             shift=shift,
                             assigned_employees=assigned_employees,
                             all_employees=all_employees,
                             event_id=event_id)
                             
    except Exception as e:
        app.logger.error(f"Error in assign_employees: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/employee_event_earnings')
@login_required
def employee_event_earnings():
    # Get filter parameters
    employee_id = request.args.get('employee_id', '')
    event_id = request.args.get('event_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all events for the dropdown
        cursor.execute("SELECT EventID, EventName, EventStart FROM event ORDER BY EventStart DESC")
        events = cursor.fetchall()

        # Get all employees for the dropdown
        cursor.execute("SELECT employeeid, employeename FROM employee ORDER BY employeename")
        employees = cursor.fetchall()

        # Build the base query for event totals
        totals_query = """
            SELECT 
                evt.EventID,
                evt.EventName,
                evt.EventStart,
                evt.EventEnd,
                ROUND(SUM(es.hours), 2) as event_total_hours,
                ROUND(SUM(es.hours * evt.EventPerHourcost), 2) as event_total_gross,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1104), 2) as event_total_employee_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1384), 2) as event_total_employer_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 1.1384), 2) as event_total_cost
            FROM employee_shifts es
            JOIN shifts s ON es.shiftid = s.shiftid
            JOIN event evt ON s.eventid = evt.EventID
            WHERE es.hours > 0
        """

        # Add filters to totals query
        params = []
        if event_id:
            totals_query += " AND evt.EventID = %s"
            params.append(event_id)
        if start_date:
            totals_query += " AND evt.EventStart >= %s"
            params.append(start_date)
        if end_date:
            totals_query += " AND evt.EventStart <= %s"
            params.append(end_date)

        totals_query += " GROUP BY evt.EventID, evt.EventName, evt.EventStart, evt.EventEnd ORDER BY evt.EventStart DESC"

        # Execute totals query
        cursor.execute(totals_query, params)
        event_totals = {et['EventID']: et for et in cursor.fetchall()}

        # Build the main query for employee details
        query = """
            SELECT 
                e.employeeid,
                e.employeename,
                evt.EventID,
                evt.EventName,
                evt.EventStart,
                evt.EventEnd,
                ROUND(SUM(es.hours), 2) as total_hours,
                ROUND(evt.EventPerHourcost, 2) as costperhour,
                ROUND(evt.EventPerHourselling, 2) as sellingperhour,
                ROUND(SUM(es.hours * evt.EventPerHourcost), 2) as gross_earnings,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1104), 2) as total_employee_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1384), 2) as total_employer_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.8896), 2) as net_earnings,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 1.1384), 2) as total_cost
            FROM employee_shifts es
            JOIN employee e ON e.employeeid = es.employeeid
            JOIN shifts s ON es.shiftid = s.shiftid
            JOIN event evt ON s.eventid = evt.EventID
            WHERE es.hours > 0
        """

        # Add filters
        params = []
        if employee_id:
            query += " AND e.employeeid = %s"
            params.append(employee_id)
        if event_id:
            query += " AND evt.EventID = %s"
            params.append(event_id)
        if start_date:
            query += " AND evt.EventStart >= %s"
            params.append(start_date)
        if end_date:
            query += " AND evt.EventStart <= %s"
            params.append(end_date)

        # Group by to get totals per employee per event
        query += """ 
            GROUP BY e.employeeid, e.employeename, evt.EventID, evt.EventName, evt.EventStart, evt.EventEnd, 
            evt.EventPerHourcost, evt.EventPerHourselling
            ORDER BY evt.EventStart DESC, evt.EventName, e.employeename
        """

        # Execute the query
        cursor.execute(query, params)
        earnings = cursor.fetchall()

        # Group earnings by event
        earnings_by_event = {}
        for earning in earnings:
            event_id = earning['EventID']
            if event_id not in earnings_by_event:
                earnings_by_event[event_id] = {
                    'event_info': {
                        'EventID': event_id,
                        'EventName': earning['EventName'],
                        'EventStart': earning['EventStart'],
                        'EventEnd': earning['EventEnd']
                    },
                    'employees': [],
                    'totals': event_totals.get(event_id, {})
                }
            earnings_by_event[event_id]['employees'].append(earning)

        return render_template('reports/employee_event_earnings.html',
                             earnings_by_event=earnings_by_event,
                             events=events,
                             employees=employees,
                             selected_employee=employee_id,
                             selected_event=event_id,
                             selected_start_date=start_date,
                             selected_end_date=end_date)

    except Exception as e:
        app.logger.error(f"Error in employee_event_earnings: {str(e)}")
        return render_template('reports/employee_event_earnings.html',
                             earnings_by_event={},
                             events=[],
                             employees=[],
                             selected_employee=employee_id,
                             selected_event=event_id,
                             selected_start_date=start_date,
                             selected_end_date=end_date,
                             error=str(e))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_event_employee_earnings(event_id):
    """Update earnings for all employees in an event."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all employees assigned to the event
        cursor.execute("""
            SELECT DISTINCT es.employeeid
            FROM employee_shifts es
            JOIN shifts s ON es.shiftid = s.shiftid
            WHERE s.eventid = %s
        """, (event_id,))
        
        employees = cursor.fetchall()
        
        # Update earnings for each employee
        for employee in employees:
            cursor.execute("CALL update_employee_event_earnings_for_shift(%s, %s)", 
                         (employee['employeeid'], event_id))
        
        conn.commit()
        return True

    except Exception as e:
        app.logger.error(f"Error updating event employee earnings: {str(e)}")
        return False

    finally:
        if conn:
            conn.close()

@app.route('/events/<int:event_id>/update_earnings', methods=['POST'])
@login_required
def update_event_earnings(event_id):
    """Update earnings for all employees in an event."""
    if update_event_employee_earnings(event_id):
        flash('Employee earnings have been updated successfully.', 'success')
    else:
        flash('An error occurred while updating employee earnings.', 'error')
    
    return redirect(url_for('employee_event_earnings', event_id=event_id))

def get_db_connection():
    """Get a database connection with DictCursor."""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/export_employee_event_earnings')
@login_required
def export_employee_event_earnings():
    # Get filter parameters
    employee_id = request.args.get('employee_id', '')
    event_id = request.args.get('event_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    export_format = request.args.get('format', 'xlsx')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get event totals
        totals_query = """
            SELECT 
                evt.EventID,
                evt.EventName,
                evt.EventStart,
                evt.EventEnd,
                ROUND(SUM(es.hours), 2) as event_total_hours,
                ROUND(SUM(es.hours * evt.EventPerHourcost), 2) as event_total_gross,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1104), 2) as event_total_employee_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1384), 2) as event_total_employer_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 1.1384), 2) as event_total_cost
            FROM employee_shifts es
            JOIN shifts s ON es.shiftid = s.shiftid
            JOIN event evt ON s.eventid = evt.EventID
            WHERE es.hours > 0
        """

        # Add filters to totals query
        params = []
        if event_id:
            totals_query += " AND evt.EventID = %s"
            params.append(event_id)
        if start_date:
            totals_query += " AND evt.EventStart >= %s"
            params.append(start_date)
        if end_date:
            totals_query += " AND evt.EventStart <= %s"
            params.append(end_date)

        totals_query += " GROUP BY evt.EventID, evt.EventName, evt.EventStart, evt.EventEnd ORDER BY evt.EventStart DESC"
        cursor.execute(totals_query, params)
        event_totals = {et['EventID']: et for et in cursor.fetchall()}

        # Get employee details
        query = """
            SELECT 
                e.employeeid,
                e.employeename,
                evt.EventID,
                evt.EventName,
                evt.EventStart,
                evt.EventEnd,
                ROUND(SUM(es.hours), 2) as total_hours,
                ROUND(evt.EventPerHourcost, 2) as costperhour,
                ROUND(evt.EventPerHourselling, 2) as sellingperhour,
                ROUND(SUM(es.hours * evt.EventPerHourcost), 2) as gross_earnings,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1104), 2) as total_employee_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.1384), 2) as total_employer_contrib,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 0.8896), 2) as net_earnings,
                ROUND(SUM(es.hours * evt.EventPerHourcost * 1.1384), 2) as total_cost
            FROM employee_shifts es
            JOIN employee e ON e.employeeid = es.employeeid
            JOIN shifts s ON es.shiftid = s.shiftid
            JOIN event evt ON s.eventid = evt.EventID
            WHERE es.hours > 0
        """

        # Add filters
        params = []
        if employee_id:
            query += " AND e.employeeid = %s"
            params.append(employee_id)
        if event_id:
            query += " AND evt.EventID = %s"
            params.append(event_id)
        if start_date:
            query += " AND evt.EventStart >= %s"
            params.append(start_date)
        if end_date:
            query += " AND evt.EventStart <= %s"
            params.append(end_date)

        query += """ 
            GROUP BY e.employeeid, e.employeename, evt.EventID, evt.EventName, evt.EventStart, evt.EventEnd, 
            evt.EventPerHourcost, evt.EventPerHourselling
            ORDER BY evt.EventStart DESC, evt.EventName, e.employeename
        """

        cursor.execute(query, params)
        earnings = cursor.fetchall()

        # Group earnings by event
        earnings_by_event = {}
        for earning in earnings:
            event_id = earning['EventID']
            if event_id not in earnings_by_event:
                earnings_by_event[event_id] = {
                    'event_info': {
                        'EventID': event_id,
                        'EventName': earning['EventName'],
                        'EventStart': earning['EventStart'],
                        'EventEnd': earning['EventEnd']
                    },
                    'employees': [],
                    'totals': event_totals.get(event_id, {})
                }
            earnings_by_event[event_id]['employees'].append(earning)

        if export_format == 'xlsx':
            return export_to_excel(earnings_by_event)
        else:
            return export_to_pdf(earnings_by_event)

    except Exception as e:
        app.logger.error(f"Error in export_employee_event_earnings: {str(e)}")
        flash('An error occurred while exporting the report.', 'error')
        return redirect(url_for('employee_event_earnings'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def export_to_excel(earnings_by_event):
    wb = Workbook()
    ws = wb.active
    ws.title = "Employee Event Earnings"

    # Styles
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color='f8f9fc', end_color='f8f9fc', fill_type='solid')
    total_font = Font(bold=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Headers
    headers = ['Employee', 'Total Hours', 'Cost/Hour', 'Gross Earnings', 'Employee Contributions',
              'Employer Contributions', 'Net Earnings', 'Total Cost']
    
    current_row = 1
    for event_id, event_data in earnings_by_event.items():
        # Event header
        ws.cell(row=current_row, column=1, value=f"{event_data['event_info']['EventName']} ({event_data['event_info']['EventStart'].strftime('%d %b %Y')})")
        ws.cell(row=current_row, column=1).font = Font(bold=True, size=14)
        current_row += 2

        # Column headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        current_row += 1

        # Employee data
        for emp in event_data['employees']:
            ws.cell(row=current_row, column=1, value=emp['employeename'])
            ws.cell(row=current_row, column=2, value=float(emp['total_hours']))
            ws.cell(row=current_row, column=3, value=float(emp['costperhour']))
            ws.cell(row=current_row, column=4, value=float(emp['gross_earnings']))
            ws.cell(row=current_row, column=5, value=float(emp['total_employee_contrib']))
            ws.cell(row=current_row, column=6, value=float(emp['total_employer_contrib']))
            ws.cell(row=current_row, column=7, value=float(emp['net_earnings']))
            ws.cell(row=current_row, column=8, value=float(emp['total_cost']))
            
            for col in range(1, 9):
                ws.cell(row=current_row, column=col).border = border
            current_row += 1

        # Event totals
        totals = event_data['totals']
        ws.cell(row=current_row, column=1, value='Event Totals').font = total_font
        ws.cell(row=current_row, column=2, value=float(totals['event_total_hours'])).font = total_font
        ws.cell(row=current_row, column=4, value=float(totals['event_total_gross'])).font = total_font
        ws.cell(row=current_row, column=5, value=float(totals['event_total_employee_contrib'])).font = total_font
        ws.cell(row=current_row, column=6, value=float(totals['event_total_employer_contrib'])).font = total_font
        ws.cell(row=current_row, column=8, value=float(totals['event_total_cost'])).font = total_font

        for col in range(1, 9):
            cell = ws.cell(row=current_row, column=col)
            cell.fill = header_fill
            cell.border = border

        current_row += 3

    # Format columns
    for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws.column_dimensions[col].width = 15
    ws.column_dimensions['A'].width = 30

    # Create the response
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='employee_event_earnings.xlsx'
    )

def export_to_pdf(earnings_by_event):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    # Custom style for event headers
    event_header_style = ParagraphStyle(
        'EventHeader',
        parent=styles['Heading2'],
        spaceAfter=20
    )

    for event_id, event_data in earnings_by_event.items():
        # Event header
        event_header = Paragraph(
            f"{event_data['event_info']['EventName']} ({event_data['event_info']['EventStart'].strftime('%d %b %Y')})",
            event_header_style
        )
        elements.append(event_header)

        # Table headers
        headers = ['Employee', 'Total Hours', 'Cost/Hour', 'Gross Earnings', 'Employee Contributions',
                  'Employer Contributions', 'Net Earnings', 'Total Cost']
        
        # Table data
        data = [headers]
        
        # Employee rows
        for emp in event_data['employees']:
            row = [
                emp['employeename'],
                f"{float(emp['total_hours']):.2f}",
                f"€{float(emp['costperhour']):.2f}",
                f"€{float(emp['gross_earnings']):.2f}",
                f"€{float(emp['total_employee_contrib']):.2f}",
                f"€{float(emp['total_employer_contrib']):.2f}",
                f"€{float(emp['net_earnings']):.2f}",
                f"€{float(emp['total_cost']):.2f}"
            ]
            data.append(row)

        # Totals row
        totals = event_data['totals']
        totals_row = [
            'Event Totals',
            f"{float(totals['event_total_hours']):.2f}",
            '',
            f"€{float(totals['event_total_gross']):.2f}",
            f"€{float(totals['event_total_employee_contrib']):.2f}",
            f"€{float(totals['event_total_employer_contrib']):.2f}",
            '',
            f"€{float(totals['event_total_cost']):.2f}"
        ]
        data.append(totals_row)

        # Create and style the table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

    # Build the PDF
    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='employee_event_earnings.pdf'
    )

if __name__ == "__main__":
    logging.info("Starting the Flask application...")
    try:
        app.run(debug=True)
    except Exception as e:
        logging.error(f"An error occurred while starting the application: {str(e)}")

