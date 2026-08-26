# Robo Raksha — Multi-Module Emergency Response Robot System

Robo Raksha is an autonomous emergency detection and risk management system built with 4 decoupled modules allowing parallel development by a 4-person team.

---

## 📁 Repository Structure & Roles

| Folder | Assignee | Role & Key Responsibilities |
|---|---|---|
| `firmware/` | **Builder A** | ESP32/Arduino code for sensors (flame, sound, vibration, distance), obstacle avoidance, camera streaming, and telemetry HTTP POST. |
| `server/` | **Person 1 (The Builder)** | Central Python server running on laptop. Receives telemetry, computes severity score (Flame=5, Sound=3, No Movement=4), manages countdown timer state machine, serves dashboard JSON, handles human actions, and triggers emergency comms dispatch. |
| `dashboard/` | **Person 2 & Person 3** | **Person 2**: HTML/CSS control room UI design (dark theme, normal/alert/dispatched states). **Person 3**: JavaScript polling, countdown ticker, and operator action dispatcher. |
| `comms/` | **Person 4** | SIM800L GSM module interface + Python script. Formats emergency SMS with real GPS coordinates, executes auto-dial, and manages predictive Wi-Fi fallback. |

---

## 🤝 Inter-Module JSON Contracts (`contracts/data_formats.json`)

### 1. Robot → Server (`POST http://localhost:5000/api/telemetry`)
```json
{
  "flame": 1,
  "sound": 87,
  "vibration": 0,
  "distance_cm": 45
}
```

### 2. Server → Dashboard (`GET http://localhost:5000/api/dashboard/status`)
```json
{
  "state": "ALERT",
  "event": "fire",
  "severity": 12,
  "clip_url": "http://localhost:5000/static/sample_stream.jpg",
  "timer_seconds": 45,
  "options": ["Dispatch fire", "Investigate", "False alarm"],
  "latest_telemetry": {
    "flame": 1,
    "sound": 87,
    "vibration": 0,
    "distance_cm": 45
  }
}
```

### 3. Dashboard → Server (`POST http://localhost:5000/api/dashboard/action`)
```json
{
  "action": "Investigate"
}
```

### 4. Server → Comms (`POST http://localhost:5001/api/comms/dispatch`)
```json
{
  "service": "fire",
  "lat": 12.9716,
  "lng": 77.5946,
  "message": "FIRE EMERGENCY DETECTED! Flame: 1, Sound: 87. Stationary for 90s. Severity Score: 12. Immediate assistance required."
}
```

---

## 🚀 How to Run Person 1's Server (The Builder)

### Step 1: Install Dependencies
```bash
pip install -r server/requirements.txt
```

### Step 2: Run Unit Tests
```bash
python server/test_server.py
```

### Step 3: Start Mock Comms Listener (Simulating Person 4 on Port 5001)
In terminal #1:
```bash
python server/mock_comms_listener.py
```

### Step 4: Start Main Server (Person 1 on Port 5000)
In terminal #2:
```bash
python server/app.py
```

### Step 5: Test Telemetry Stream (Simulating Robot)
In terminal #3:
- **Normal Telemetry**: `python server/mock_robot.py --mode normal`
- **Fire Emergency Telemetry**: `python server/mock_robot.py --mode fire`

---

## 📅 7-Week Development Roadmap

- **Weeks 1–2 (Ugly Working Version)**: Build simplest individual modules against fake data contracts.
- **Weeks 3–4 (Real Business Logic)**: Full sensor suite, live severity scoring, real polling, SIM800L AT commands.
- **Week 5 (Integration)**: Connect Robot → Server → Dashboard → Comms.
- **Week 6 (Patent Core Mechanisms)**: Live re-scoring loop, risk-decay formula, situation-specific menu, pre-generated SMS on Wi-Fi drop.
- **Week 7 (Failure Testing & Logging)**: Deliberate failure tests and quantitative performance logging.
