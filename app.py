import logging
import os
import platform

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

# Windows-specific imports
WINDOWS = platform.system() == 'Windows'
if WINDOWS:
    try:
        import win32com.client
        import pythoncom
        EXCHANGE_AVAILABLE = True
    except ImportError:
        EXCHANGE_AVAILABLE = False
else:
    EXCHANGE_AVAILABLE = False

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, send_file
from markupsafe import Markup
from config import app, get_mysql_connection
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, date, timezone
import pymysql
from flask_mysqldb import MySQL  # Added MySQL import
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
import csv
from io import StringIO
from models.system_settings import ContributionSettings
import re
import uuid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import io
import base64
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
            # Check if token exists and is valid
            cursor.execute('''
                SELECT prt.*, u.email, u.username 
                FROM password_reset_tokens prt
                JOIN users u ON u.id = prt.user_id
                WHERE token = %s AND expiry > NOW()
            ''', (token,))
            
            token_data = cursor.fetchone()
            
            if not token_data:
                flash('Invalid or expired reset token.', 'error')
                return redirect(url_for('login'))
            
            if request.method == 'POST':
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                
                if not password or not confirm_password:
                    flash('Both password fields are required.', 'error')
                    return render_template('auth/reset_password.html')
                
                if password != confirm_password:
                    flash('Passwords do not match.', 'error')
                    return render_template('auth/reset_password.html')
                
                # Update password
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    'UPDATE users SET password = %s WHERE id = %s',
                    (hashed_password, token_data['user_id'])
                )
                
                # Delete used token
                cursor.execute(
                    'DELETE FROM password_reset_tokens WHERE token = %s',
                    (token,)
                )
                
                conn.commit()
                
                flash('Your password has been reset successfully.', 'success')
                return redirect(url_for('login'))
            
            return render_template('auth/reset_password.html')
            
    except Exception as e:
        flash(f'Error resetting password: {str(e)}', 'error')
        return redirect(url_for('login'))
        
    finally:
        if 'conn' in locals():
            conn.close() 