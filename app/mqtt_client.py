"""
MQTT client wrapper for the smart-home operator console.

Designed for honest graceful degradation: if no broker is configured
or reachable, the app keeps running in sim mode and the UI surfaces
that state explicitly. There is no fake "live" state.

Topic schema:
    home/devices/<id>/state    — published BY this app on every mutation
    home/devices/<id>/command  — subscribed BY this app; external clients
                                 publish here to drive devices through the
                                 real broker round-trip
"""

import json
import os
import threading
import time
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:  # pragma: no cover — paho is in requirements.txt
    PAHO_AVAILABLE = False


COMMAND_TOPIC = "home/devices/+/command"
STATE_TOPIC_TEMPLATE = "home/devices/{device_id}/state"


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class MQTTClient:
    """Thin paho-mqtt wrapper with graceful failure semantics.

    The Flask app constructs one of these at startup. If the broker is
    unreachable, .start() returns immediately and .connected stays False;
    the rest of the app continues in sim mode.

    A device_controller callback is registered so that incoming commands
    on home/devices/<id>/command are routed back into the controller.
    """

    def __init__(self, host=None, port=None, username=None, password=None,
                 client_id=None, command_handler=None):
        self.host = host or os.environ.get("MQTT_HOST")
        self.port = int(port or os.environ.get("MQTT_PORT", 1883))
        self.username = username or os.environ.get("MQTT_USERNAME")
        self.password = password or os.environ.get("MQTT_PASSWORD")
        self.client_id = client_id or os.environ.get("MQTT_CLIENT_ID", "smart-home-app")
        self.command_handler = command_handler

        self.connected = False
        self.last_attempt = None
        self.last_error = None
        self.enabled = bool(self.host) and PAHO_AVAILABLE
        self._client = None
        self._lock = threading.Lock()

    # ---------- public API ----------

    @property
    def mode(self) -> str:
        """High-level mode label surfaced to the UI."""
        if not self.enabled:
            return "sim"
        return "live" if self.connected else "sim"

    def status(self) -> dict:
        """Snapshot of broker state for /api/broker/status."""
        return {
            "mode": self.mode,
            "connected": self.connected,
            "enabled": self.enabled,
            "host": self.host,
            "port": self.port if self.host else None,
            "last_attempt": self.last_attempt,
            "last_error": self.last_error,
            "paho_available": PAHO_AVAILABLE,
        }

    def start(self):
        """Connect to the broker without blocking.

        Returns True if a connection attempt was initiated, False if
        broker is not configured or paho is missing.
        """
        if not self.enabled:
            print(f"⚠️  MQTT disabled (host={self.host!r}, paho={PAHO_AVAILABLE})")
            return False

        self._client = mqtt.Client(client_id=self.client_id, clean_session=True)
        if self.username:
            self._client.username_pw_set(self.username, self.password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        self.last_attempt = datetime.now(timezone.utc).isoformat()
        try:
            # connect_async + loop_start: non-blocking; paho retries internally
            self._client.connect_async(self.host, self.port, keepalive=30)
            self._client.loop_start()
            return True
        except Exception as exc:
            self.connected = False
            self.last_error = str(exc)
            print(f"❌ MQTT connect_async failed: {exc}")
            return False

    def stop(self):
        if self._client is None:
            return
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass

    def publish_device_state(self, device):
        """Publish device state to home/devices/<id>/state. No-op in sim mode."""
        if not self.connected or self._client is None:
            return False
        payload = json.dumps({
            "id": device.id,
            "name": device.name,
            "type": device.type,
            "room": device.room,
            "status": device.status,
            "value": device.value,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        topic = STATE_TOPIC_TEMPLATE.format(device_id=device.id)
        try:
            self._client.publish(topic, payload, qos=0, retain=True)
            return True
        except Exception as exc:
            self.last_error = f"publish failed: {exc}"
            return False

    # ---------- paho callbacks ----------

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            with self._lock:
                self.connected = True
                self.last_error = None
            print(f"✅ MQTT connected to {self.host}:{self.port}")
            client.subscribe(COMMAND_TOPIC, qos=0)
        else:
            with self._lock:
                self.connected = False
                self.last_error = f"connect rc={rc}"
            print(f"❌ MQTT connect failed rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        with self._lock:
            self.connected = False
        if rc != 0:
            print(f"⚠️  MQTT disconnected unexpectedly rc={rc} — paho will retry")

    def _on_message(self, client, userdata, msg):
        if self.command_handler is None:
            return
        # Topic: home/devices/<id>/command
        parts = msg.topic.split("/")
        if len(parts) != 4 or parts[0] != "home" or parts[1] != "devices" or parts[3] != "command":
            return
        try:
            device_id = int(parts[2])
        except ValueError:
            return
        try:
            payload = json.loads(msg.payload.decode("utf-8") or "{}")
        except Exception as exc:
            print(f"⚠️  MQTT bad command payload on {msg.topic}: {exc}")
            return
        try:
            self.command_handler(device_id, payload)
        except Exception as exc:
            print(f"⚠️  MQTT command handler error: {exc}")
