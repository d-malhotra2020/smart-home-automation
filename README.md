# Smart Home Automation System

An intelligent home automation system that integrates various IoT devices and sensors to create a seamless smart home experience.

## Features
- Automated lighting control
- Climate control system
- Security monitoring
- Mobile + Voice control
- 30% energy savings target
- <500ms response latency

## Tech Stack
- Python (Flask web server)
- Raspberry Pi simulation
- MQTT message broker
- SQLite database
- WebSocket for real-time updates

## Project Structure
```
smart-home-automation/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── mqtt_client.py
│   ├── device_controller.py
│   └── web_interface.py
├── devices/
│   ├── sensors.py
│   ├── lights.py
│   ├── climate.py
│   └── security.py
├── static/
├── templates/
├── requirements.txt
└── main.py
```

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the system: `python main.py`
3. Access web interface: `http://localhost:5000`