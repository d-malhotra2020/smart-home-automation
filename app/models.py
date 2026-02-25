import sqlite3
from datetime import datetime
import json

class Device:
    def __init__(self, id=None, name=None, type=None, room=None, status='off', value=0.0):
        self.id = id
        self.name = name
        self.type = type
        self.room = room
        self.status = status
        self.value = value
        self.last_update = datetime.now()
    
    @staticmethod
    def get_all():
        """Get all devices from database"""
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM devices ORDER BY room, name')
        devices = []
        for row in cursor.fetchall():
            device = Device(row[0], row[1], row[2], row[3], row[4], row[5])
            device.last_update = row[6]
            devices.append(device)
        conn.close()
        return devices
    
    @staticmethod
    def get_by_id(device_id):
        """Get device by ID"""
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            device = Device(row[0], row[1], row[2], row[3], row[4], row[5])
            device.last_update = row[6]
            return device
        return None
    
    @staticmethod
    def get_by_room(room):
        """Get devices by room"""
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM devices WHERE room = ?', (room,))
        devices = []
        for row in cursor.fetchall():
            device = Device(row[0], row[1], row[2], row[3], row[4], row[5])
            device.last_update = row[6]
            devices.append(device)
        conn.close()
        return devices
    
    def update_status(self, status, value=None):
        """Update device status and value"""
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        if value is not None:
            cursor.execute(
                'UPDATE devices SET status = ?, value = ?, last_update = CURRENT_TIMESTAMP WHERE id = ?',
                (status, value, self.id)
            )
            self.value = value
        else:
            cursor.execute(
                'UPDATE devices SET status = ?, last_update = CURRENT_TIMESTAMP WHERE id = ?',
                (status, self.id)
            )
        conn.commit()
        conn.close()
        self.status = status
        self.last_update = datetime.now()
    
    def log_sensor_data(self, value):
        """Log sensor data reading"""
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sensor_data (device_id, value) VALUES (?, ?)',
            (self.id, value)
        )
        cursor.execute(
            'UPDATE devices SET value = ?, last_update = CURRENT_TIMESTAMP WHERE id = ?',
            (value, self.id)
        )
        conn.commit()
        conn.close()
        self.value = value
    
    def to_dict(self):
        """Convert device to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'room': self.room,
            'status': self.status,
            'value': self.value,
            'last_update': str(self.last_update)
        }

class Room:
    @staticmethod
    def get_all():
        """Get all unique rooms"""
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT room FROM devices ORDER BY room')
        rooms = [row[0] for row in cursor.fetchall()]
        conn.close()
        return rooms
    
    @staticmethod
    def get_room_summary(room):
        """Get summary of devices in a room"""
        devices = Device.get_by_room(room)
        summary = {
            'room': room,
            'total_devices': len(devices),
            'lights_on': len([d for d in devices if d.type == 'light' and d.status == 'on']),
            'sensors_active': len([d for d in devices if d.type == 'sensor' and d.status == 'active']),
            'climate_status': next((d.status for d in devices if d.type == 'climate'), 'N/A'),
            'temperature': next((d.value for d in devices if 'temperature' in d.name.lower()), None)
        }
        return summary