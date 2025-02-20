from flask import Flask
from flask_login import LoginManager
from .config import Config
import mysql.connector
from mysql.connector import pooling

# Konfigurasi koneksi database
db_config = {
    'pool_name': 'mypool',
    'pool_size': 5,
    'host': 'localhost',
    'user': 'root',
    'password': '',  # sesuaikan jika ada password
    'database': 'hotel_management'
}

# Buat connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def get_db():
    return connection_pool.get_connection()

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .controllers.main import main
    from .controllers.auth import auth
    from .controllers.admin import admin
    from .controllers.guest import guest

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(guest)

    return app 