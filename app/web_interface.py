from flask import render_template, request, jsonify
from flask_socketio import emit
from .models import Device, Room
from .device_controller import DeviceController

def setup_routes(app, socketio):
    controller = DeviceController(socketio)
    controller.start_sensor_simulation()
    
    @app.route('/')
    def index():
        return """
        <html>
        <head><title>Smart Home Automation System</title></head>
        <body>
            <h1>🏠 Smart Home Automation System</h1>
            <p>System Status: Online</p>
            <p>API Endpoints:</p>
            <ul>
                <li><a href="/api/devices">/api/devices</a> - List all devices</li>
                <li><a href="/api/rooms">/api/rooms</a> - List all rooms</li>
                <li><a href="/api/energy">/api/energy</a> - Energy usage</li>
            </ul>
        </body>
        </html>
        """
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "Smart Home Automation"}
    
    @app.route('/api/devices')
    def get_devices():
        try:
            devices = Device.get_all()
            return jsonify([device.to_dict() for device in devices])
        except Exception as e:
            print(f"Error getting devices: {e}")
            return jsonify({"error": "Database not available", "devices": []})
    
    @app.route('/api/rooms')
    def get_rooms():
        try:
            rooms = Room.get_all()
            room_data = []
            for room in rooms:
                summary = Room.get_room_summary(room)
                room_data.append(summary)
            return jsonify(room_data)
        except Exception as e:
            print(f"Error getting rooms: {e}")
            return jsonify({"error": "Database not available", "rooms": []})
    
    @app.route('/api/devices/<int:device_id>/toggle', methods=['POST'])
    def toggle_device(device_id):
        device = controller.toggle_light(device_id)
        if device:
            return jsonify(device.to_dict())
        return jsonify({'error': 'Device not found or not controllable'}), 404
    
    @app.route('/api/devices/<int:device_id>/brightness', methods=['POST'])
    def set_brightness(device_id):
        data = request.get_json()
        brightness = data.get('brightness', 0)
        device = controller.set_light_brightness(device_id, brightness)
        if device:
            return jsonify(device.to_dict())
        return jsonify({'error': 'Device not found'}), 404
    
    @app.route('/api/devices/<int:device_id>/temperature', methods=['POST'])
    def set_temperature(device_id):
        data = request.get_json()
        temperature = data.get('temperature', 22.0)
        device = controller.set_temperature(device_id, temperature)
        if device:
            return jsonify(device.to_dict())
        return jsonify({'error': 'Device not found'}), 404
    
    @app.route('/api/energy')
    def get_energy_usage():
        usage = controller.get_energy_usage()
        return jsonify({
            'current_usage': usage,
            'daily_estimate': round(usage * 24, 2),
            'monthly_estimate': round(usage * 24 * 30, 2),
            'cost_per_hour': round(usage * 0.12, 2)  # $0.12 per kWh
        })
    
    @app.route('/api/automation')
    def get_automation_rules():
        rules = controller.get_room_automation_rules()
        return jsonify(rules)
    
    @socketio.on('connect')
    def handle_connect():
        print(f'Client connected: {request.sid}')
        # Send current device states
        devices = Device.get_all()
        emit('initial_data', {
            'devices': [device.to_dict() for device in devices]
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client disconnected: {request.sid}')
    
    @socketio.on('device_control')
    def handle_device_control(data):
        device_id = data.get('device_id')
        action = data.get('action')
        value = data.get('value')
        
        if action == 'toggle':
            device = controller.toggle_light(device_id)
        elif action == 'brightness':
            device = controller.set_light_brightness(device_id, value)
        elif action == 'temperature':
            device = controller.set_temperature(device_id, value)
        else:
            emit('error', {'message': 'Unknown action'})
            return
        
        if device:
            emit('device_update', device.to_dict(), broadcast=True)
        else:
            emit('error', {'message': 'Device control failed'})
    
    return controller