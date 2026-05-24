#!/usr/bin/env python3
"""
Smart Home Automation System
Main application entry point
"""

import os
import sys
from app import create_app
from app.web_interface import setup_routes

def main():
    """Main application function"""
    print("🏠 Starting Smart Home Automation System...")

    # Create Flask app, SocketIO, and MQTT client
    app, socketio, mqtt_client = create_app()

    # Setup routes and device controller (also starts MQTT if configured)
    controller = setup_routes(app, socketio, mqtt_client=mqtt_client)
    
    print("✅ System initialized successfully!")
    print("📱 Web interface available at: http://localhost:5000")
    print("🔧 Features:")
    print("   • Automated lighting control")
    print("   • Climate control system")  
    print("   • Security monitoring")
    print("   • Real-time sensor data")
    print("   • Energy usage tracking")
    print("\n🚀 Starting web server...")
    
    try:
        # Run the application
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Starting server on port {port}")
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=port, 
            debug=False,  # Set to False for production
            allow_unsafe_werkzeug=False,
            log_output=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Smart Home System...")
        controller.stop_sensor_simulation()
        if mqtt_client is not None:
            mqtt_client.stop()
        print("✅ System shutdown complete.")
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()