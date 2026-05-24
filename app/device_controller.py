import time
import random
import threading
from datetime import datetime
from .models import Device

class DeviceController:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.running = False
        self.sensor_thread = None
    
    def start_sensor_simulation(self):
        """Start simulating sensor readings"""
        if not self.running:
            self.running = True
            self.sensor_thread = threading.Thread(target=self._sensor_loop)
            self.sensor_thread.daemon = True
            self.sensor_thread.start()
    
    def stop_sensor_simulation(self):
        """Stop sensor simulation"""
        self.running = False
        if self.sensor_thread:
            self.sensor_thread.join()
    
    def _sensor_loop(self):
        """Main sensor simulation loop"""
        while self.running:
            self._update_sensors()
            time.sleep(5)  # Update every 5 seconds
    
    def _update_sensors(self):
        """Update sensor readings with simulated data"""
        devices = Device.get_all()
        updated_devices = []
        
        for device in devices:
            if device.type == 'sensor':
                if 'temperature' in device.name.lower():
                    # Simulate temperature fluctuation
                    base_temp = 22.0
                    variation = random.uniform(-2, 2)
                    new_value = round(base_temp + variation, 1)
                    device.log_sensor_data(new_value)
                    updated_devices.append(device)
                
                elif 'humidity' in device.name.lower():
                    # Simulate humidity changes
                    base_humidity = 45.0
                    variation = random.uniform(-5, 5)
                    new_value = round(max(30, min(70, base_humidity + variation)), 1)
                    device.log_sensor_data(new_value)
                    updated_devices.append(device)
                
                elif 'motion' in device.name.lower():
                    # Simulate motion detection
                    if random.random() < 0.1:  # 10% chance of motion
                        device.log_sensor_data(1)
                        device.update_status('motion_detected')
                        updated_devices.append(device)
                        # Auto-reset after 3 seconds
                        threading.Timer(3.0, lambda: self._reset_motion_sensor(device.id)).start()
        
        # Emit updates to web interface
        if self.socketio and updated_devices:
            self.socketio.emit('sensor_update', {
                'devices': [device.to_dict() for device in updated_devices],
                'timestamp': datetime.now().isoformat()
            })
    
    def _reset_motion_sensor(self, device_id):
        """Reset motion sensor to active state"""
        device = Device.get_by_id(device_id)
        if device:
            device.update_status('active', 0)
            if self.socketio:
                self.socketio.emit('device_update', device.to_dict())
    
    def toggle_light(self, device_id):
        """Toggle light on/off"""
        device = Device.get_by_id(device_id)
        if device and device.type == 'light':
            new_status = 'off' if device.status == 'on' else 'on'
            brightness = 100 if new_status == 'on' else 0
            device.update_status(new_status, brightness)
            
            # Emit update
            if self.socketio:
                self.socketio.emit('device_update', device.to_dict())
            
            return device
        return None
    
    def set_light_brightness(self, device_id, brightness):
        """Set light brightness (0-100)"""
        device = Device.get_by_id(device_id)
        if device and device.type == 'light':
            status = 'on' if brightness > 0 else 'off'
            device.update_status(status, brightness)
            
            # Emit update
            if self.socketio:
                self.socketio.emit('device_update', device.to_dict())
            
            return device
        return None
    
    def set_temperature(self, device_id, temperature):
        """Set thermostat temperature"""
        device = Device.get_by_id(device_id)
        if device and device.type == 'climate':
            device.update_status('heating' if temperature > device.value else 'cooling', temperature)
            
            # Emit update
            if self.socketio:
                self.socketio.emit('device_update', device.to_dict())
            
            return device
        return None
    
    def get_energy_usage(self):
        """Calculate estimated energy usage"""
        devices = Device.get_all()
        total_usage = 0
        
        for device in devices:
            if device.type == 'light' and device.status == 'on':
                # LED light: ~10W at full brightness
                total_usage += (device.value / 100) * 10
            elif device.type == 'climate':
                # HVAC system: ~2000W when active
                if device.status in ['heating', 'cooling']:
                    total_usage += 2000
        
        return round(total_usage, 2)
    
    def apply_motion_lighting(self, room):
        """Apply motion-activated lighting"""
        lights = [d for d in Device.get_by_room(room) if d.type == 'light']
        for light in lights:
            if light.status == 'off':
                self.toggle_light(light.id)