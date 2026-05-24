# Smart Home Automation

Operator-console dashboard for a simulated home-automation system, with an honest **real MQTT broker round-trip** so the architecture matches the narrative.

**Live:** https://smart-home-automation-production.up.railway.app/

## Stack

- **Backend:** Python 3.9 · Flask 2.3 · Flask-SocketIO 5.3 · paho-mqtt 1.6 · SQLite · eventlet
- **Broker:** Eclipse Mosquitto 2.0 (optional sidecar — app degrades to sim mode if unavailable)
- **Frontend:** Single-file `app/templates/index.html` — operator-terminal aesthetic, no build pipeline (Geist Sans + JetBrains Mono via Google Fonts CDN, WebSocket for real-time updates)
- **Deploy:** Railway (Nixpacks builder for the Flask service; Mosquitto runs as a separate Railway service)

## What is real vs simulated

The UI tells the truth via the **`// system reality`** footer at the bottom of the page:

- **Simulated:** All device state (lights, sensors, climate) lives in SQLite + is mutated server-side. No physical fixtures are wired.
- **Real:** When `MQTT_HOST` is configured and the broker is reachable, every device mutation publishes to `home/devices/<id>/state` on the broker, and the app subscribes to `home/devices/+/command` so an external MQTT client can drive devices through a real round-trip.
- **Honest degradation:** Without a broker the broker pip stays grey and labelled `offline · sim`. It only flips to `live` when a real connection is established.

## Topic schema

| Topic | Direction | Payload |
|---|---|---|
| `home/devices/<id>/state` | published by the app | `{id, name, type, room, status, value, ts}` (retained) |
| `home/devices/<id>/command` | subscribed by the app | `{action: "toggle"\|"brightness"\|"temperature", value: <num>}` |

### Try the round-trip locally

```bash
# 1. Start the broker
docker compose up -d mosquitto

# 2. Run the app (separate terminal)
MQTT_HOST=localhost python main.py

# 3. Drive a device from a third terminal — UI updates in real time
mosquitto_pub -h localhost -t home/devices/1/command -m '{"action":"toggle"}'
mosquitto_pub -h localhost -t home/devices/1/command -m '{"action":"brightness","value":42}'

# 4. Watch state messages flow back
mosquitto_sub -h localhost -t 'home/devices/+/state' -v
```

## Local development

```bash
pip install -r requirements.txt

# Without broker — sim mode, broker pip stays offline:
python main.py

# With broker — broker pip flips to live:
docker compose up -d mosquitto
MQTT_HOST=localhost python main.py
```

Open `http://localhost:5000`.

## Project layout

```
smart-home-automation/
├── app/
│   ├── __init__.py          # Flask + SocketIO + MQTTClient factory
│   ├── models.py            # Device / Room (SQLite-backed)
│   ├── device_controller.py # Mutation logic + sensor sim loop + MQTT publish
│   ├── mqtt_client.py       # paho-mqtt wrapper with graceful degradation
│   ├── web_interface.py     # Routes + /api/broker/status + WS handlers
│   └── templates/
│       └── index.html       # Single-file UI (operator-terminal aesthetic)
├── mosquitto/
│   ├── Dockerfile           # eclipse-mosquitto:2.0 + config
│   └── config/mosquitto.conf
├── docker-compose.yml       # Local broker only — app runs natively
├── main.py                  # Entry point
├── railway.json             # Railway Nixpacks config (Flask service)
├── requirements.txt
└── .env.example
```

## Deploy: Railway

The Flask service deploys from the repo root via Nixpacks (see `railway.json`). To enable the real broker round-trip:

1. **Add a new Railway service** in the same project, pointing at this repo with **root directory** set to `mosquitto/`. Railway will build the Dockerfile and expose Mosquitto on port 1883.
2. **Enable private networking** between the two services (Railway → service settings → Networking → Private Networking → generate internal domain).
3. **On the Flask service**, set env vars:
   ```
   MQTT_HOST=<mosquitto-internal-hostname>.railway.internal
   MQTT_PORT=1883
   ```
4. **Redeploy** the Flask service. The `// system reality` footer will flip to "live" and the broker pip will turn green.

If you'd rather not run your own broker, point `MQTT_HOST` at any public test broker (e.g. `test.mosquitto.org` — public, anonymous, intentionally unreliable). The UI will report it accurately.

## Honesty notes

This repo intentionally avoids overclaiming. The work-page narrative (drewmalhotra.com → smart home) describes a "local Mosquitto MQTT broker"; this codebase ships the actual broker plumbing and degrades transparently when no broker is available, instead of pretending. The same honesty pattern shows up on the [financial-analysis-tool](https://github.com/d-malhotra2020/financial-analysis-tool) calibration card (measured backtest accuracy displayed alongside predictions).
