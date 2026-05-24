# smart-home-automation — Next Session Plan

**Created:** 2026-05-23 (session paused for the night)
**Resume with:** `cd ~/separate-projects/smart-home-automation && cat NEXT-SESSION.md`
**Plan:** Option C — full overhaul (operator-terminal restyle + UX streamline + real MQTT broker)

---

## What got decided tonight

After the financial-analysis-tool restyle, surveyed this repo and presented four "streamlined" options. Drew chose **Option C: full overhaul** but called the night before execution.

**Option C scope:**

1. **Operator-terminal aesthetic restyle** (matches drewmalhotra.com + financial-analysis-tool)
   - Replace `templates/index.html`'s purple/glassmorphism look (`linear-gradient(135deg, #667eea 0%, #764ba2 100%)`) with:
     - Background `#0a0a0c`, surface `#111114`, hairlines `#1f1f23`
     - Geist Sans + JetBrains Mono via CDN (no Next.js build pipeline here — straight CSS)
     - Bloomberg green (`#22c55e`) for "on" / red (`#ef4444`) for "off"
     - Mono small-caps section labels with `//` prefix
     - Pip indicators (green pulse) on the status bar
   - Goal: same hand as the other two surfaces. Recruiters tab between them and feel one designer.

2. **UX streamline**
   - Drop the nested room-card / device-card grid busyness.
   - Switch to a dense single-list view with room as a column or grouping label.
   - Add a sticky top status bar: `● broker: live · 14 devices · 0.83 kW · NY 21:42`
   - Cut the energy-usage card if it's still a static placeholder (check `web_interface.py` line 65 — `/api/energy` endpoint).
   - Tighter mobile/desktop responsiveness.
   - Drop or hide automation-rules UI if it's mostly a placeholder.

3. **Make the manifesto true — real MQTT broker** (the substantive piece)
   - Work-page deep-dive (`src/work/smart-home.md` on the portfolio) claims "local Mosquitto MQTT broker" — currently the broker isn't actually running; devices are simulated.
   - Add a Mosquitto sidecar service (Docker Compose locally, or Railway second service).
   - Wire `app/device_controller.py` to actually publish/subscribe via `paho-mqtt` (already in `requirements.txt`).
   - Add a "broker: live" / "broker: offline" indicator on the status bar so the UI tells the truth either way.
   - Be honest about which devices have real MQTT topics vs. simulated state — label them, like the calibration card on financial-analysis-tool labels what was actually backtested.

---

## Current state survey (as of session pause)

**Stack:** Flask 2.3.3 + Flask-SocketIO 5.3.6 + SQLite + paho-mqtt 1.6.1 (no broker) + eventlet
**Entry:** `python main.py` → `app/__init__.py:create_app()` + `app/web_interface.py:setup_routes()`
**UI:** Single 405-line `templates/index.html` with inline CSS (purple gradient theme, last touched commit `3d3a5d2` "Modernize smart home UI with dark theme and improved design" — name says dark, reality is purple)
**Live:** https://smart-home-automation-production.up.railway.app/ → HTTP 200
**Repo state:** clean, HEAD `3d3a5d2`, in sync with `origin/master`. No `.planning/` directory.

**Routes in `app/web_interface.py`:**
- `GET /` → index template
- `GET /health`
- `GET /api/devices`
- `GET /api/rooms`
- `POST /api/devices/<id>/toggle`
- `POST /api/devices/<id>/brightness`
- `POST /api/devices/<id>/temperature`
- `GET /api/energy` (likely placeholder)
- `GET /api/automation` (likely placeholder)
- WebSocket: `connect`, `disconnect`, `device_control` events

**Important repo facts:**
- Same diverged-copy situation as the other projects: `~/projects/smart-home-automation/` is a separate Railway-tweaked variant with no remote — don't touch it. Canonical lives at `~/separate-projects/smart-home-automation/` with `github.com/d-malhotra2020/smart-home-automation.git`.
- Railway uses Nixpacks (no Dockerfile yet) per `railway.json`. If MQTT broker work needs a sidecar, may switch to Docker Compose or a second Railway service.
- `devices/` directory exists but is empty (placeholder for real MQTT device definitions when broker work happens).

---

## How to resume

When ready to execute Option C, the natural pattern is the same one used for financial-analysis-tool:

1. **Phase 1 — Aesthetic restyle**
   Rewrite `templates/index.html` (and `app/templates/index.html` — check which is actually served; commit `0454e29` says "Move template to app/templates"). Inline `<style>` block with the operator-terminal token system. Geist Sans + JetBrains Mono from Google Fonts CDN. Atomic commit.

2. **Phase 2 — UX streamline**
   Restructure the rendered DOM and the data shapes returned by `/api/rooms` / `/api/devices`. Drop dead routes. Tighten the page. Atomic commit.

3. **Phase 3 — Real MQTT broker**
   - Add `docker-compose.yml` (local) or a Railway companion service for `eclipse-mosquitto`.
   - Refactor `app/device_controller.py` to publish/subscribe instead of just simulate.
   - Add a broker-health route + UI indicator.
   - Document in `README.md` how to spin up the broker locally (and how Railway runs it).
   - Atomic commit(s).

4. **Phase 4 — Honest labeling**
   Like the financial tool's calibration card: a small "what's real, what's simulated" section in the dashboard. Don't claim more than is true.

5. **Push + deploy + verify on Railway.**

Estimated total: ~3 hours of focused work. Phases 1+2 can be one subagent dispatch; phase 3 is its own dispatch.

---

## Cross-project context (so a fresh session has the picture)

This is the third project Drew is polishing in the same "operator-terminal aesthetic + recruiter narrative + honest substantive feature" playbook:

| Project | Aesthetic | Substantive feature | Status |
|---|---|---|---|
| drewmalhotra.com | Operator-console (dark + mono + status bar + agent dock) | Phase 10 cost guardrails + Brivo training expansion | Shipped |
| financial-analysis-tool | Operator-terminal (Geist Sans + JetBrains Mono + green/red candles) | Backtest harness (49.5% honest, no-lookahead) | Shipped |
| smart-home-automation | (planned: same operator-terminal language) | (planned: real Mosquitto broker, manifesto-true) | **This file** |

The shared design language matters — when a recruiter tabs between drewmalhotra.com → financial-analysis-tool → smart-home-automation, they should feel one designer's hand across all three.

---

## Drew-actions still open (from prior sessions)

Not all are blockers for smart-home work, just don't forget them:

- [ ] Anthropic dashboard $10/mo spend cap + alerts at $5 / $9 (drewmalhotra.com Phase 10)
- [ ] Submit sitemap to Google Search Console (Phase 5)
- [ ] Enable Cloudflare Analytics Engine + redeploy worker (Phase 3 deferred → Phase 8 unblocker)
- [ ] LinkedIn recommendations from 2–3 former colleagues (Phase 6 unblocker)
- [ ] Reconcile the diverged-copy repos (`~/projects/*` April variants — orthogonal cleanup)

---

*Authored at session-end so a fresh session lands on its feet. Replace this file with `SUMMARY.md` after Option C ships, or delete it.*
