# IoT-Based Smart Home Security System

An enterprise-grade, secure web-based Smart Home Security System developed for university Secure Software Engineering laboratory evaluation. This application enables authorized homeowners, family members, and administrators to monitor and control simulated IoT devices, configure reactive automation rules, review real-time security alerts, and inspect immutable audit logs with strict server-side Role-Based Access Control (RBAC).

---

## 1. Project Title
**IoT-Based Smart Home Security System (SHS Security Console)**

---

## 2. Project Objective
Develop a secure, modular web platform that simulates and manages a home IoT security ecosystem:
- Server-side Role-Based Access Control (RBAC) preventing unauthorized operations.
- Cryptographic IoT hardware and gateway authentication.
- Real-time sensor telemetry ingestion and state management.
- Dynamic automation rule evaluation (Trigger -> Condition -> Action).
- Security alert generation and event categorization.
- Cryptographically sound audit logging capturing all security-critical operations.
- Containerization and orchestration deployment templates for Docker and Kubernetes.

---

## 3. Key Features
- **User Authentication**: Secure authentication using `bcrypt` adaptive salt hashing.
- **Server-Side Authorization (RBAC)**: Three distinct roles (`HOMEOWNER`, `FAMILY_MEMBER`, `ADMIN`) strictly enforced on both web controllers and REST APIs.
- **Dedicated Smart Lock Interface**: Authorized Homeowners can lock/unlock; Family Members are strictly forbidden from unlocking the door (returns `HTTP 403` and logs a high-severity security incident).
- **IoT Device Management**: Administrator device registration, type categorization, and online/offline status control.
- **Telemetry & Sensor Monitoring**: Real-time monitoring of motion sensors, door contact sensors, and temperature readings.
- **Rule-Based Automation Engine**: Dynamic triggers (e.g. motion detected) evaluating conditions to execute hardware actions (e.g. porch light ON) and dispatch instant alerts.
- **Security Incident Logging**: Tamper-evident audit ledger capturing authentication events, device actions, unauthorized command attempts, and sensor breaches.
- **Zero-Trust Error Handling**: Generic error messages preventing information leakage (no stack traces, database schema reveals, or internal paths).
- **IoT Hardware Simulator**: Standalone CLI script and integrated laboratory test panel simulating realistic sensor events over HTTP REST.

---

## 4. Technology Stack
- **Backend**: Python 3.11+ / Flask 3.1
- **Database & ORM**: SQLite, SQLAlchemy, Flask-SQLAlchemy
- **Authentication & Security**: bcrypt, Secure Session Cookies (`HttpOnly`, `SameSite=Lax`), Content Security Policy (CSP)
- **Frontend**: HTML5, CSS3 (Enterprise Classic Theme, no neon/gaming visuals), Vanilla JavaScript, Jinja2 Templates
- **Testing**: pytest
- **Security Static Analysis**: Bandit
- **Containerization**: Docker (Hardened non-root image)
- **Orchestration**: Kubernetes manifests (Namespace, Secret, Deployment, Service)
- **CI/CD**: GitHub Actions workflow

---

## 5. Architecture Overview
```
                         ┌──────────────────┐
                         │   WEB CLIENT     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   FLASK ROUTER   │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
        ┌───────────────────────┐   ┌───────────────────────┐
        │  AUTH & RBAC ENGINE   │   │   REST API GATEWAY    │
        └───────────┬───────────┘   └───────────┬───────────┘
                    │                           │
                    ▼                           ▼
        ┌───────────────────────────────────────────────────┐
        │                 SERVICE LAYER                     │
        │  • DeviceService     • SensorService              │
        │  • AutomationService • AuditService               │
        │  • NotificationService                            │
        └───────────────────────────┬───────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │                PERSISTENT DATABASE                │
        │  • Users      • Devices       • SensorData        │
        │  • Rules      • SecurityLogs  • Notifications     │
        └───────────────────────────────────────────────────┘
```

---

## 6. Project Structure
```
smart-home-security/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI/CD pipeline
├── app/
│   ├── __init__.py              # Application factory & security headers
│   ├── models/                  # Relational database models
│   │   ├── __init__.py
│   │   ├── user.py              # User model & bcrypt hashing
│   │   ├── device.py            # Device metadata & key verification
│   │   ├── sensor_data.py       # Time-series telemetry records
│   │   ├── automation.py        # Automation rule schema
│   │   ├── security_log.py      # Immutable security audit logs
│   │   └── notification.py      # Alerts & notifications
│   ├── routes/                  # Controller blueprints & endpoints
│   │   ├── __init__.py
│   │   ├── auth.py              # Login & session management
│   │   ├── dashboard.py         # Real-time overview console
│   │   ├── devices.py           # Device enrollment & status
│   │   ├── lock.py              # Dedicated Smart Lock controller
│   │   ├── sensors.py           # Sensor telemetry & lab simulator UI
│   │   ├── automation.py        # Rule configuration & execution
│   │   ├── alerts.py            # Alerts feed & dismissal
│   │   ├── logs.py              # Security audit log viewer
│   │   ├── users.py             # Administrator account management
│   │   ├── settings.py          # User settings & security overview
│   │   └── api.py               # REST API endpoints
│   ├── services/                # Business logic & security validation
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication & RBAC decorators
│   │   ├── device_service.py    # Hardware state & command validation
│   │   ├── sensor_service.py    # Sensor ingestion & anomaly detection
│   │   ├── automation_service.py# Rule evaluation engine
│   │   ├── audit_service.py     # Secure logging with redaction
│   │   └── notification_service.py # Alert generation
│   ├── simulator/               # IoT device hardware simulation
│   │   ├── __init__.py
│   │   └── iot_simulator.py     # Network simulator client
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Enterprise classic styling
│   │   └── js/
│   │       └── main.js          # Core interactive script
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       ├── devices.html
│       ├── lock.html
│       ├── sensors.html
│       ├── automation.html
│       ├── alerts.html
│       ├── logs.html
│       ├── users.html
│       ├── settings.html
│       └── errors/              # 403, 404, 500 error pages
├── k8s/                         # Kubernetes manifests
│   ├── namespace.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── tests/                       # Automated pytest test suites
│   ├── conftest.py              # In-memory test db & fixtures
│   ├── test_auth.py             # Authentication tests
│   ├── test_devices.py          # Device registry tests
│   ├── test_lock.py             # Smart lock & RBAC bypass tests
│   ├── test_sensors.py          # Telemetry & anomaly tests
│   ├── test_automation.py       # Rule lifecycle tests
│   └── test_security_logs.py    # Audit logging & privacy tests
├── config.py                    # Environment configurations
├── Dockerfile                   # Hardened container image
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt             # Locked Python dependencies
├── run.py                       # Application entrypoint
├── run_simulator.py             # Standalone CLI hardware simulator
├── seed.py                      # Database initialization & default users
└── README.md
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.10+
- Git

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone <repository-url>
cd "sse end lab"
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

---

## 8. Database Initialization & Development Seed

Run the database seed script to generate tables and default development entities:
```bash
python seed.py
```

### Default Seed Accounts
| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `homeowner` | `HomeOwner#2026!` | `HOMEOWNER` | Full device monitoring, lock/unlock smart door, control lights, manage automation, view audit logs |
| `familymember`| `Family#2026!` | `FAMILY_MEMBER` | Monitor devices and sensors, control lights. **Forbidden from unlocking door or viewing audit logs.** |
| `admin` | `Admin#2026!` | `ADMIN` | Device registration, user management, system audit logs, lock/unlock door |

