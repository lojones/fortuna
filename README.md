# Visualizr / Fortuna

Fortuna is a web application that lets authenticated users describe complex data scenarios through a conversational chat interface powered by Anthropic Claude. The AI iteratively clarifies requirements through back-and-forth dialogue, then generates rich, self-contained HTML visualizations. Users can publish, version, and iterate on their visualizations.

---

## Features

- **Conversational visualization creation** — Describe what you want; the AI asks clarifying questions until it has enough context to generate a complete visualization
- **Rich HTML output** — Self-contained HTML/CSS/JS documents rendered in a sandboxed iframe
- **Draft & publish versioning** — Keep a working draft, publish named versions, and restore any historical version
- **User management with admin approval** — New registrations require admin approval before access is granted
- **Role-based access control** — Admin and regular user roles with distinct permissions
- **Real-time streaming** — LLM responses stream token-by-token via WebSocket

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 (Composition API), Vite 5, Pinia, Vue Router 4, PrimeVue 4, Tailwind CSS 3 |
| Backend | Python 3.11+, FastAPI 0.111, Uvicorn |
| Database | MongoDB Atlas (async via Motor 3.4) |
| Auth | JWT (HS256, 8h expiry) + bcrypt |
| LLM | Anthropic Claude claude-opus-4-5 |
| Real-time | WebSocket (FastAPI built-in) |

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- A [MongoDB Atlas](https://www.mongodb.com/atlas) cluster (free tier works) with a database named `fortuna`
- An [Anthropic API key](https://console.anthropic.com/)

---

## Local Setup

### 1. Clone and configure environment

```bash
git clone https://github.com/lojones/fortuna.git
cd fortuna
```

Copy the example env file and fill in your values:

```bash
cp .env.example backend/.env
```

Edit `backend/.env`:

```env
# MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=fortuna

# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-32-byte-secret-here

JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=480

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Default admin credentials (created automatically on first boot)
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@fortuna.app
DEFAULT_ADMIN_PASSWORD=changeme123

# Frontend origin for CORS
FRONTEND_ORIGIN=http://localhost:5173
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend starts at **http://localhost:8000**. Interactive API docs are available at **http://localhost:8000/docs**.

On first startup, if no admin user exists in the database, one is created automatically using the `DEFAULT_ADMIN_*` credentials from your `.env`.

### 3. Frontend

```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```

The frontend starts at **http://localhost:5173**.

---

## First Run

1. Open http://localhost:5173
2. Click **Register** and create an account
3. Log in as the default admin (credentials from `backend/.env`) and approve the new user at **Admin → User Management**
4. Log in as the new user and start creating visualizations

---

## Project Structure

```
fortuna/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── requirements.txt
│   └── app/
│       ├── config.py            # Settings via Pydantic BaseSettings
│       ├── db/                  # MongoDB client + seed script
│       ├── models/              # Pydantic models (user, visualization, chat)
│       ├── routers/             # API route handlers + WebSocket
│       ├── services/            # Business logic + LLM integration
│       ├── middleware/          # JWT auth middleware
│       └── utils/               # HTML sanitizer
│
├── frontend/
│   ├── src/
│   │   ├── views/               # Page-level Vue components
│   │   ├── components/          # Reusable UI components
│   │   ├── stores/              # Pinia state (auth, chat, visualization)
│   │   ├── services/            # Axios API client + WebSocket service
│   │   └── router/              # Vue Router with auth guards
│   └── package.json
│
├── .env.example                 # Reference env file (no secrets)
└── docker-compose.yml           # Optional containerized setup
```

---

## API Overview

All REST endpoints are prefixed with `/api`. A WebSocket endpoint handles real-time chat streaming.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Authenticate and receive JWT |
| GET | `/api/users/me` | Current user profile |
| GET | `/api/visualizations` | List your visualizations |
| POST | `/api/visualizations` | Create a new visualization |
| GET | `/api/visualizations/{id}` | Get a visualization |
| POST | `/api/visualizations/{id}/publish` | Publish current draft |
| WS | `/api/chat/ws/{viz_id}?token=` | Real-time LLM chat stream |

Full interactive docs: http://localhost:8000/docs

---

## Docker (Optional)

```bash
# Requires backend/.env and frontend/.env to be configured first
docker-compose up --build
```

---

## Forgot Admin Password

bcrypt password hashes stored in MongoDB are **one-way** — they cannot be decrypted.  To regain access, use the included reset script to hash a new password and write it directly to the database.

```bash
cd backend
source venv/bin/activate   # or venv\Scripts\activate on Windows

# Interactive (prompts for username and new password)
python reset_admin_password.py

# Or supply the username explicitly (password will still be prompted, hidden)
python reset_admin_password.py --username admin
```

The script will:
1. Look up the user by username in MongoDB.
2. Hash the new password with bcrypt (work factor 12).
3. Update `hashed_password` and `updated_at` in the `users` collection.

You can then log in with the new password immediately.

> **Tip:** If you have also lost your `.env` values and cannot connect to MongoDB, update `MONGODB_URI` in `backend/.env` first, then run the script.

---

## Running Tests

```bash
cd backend
venv\Scripts\activate   # or source venv/bin/activate
pytest
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URI` | ✅ | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | ✅ | Database name (default: `fortuna`) |
| `JWT_SECRET_KEY` | ✅ | Random 32-byte hex string |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |
| `DEFAULT_ADMIN_USERNAME` | ✅ | Admin username for initial seed |
| `DEFAULT_ADMIN_EMAIL` | ✅ | Admin email for initial seed |
| `DEFAULT_ADMIN_PASSWORD` | ✅ | Admin password for initial seed |
| `FRONTEND_ORIGIN` | ✅ | CORS allowed origin (e.g. `http://localhost:5173`) |
| `JWT_EXPIRY_MINUTES` | ⬜ | Token lifetime in minutes (default: 480) |

---

## License

MIT
