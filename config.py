from flask import Flask
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'V0sp0r0si968!'
app.config['MYSQL_DB'] = 'sml'
app.config['MYSQL_PORT'] = 3306

# Secret key for session management
app.config['SECRET_KEY'] = '4256ccebf2245cc9e3651352e4540c16a42dade9250b9408e3dff75e40ddaa2d'

def get_mysql_connection():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            port=app.config['MYSQL_PORT'],
            cursorclass=pymysql.cursors.DictCursor
        )
        if connection:
            cursor = connection.cursor()
            return connection, cursor
    except Exception as e:
        print(f"Error connecting to MySQL: {str(e)}")
        return None, None