---

## 9. Running the Application

Start the Flask server:
```bash
python run.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000/login
```

---

## 10. Running the IoT Simulator

The application supports both in-browser simulation (via the Sensors page) and standalone execution.

### Standalone CLI Simulator:
```bash
# Trigger motion detection event in Living Room:
python run_simulator.py --motion

# Clear motion detection:
python run_simulator.py --clear-motion

# Simulate front door opened:
python run_simulator.py --open-door

# Simulate front door closed:
python run_simulator.py --close-door

# Report high temperature reading:
python run_simulator.py --temp 31.5

# Start autonomous simulation loop (generates realistic events every 5 seconds):
python run_simulator.py --loop 5
```

---

## 11. Running Automated Tests & Security Scans

### Run Pytest Test Suite:
```bash
pytest -v
```

### Run Bandit Static Security Scanner:
```bash
bandit -r app/
```

---

## 12. REST API Reference

| Method | Endpoint | Description | Role / Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/login` | Authenticate and obtain session | Public |
| `POST` | `/api/logout` | Terminate session | Authenticated |
| `GET` | `/api/devices` | List registered devices | Authenticated |
| `GET` | `/api/devices/<id>` | Retrieve single device status | Authenticated |
| `POST` | `/api/devices` | Register new device | `ADMIN` only |
| `PUT` | `/api/devices/<id>/status`| Update device network state | `ADMIN` or Gateway Token |
| `POST` | `/api/devices/<id>/lock` | Engage smart lock | `HOMEOWNER`, `ADMIN` |
| `POST` | `/api/devices/<id>/unlock` | Disengage smart lock | `HOMEOWNER`, `ADMIN` (403 for `FAMILY_MEMBER`) |
| `POST` | `/api/devices/<id>/command`| Execute generic command (`ON`, `OFF`)| Authenticated |
| `GET` | `/api/sensors` | Query telemetry readings | Authenticated |
| `POST` | `/api/sensors/event` | Ingest sensor reading from hardware | Device Key / Gateway Token |
| `GET` | `/api/automation` | List automation rules | Authenticated |
| `POST` | `/api/automation` | Create new rule | `HOMEOWNER`, `ADMIN` |
| `PUT` | `/api/automation/<id>`| Toggle rule active status | `HOMEOWNER`, `ADMIN` |
| `DELETE`| `/api/automation/<id>`| Delete automation rule | `HOMEOWNER`, `ADMIN` |
| `GET` | `/api/alerts` | List system notifications | Authenticated |
| `GET` | `/api/security-logs` | Query security audit ledger | `HOMEOWNER`, `ADMIN` |

---

## 13. Security Controls & Defenses

1. **Defense-in-Depth RBAC**: All authorization checks are enforced server-side. Direct API manipulation attempts bypass UI buttons but are rejected with `HTTP 403 Forbidden` and immediately logged.
2. **Cryptographic Protection**: Passwords hashed with `bcrypt` using 12 rounds of salted key-stretching.
3. **Sensitive Data Redaction**: The audit logging engine automatically intercepts and redacts passwords, tokens, and cryptographic keys before database persistence.
4. **Hardware Key Verification**: Sensor telemetry endpoints authenticate requests via SHA-256 pre-shared hardware keys (`X-Device-Key`) or gateway token validation.
5. **Security Headers**: Standard headers injected on all HTTP responses (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, strict `Content-Security-Policy`).
6. **Zero-Trust Error Handling**: Internal stack traces and file paths are suppressed.

---

## 14. Containerization (Docker)
Build the production container image:
```bash
docker build -t smart-home-security:v1.0 .
```
Run the container:
```bash
docker run -d -p 5000:5000 --name shs-app smart-home-security:v1.0
```

---

## 15. Kubernetes / Minikube Deployment
Apply the manifests to deploy the system with pod security contexts, resource quotas, and namespace isolation:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```
Verify the pod deployment:
```bash
kubectl get pods -n smart-home-security
```
