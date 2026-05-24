from flask import Flask
from flask_socketio import SocketIO
import sqlite3
import os

from .mqtt_client import MQTTClient


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize database
    init_db()

    # MQTT client — initialized here so /api/broker/status can read it
    # even if startup connection fails. command_handler wired in
    # setup_routes once the DeviceController exists.
    mqtt_client = MQTTClient()

    return app, socketio, mqtt_client

def init_db():
    """Initialize the SQLite database"""
    try:
        print("🔄 Initializing database...")
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices'")
        if cursor.fetchone():
            print("✅ Database already initialized")
            conn.close()
            return
        
        # Create devices table
        cursor.execute('''
            CREATE TABLE devices (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                room TEXT NOT NULL,
                status TEXT DEFAULT 'off',
                value REAL DEFAULT 0.0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sensor_data table
        cursor.execute('''
            CREATE TABLE sensor_data (
                id INTEGER PRIMARY KEY,
                device_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                value REAL,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        ''')
        
        # Insert sample devices
        devices = [
            ('Living Room Light', 'light', 'living_room', 'off', 0),
            ('Bedroom Light', 'light', 'bedroom', 'off', 0),
            ('Kitchen Light', 'light', 'kitchen', 'off', 0),
            ('Thermostat', 'climate', 'living_room', 'auto', 22.0),
            ('Motion Sensor', 'sensor', 'living_room', 'active', 0),
            ('Door Sensor', 'sensor', 'entrance', 'closed', 0),
            ('Temperature Sensor', 'sensor', 'living_room', 'active', 22.5),
            ('Humidity Sensor', 'sensor', 'living_room', 'active', 45.0),
        ]
        
        cursor.executemany(
            'INSERT INTO devices (name, type, room, status, value) VALUES (?, ?, ?, ?, ?)',
            devices
        )
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        print("⚠️  Continuing without database initialization...")
        # Don't raise the exception - allow app to start without database