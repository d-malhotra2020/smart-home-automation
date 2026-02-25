from flask import Flask
from flask_socketio import SocketIO
import sqlite3
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize database
    init_db()
    
    return app, socketio

def init_db():
    """Initialize the SQLite database"""
    if not os.path.exists('smart_home.db'):
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        
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