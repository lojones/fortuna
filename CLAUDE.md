# Fortuna Application Specification

## Version 1.0.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Repository Structure](#3-repository-structure)
4. [Technology Stack](#4-technology-stack)
5. [Database Design](#5-database-design)
6. [Backend Specification](#6-backend-specification)
7. [Frontend Specification](#7-frontend-specification)
8. [Authentication & Authorization](#8-authentication--authorization)
9. [LLM Integration](#9-llm-integration)
10. [Visualization Lifecycle](#10-visualization-lifecycle)
11. [API Specification](#11-api-specification)
12. [Environment Configuration](#12-environment-configuration)
13. [Security Requirements](#13-security-requirements)
14. [Error Handling](#14-error-handling)

---

## 1. Project Overview

**Application Name:** Fortuna

**Purpose:** Fortuna is a web application that allows authenticated users to describe complex information or data scenarios through a conversational chat interface powered by Anthropic Claude claude-opus-4-5. The LLM iteratively clarifies requirements through back-and-forth dialogue until it has sufficient understanding to generate a rich, self-contained HTML visualization. Users can publish visualizations, iterate on them, and manage versioned outputs.

**Key Capabilities:**
- User registration with admin approval workflow
- Role-based access (Admin, Regular User)
- Conversational visualization creation via LLM
- Iterative LLM clarification loop before generating HTML
- Draft/Publish versioning of visualizations
- In-app hosted visualization rendering
- Continue or branch existing visualization projects

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FORTUNA MONOREPO                      │
│                                                             │
│  ┌──────────────────┐         ┌──────────────────────────┐  │
│  │   FRONTEND       │         │       BACKEND            │  │
│  │   Vue 3 + Vite   │◄───────►│   Python / FastAPI       │  │
│  │   Port: 5173     │  REST   │   Port: 8000             │  │
│  └──────────────────┘  +WS    └──────────┬───────────────┘  │
│                                          │                   │
│                              ┌───────────▼───────────┐      │
│                              │   MongoDB Atlas        │      │
│                              │   Database: fortuna    │      │
│                              └───────────────────────┘      │
│                                          │                   │
│                              ┌───────────▼───────────┐      │
│                              │  Anthropic Claude      │      │
│                              │  claude-opus-4-5               │      │
│                              └───────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**Communication Pattern:**
- REST API for all CRUD and auth operations
- WebSocket connection for real-time streaming of LLM responses during chat

---

## 3. Repository Structure

```
fortuna/
├── README.md
├── .gitignore
├── .env.example
│
├── backend/
│   ├── main.py                         # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env                            # Backend env vars (gitignored)
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                   # Settings / env loading
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── mongodb.py              # MongoDB client & connection
│   │   │   └── init_db.py              # Seed default admin user
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User Pydantic models
│   │   │   ├── visualization.py        # Visualization Pydantic models
│   │   │   └── chat.py                 # Chat message Pydantic models
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # /api/auth/*
│   │   │   ├── users.py                # /api/users/*
│   │   │   ├── visualizations.py       # /api/visualizations/*
│   │   │   └── chat.py                 # /api/chat/* + WebSocket
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py         # JWT, password hashing
│   │   │   ├── user_service.py         # User CRUD
│   │   │   ├── visualization_service.py# Visualization CRUD
│   │   │   └── llm_service.py          # Anthropic API integration
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth_middleware.py      # JWT verification
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── html_sanitizer.py       # HTML output safety checks
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py
│       ├── test_users.py
│       ├── test_visualizations.py
│       └── test_llm_service.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── .env                            # Frontend env vars (gitignored)
│   │
│   ├── public/
│   │   └── favicon.ico
│   │
│   └── src/
│       ├── main.js
│       ├── App.vue
│       │
│       ├── assets/
│       │   └── styles/
│       │       ├── main.css
│       │       └── variables.css
│       │
│       ├── components/
│       │   ├── common/
│       │   │   ├── AppHeader.vue
│       │   │   ├── AppFooter.vue
│       │   │   ├── LoadingSpinner.vue
│       │   │   ├── ConfirmDialog.vue
│       │   │   └── NotificationToast.vue
│       │   │
│       │   ├── auth/
│       │   │   ├── LoginForm.vue
│       │   │   └── RegisterForm.vue
│       │   │
│       │   ├── chat/
│       │   │   ├── ChatWindow.vue
│       │   │   ├── ChatMessage.vue
│       │   │   ├── ChatInput.vue
│       │   │   └── TypingIndicator.vue
│       │   │
│       │   ├── visualization/
│       │   │   ├── VisualizationFrame.vue
│       │   │   ├── VisualizationCard.vue
│       │   │   ├── VersionBadge.vue
│       │   │   └── PublishButton.vue
│       │   │
│       │   └── admin/
│       │       ├── UserTable.vue
│       │       └── PendingApprovals.vue
│       │
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── RegisterView.vue
│       │   ├── DashboardView.vue
│       │   ├── ChatView.vue
│       │   ├── VisualizationView.vue
│       │   └── admin/
│       │       ├── AdminDashboardView.vue
│       │       └── UserManagementView.vue
│       │
│       ├── stores/
│       │   ├── auth.js                 # Pinia auth store
│       │   ├── chat.js                 # Pinia chat store
│       │   └── visualization.js        # Pinia visualization store
│       │
│       ├── router/
│       │   └── index.js                # Vue Router config
│       │
│       ├── services/
│       │   ├── api.js                  # Axios instance + interceptors
│       │   ├── authService.js
│       │   ├── chatService.js
│       │   ├── visualizationService.js
│       │   └── websocketService.js     # WS client wrapper
│       │
│       └── utils/
│           ├── dateFormatter.js
│           └── htmlSandbox.js          # Safe iframe rendering helper
│
└── docker-compose.yml                  # Optional local dev orchestration
```

---

## 4. Technology Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.111+ |
| ASGI Server | Uvicorn | 0.30+ |
| Database ODM | Motor (async MongoDB) | 3.4+ |
| Authentication | python-jose (JWT) | 3.3+ |
| Password Hashing | passlib[bcrypt] | 1.7+ |
| LLM Client | anthropic | latest |
| Data Validation | Pydantic v2 | 2.7+ |
| WebSockets | FastAPI WebSocket (built-in) | - |
| Environment | python-dotenv | 1.0+ |
| Testing | pytest + pytest-asyncio | - |

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Vue 3 (Composition API) | 3.4+ |
| Build Tool | Vite | 5.x |
| State Management | Pinia | 2.x |
| Router | Vue Router | 4.x |
| HTTP Client | Axios | 1.7+ |
| UI Component Lib | PrimeVue or Vuetify 3 | latest |
| CSS Framework | Tailwind CSS | 3.x |
| WebSocket | Native browser WebSocket | - |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Database | MongoDB Atlas (Cloud Cluster) |
| LLM API | Anthropic Claude claude-opus-4-5 |

---

## 5. Database Design

**Database Name:** `fortuna`

### Collections

---

#### 5.1 `users` Collection

```json
{
  "_id": "ObjectId",
  "username": "string (unique, indexed)",
  "email": "string (unique, indexed)",
  "hashed_password": "string",
  "role": "string (enum: 'admin' | 'user')",
  "status": "string (enum: 'pending' | 'active' | 'suspended')",
  "created_at": "datetime (UTC)",
  "updated_at": "datetime (UTC)",
  "approved_by": "ObjectId | null (ref: users._id)",
  "approved_at": "datetime | null"
}
```

**Indexes:**
- `username`: unique
- `email`: unique
- `status`: standard (for admin queries on pending users)

**Notes:**
- On application boot, if no user with `role: 'admin'` exists, a seed script creates the default admin user using credentials from environment variables.
- `status: 'pending'` means account exists but cannot log in until an admin sets status to `'active'`.

---

#### 5.2 `visualizations` Collection

```json
{
  "_id": "ObjectId",
  "owner_id": "ObjectId (ref: users._id, indexed)",
  "title": "string",
  "description": "string",
  "status": "string (enum: 'draft' | 'published')",
  "current_draft_html": "string (full HTML content)",
  "published_versions": [
    {
      "version_number": "integer",
      "html_content": "string",
      "published_at": "datetime (UTC)",
      "published_by": "ObjectId (ref: users._id)"
    }
  ],
  "latest_published_version": "integer | null",
  "chat_session_id": "ObjectId (ref: chat_sessions._id)",
  "created_at": "datetime (UTC)",
  "updated_at": "datetime (UTC)"
}
```

**Indexes:**
- `owner_id`: standard
- `status`: standard
- `owner_id + status`: compound

---

#### 5.3 `chat_sessions` Collection

```json
{
  "_id": "ObjectId",
  "visualization_id": "ObjectId (ref: visualizations._id, indexed)",
  "owner_id": "ObjectId (ref: users._id, indexed)",
  "messages": [
    {
      "message_id": "string (uuid)",
      "role": "string (enum: 'user' | 'assistant')",
      "content": "string",
      "message_type": "string (enum: 'chat' | 'clarification' | 'html_output')",
      "timestamp": "datetime (UTC)"
    }
  ],
  "llm_state": "string (enum: 'clarifying' | 'generating' | 'complete')",
  "created_at": "datetime (UTC)",
  "updated_at": "datetime (UTC)"
}
```

**Notes:**
- `llm_state` tracks the current phase of the LLM conversation loop.
- `message_type: 'html_output'` marks the message where the LLM returned generated HTML.
- Each visualization has exactly one chat session. The session is appended to over the life of the visualization (edits continue the same session thread).

---

## 6. Backend Specification

### 6.1 Application Entry Point (`main.py`)

```
- Create FastAPI application instance
- Configure CORS middleware to allow frontend origin
- Mount all routers under /api prefix
- Add WebSocket route for chat streaming
- On startup event: run init_db() to ensure default admin exists
- Run with Uvicorn on host 0.0.0.0, port 8000
```

### 6.2 Configuration (`app/config.py`)

Load from environment variables using Pydantic `BaseSettings`:

```
- MONGODB_URI: str               # MongoDB Atlas connection string
- MONGODB_DB_NAME: str = "fortuna"
- JWT_SECRET_KEY: str            # Strong random secret
- JWT_ALGORITHM: str = "HS256"
- JWT_EXPIRY_MINUTES: int = 480  # 8 hours
- ANTHROPIC_API_KEY: str
- DEFAULT_ADMIN_USERNAME: str
- DEFAULT_ADMIN_EMAIL: str
- DEFAULT_ADMIN_PASSWORD: str
- FRONTEND_ORIGIN: str           # e.g. http://localhost:5173
```

### 6.3 Database Layer (`app/db/mongodb.py`)

```
- Maintain a single Motor AsyncIOMotorClient instance (singleton)
- Expose get_database() dependency for FastAPI injection
- Collections accessed: users, visualizations, chat_sessions
```

### 6.4 Database Initialization (`app/db/init_db.py`)

```
FUNCTION init_db():
  db = get_database()
  admin_count = await db.users.count_documents({"role": "admin"})
  IF admin_count == 0:
    hash password from DEFAULT_ADMIN_PASSWORD
    insert user document:
      username: DEFAULT_ADMIN_USERNAME
      email: DEFAULT_ADMIN_EMAIL
      hashed_password: <hashed>
      role: "admin"
      status: "active"
      created_at: now()
    LOG "Default admin user created"
  ELSE:
    LOG "Admin user already exists, skipping seed"
```

### 6.5 Models (`app/models/`)

#### `user.py`

```python
# Pydantic models:

UserBase:
  username: str
  email: EmailStr

UserCreate(UserBase):
  password: str  # min 8 chars

UserInDB(UserBase):
  id: str          # mapped from _id
  role: Literal["admin", "user"]
  status: Literal["pending", "active", "suspended"]
  created_at: datetime
  updated_at: datetime

UserPublic(UserBase):
  id: str
  role: str
  status: str
  created_at: datetime

AdminUserUpdate:
  status: Optional[Literal["active", "suspended"]]
  role: Optional[Literal["admin", "user"]]
```

#### `visualization.py`

```python
PublishedVersion:
  version_number: int
  html_content: str
  published_at: datetime
  published_by: str

VisualizationBase:
  title: str
  description: Optional[str]

VisualizationCreate(VisualizationBase): pass

VisualizationInDB(VisualizationBase):
  id: str
  owner_id: str
  status: Literal["draft", "published"]
  current_draft_html: Optional[str]
  published_versions: List[PublishedVersion]
  latest_published_version: Optional[int]
  chat_session_id: str
  created_at: datetime
  updated_at: datetime

VisualizationPublic(VisualizationInDB): pass
```

#### `chat.py`

```python
ChatMessage:
  message_id: str
  role: Literal["user", "assistant"]
  content: str
  message_type: Literal["chat", "clarification", "html_output"]
  timestamp: datetime

ChatSessionInDB:
  id: str
  visualization_id: str
  owner_id: str
  messages: List[ChatMessage]
  llm_state: Literal["clarifying", "generating", "complete"]
  created_at: datetime
  updated_at: datetime

UserChatInput:
  content: str
```

### 6.6 Services

#### `auth_service.py`

```
FUNCTION hash_password(plain_password: str) -> str:
  use passlib bcrypt to hash and return

FUNCTION verify_password(plain_password: str, hashed_password: str) -> bool:
  use passlib bcrypt to verify

FUNCTION create_access_token(data: dict, expires_delta: timedelta) -> str:
  encode JWT with HS256, include exp claim

FUNCTION decode_access_token(token: str) -> dict:
  decode and verify JWT, raise HTTPException 401 if invalid/expired

DEPENDENCY get_current_user(token from Bearer header) -> UserInDB:
  decode token, fetch user from DB, raise 401 if not found
  raise 403 if user status != "active"

DEPENDENCY require_admin(current_user from get_current_user) -> UserInDB:
  raise 403 if current_user.role != "admin"
```

#### `user_service.py`

```
FUNCTION create_user(db, user_create: UserCreate) -> UserInDB:
  check username uniqueness -> raise 400 if taken
  check email uniqueness -> raise 400 if taken
  hash password
  insert with role="user", status="pending"
  return created user

FUNCTION get_user_by_username(db, username: str) -> UserInDB | None
FUNCTION get_user_by_id(db, user_id: str) -> UserInDB | None
FUNCTION get_all_users(db) -> List[UserInDB]
FUNCTION get_pending_users(db) -> List[UserInDB]

FUNCTION update_user_status(db, user_id: str, status: str, approved_by_id: str) -> UserInDB:
  update status field
  if status == "active": set approved_by and approved_at
  return updated user

FUNCTION update_user_role(db, user_id: str, role: str) -> UserInDB
```

#### `visualization_service.py`

```
FUNCTION create_visualization(db, owner_id: str, title: str, description: str) -> VisualizationInDB:
  create empty chat_session document first
  create visualization document referencing chat_session_id
  return visualization

FUNCTION get_visualizations_by_owner(db, owner_id: str) -> List[VisualizationInDB]

FUNCTION get_visualization_by_id(db, viz_id: str) -> VisualizationInDB | None

FUNCTION get_most_recent_visualization(db, owner_id: str) -> VisualizationInDB | None:
  query by owner_id, sort by updated_at DESC, limit 1

FUNCTION update_draft_html(db, viz_id: str, html_content: str) -> VisualizationInDB:
  update current_draft_html field
  set updated_at = now()

FUNCTION publish_visualization(db, viz_id: str, publisher_id: str) -> VisualizationInDB:
  read current_draft_html
  if current_draft_html is None: raise 400 "No draft to publish"
  increment version number (len(published_versions) + 1)
  append to published_versions array
  set latest_published_version = new version number
  set status = "published"
  set updated_at = now()
  return updated visualization

FUNCTION get_chat_session(db, session_id: str) -> ChatSessionInDB | None

FUNCTION append_message_to_session(db, session_id: str, message: ChatMessage):
  push message to messages array
  set updated_at = now()

FUNCTION update_llm_state(db, session_id: str, state: str):
  update llm_state field
```

#### `llm_service.py`

This is the most critical service. It manages the conversation loop with Claude.

```
SYSTEM_PROMPT = """
You are Fortuna's visualization assistant. Your role is to help users 
create rich, self-contained HTML visualizations of complex information.

You operate in two phases:
1. CLARIFICATION PHASE: Ask targeted questions to understand exactly 
   what the user wants to visualize. Ask ONE to THREE questions at a time.
   When you have enough information to create a complete, accurate 
   visualization, transition to the generation phase.

2. GENERATION PHASE: Generate a complete, self-contained HTML document
   that includes all CSS and JavaScript inline. The visualization should
   be visually rich, accurate to the user's requirements, and render 
   correctly in a sandboxed iframe.

CRITICAL RULES:
- During clarification, respond ONLY with questions and conversational text.
  Do NOT include any HTML code blocks during clarification.
- When you have enough information, respond with EXACTLY this marker on 
  its own line followed by the complete HTML:
  <<<VISUALIZATION_READY>>>
  [complete html document here]
- The HTML must be a complete document starting with <!DOCTYPE html>
- All assets must be inline (no external CDN links that could break in sandbox)
  EXCEPTION: You may use well-known stable CDNs like Chart.js, D3.js from 
  official CDN URLs for complex charting needs.
- When editing an existing visualization, respond with <<<VISUALIZATION_READY>>>
  followed by the complete updated HTML document incorporating the changes.
"""

CLASS LLMService:

  FUNCTION __init__(self):
    self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

  ASYNC FUNCTION process_message(
    self,
    session: ChatSessionInDB,
    new_user_message: str,
    websocket: WebSocket
  ) -> tuple[str, bool, str | None]:
    """
    Returns: (assistant_response_text, is_visualization_ready, html_content_or_none)
    Streams response tokens to websocket in real time.
    """
    
    # Build message history for Claude
    messages = []
    FOR msg in session.messages:
      IF msg.role in ["user", "assistant"] AND msg.message_type != "html_output":
        messages.append({"role": msg.role, "content": msg.content})
      ELIF msg.message_type == "html_output":
        # Include a summary reference, not the full HTML, to save tokens
        messages.append({
          "role": "assistant", 
          "content": "[Previous visualization was generated and shown to user]"
        })
    
    # Append current user message
    messages.append({"role": "user", "content": new_user_message})
    
    # Stream from Claude
    full_response = ""
    async with self.client.messages.stream(
      model="claude-opus-4-5",
      max_tokens=8192,
      system=SYSTEM_PROMPT,
      messages=messages
    ) as stream:
      async for text_chunk in stream.text_stream:
        full_response += text_chunk
        await websocket.send_json({
          "type": "chunk",
          "content": text_chunk
        })
    
    # Detect if visualization is ready
    IF "<<<VISUALIZATION_READY>>>" in full_response:
      parts = full_response.split("<<<VISUALIZATION_READY>>>", 1)
      pre_text = parts[0].strip()
      html_content = parts[1].strip()
      await websocket.send_json({"type": "visualization_ready", "html": html_content})
      RETURN (pre_text, True, html_content)
    ELSE:
      await websocket.send_json({"type": "complete"})
      RETURN (full_response, False, None)
```

### 6.7 Routers

#### `routers/auth.py` — `/api/auth`

```
POST /api/auth/login
  Body: { username: str, password: str }
  Logic:
    1. Fetch user by username
    2. Verify password
    3. Check status == "active" (raise 403 with message "Account pending approval" if pending)
    4. Generate JWT
    5. Return { access_token, token_type: "bearer", user: UserPublic }

POST /api/auth/register
  Body: UserCreate
  Logic:
    1. Call user_service.create_user()
    2. Return { message: "Registration successful. Awaiting admin approval.", user: UserPublic }
    NOTE: No JWT issued at registration. User must wait for approval.
```

#### `routers/users.py` — `/api/users`

```
GET /api/users/me
  Auth: Required (any active user)
  Returns: UserPublic of current user

GET /api/users
  Auth: Admin only
  Returns: List[UserPublic] of all users

GET /api/users/pending
  Auth: Admin only
  Returns: List[UserPublic] where status == "pending"

PATCH /api/users/{user_id}/approve
  Auth: Admin only
  Logic: Set status = "active", set approved_by = current admin id
  Returns: Updated UserPublic

PATCH /api/users/{user_id}/suspend
  Auth: Admin only
  Logic: Set status = "suspended"
  Returns: Updated UserPublic

PATCH /api/users/{user_id}/role
  Auth: Admin only
  Body: { role: "admin" | "user" }
  Returns: Updated UserPublic

DELETE /api/users/{user_id}
  Auth: Admin only
  Logic: Hard delete user (consider cascade implications)
  Returns: { message: "User deleted" }
```

#### `routers/visualizations.py` — `/api/visualizations`

```
GET /api/visualizations
  Auth: Required
  Logic: Return all visualizations owned by current_user
  Returns: List[VisualizationPublic]

GET /api/visualizations/recent
  Auth: Required
  Logic: Return most recent visualization for current user
  Returns: VisualizationPublic | null

POST /api/visualizations
  Auth: Required
  Body: { title: str, description: Optional[str] }
  Logic:
    1. Create visualization + linked empty chat_session
    2. Return new VisualizationPublic with chat_session_id

GET /api/visualizations/{viz_id}
  Auth: Required
  Logic:
    1. Fetch visualization
    2. Verify owner_id == current_user.id (raise 403 otherwise)
  Returns: VisualizationPublic

GET /api/visualizations/{viz_id}/chat
  Auth: Required
  Logic:
    1. Fetch visualization, verify ownership
    2. Fetch linked chat_session
  Returns: ChatSessionInDB (with messages)

POST /api/visualizations/{viz_id}/publish
  Auth: Required
  Logic:
    1. Fetch visualization, verify ownership
    2. Verify current_draft_html is not null/empty
    3. Call visualization_service.publish_visualization()
  Returns: Updated VisualizationPublic

GET /api/visualizations/{viz_id}/versions/{version_number}
  Auth: Required
  Logic:
    1. Fetch visualization, verify ownership
    2. Find matching version in published_versions
  Returns: { version_number, html_content, published_at }
```

#### `routers/chat.py` — `/api/chat`

```
WebSocket: /api/chat/ws/{viz_id}
  Auth: JWT token passed as query parameter ?token=<jwt>
  
  ON CONNECT:
    1. Validate token, get current_user
    2. Fetch visualization by viz_id
    3. Verify ownership (close with 4003 if unauthorized)
    4. Fetch chat_session linked to visualization
    5. Send initial state: { type: "init", session: ChatSessionInDB }
  
  ON MESSAGE (JSON: { content: str }):
    1. Validate content is non-empty string
    2. Create user ChatMessage, append to session in DB
    3. Call llm_service.process_message(session, content, websocket)
       (This streams chunks back as { type: "chunk", content: "..." })
    4. After stream completes:
       a. IF is_visualization_ready:
          - Create assistant message with message_type="html_output", content=html_content
          - Append to session
          - Update visualization current_draft_html = html_content
          - Update llm_state = "complete"
          - Send: { type: "visualization_ready", html: html_content, viz_id: viz_id }
       b. ELSE (still clarifying):
          - Create assistant message with message_type="clarification"
          - Append to session
          - Update llm_state = "clarifying"
          - Send: { type: "complete" }
  
  ON DISCONNECT:
    Clean up as needed
```

---

## 7. Frontend Specification

### 7.1 Router Configuration (`router/index.js`)

```
Routes:
  /login                  -> LoginView          (guest only)
  /register               -> RegisterView        (guest only)
  /dashboard              -> DashboardView       (auth required)
  /chat/:vizId            -> ChatView            (auth required)
  /visualization/:vizId   -> VisualizationView   (auth required)
  /admin                  -> AdminDashboardView  (admin required)
  /admin/users            -> UserManagementView  (admin required)
  /                       -> redirect to /dashboard if auth, else /login

Navigation Guards:
  - beforeEach: check auth store for valid token
  - Redirect unauthenticated users to /login
  - Redirect authenticated non-admins away from /admin routes
  - Redirect authenticated users away from /login and /register
```

### 7.2 Pinia Stores

#### `stores/auth.js`

```
State:
  user: UserPublic | null
  token: string | null
  isLoading: boolean
  error: string | null

Getters:
  isAuthenticated: computed => !!token && !!user
  isAdmin: computed => user?.role === "admin"
  isPending: computed => user?.status === "pending"

Actions:
  login(username, password):
    POST /api/auth/login
    Store token in localStorage and state
    Store user in state
    Navigate to /dashboard

  register(username, email, password):
    POST /api/auth/register
    Show success message about pending approval
    Navigate to /login

  logout():
    Clear localStorage
    Clear state
    Navigate to /login

  fetchCurrentUser():
    GET /api/users/me
    Update user in state

  initializeAuth():
    On app mount, read token from localStorage
    If token exists, call fetchCurrentUser()
    If 401, clear token and navigate to /login
```

#### `stores/chat.js`

```
State:
  currentSession: ChatSessionInDB | null
  isConnected: boolean
  isStreaming: boolean
  streamBuffer: string
  currentVizId: string | null
  error: string | null

Actions:
  connectToChat(vizId):
    Initialize WebSocket via websocketService
    Set currentVizId
    Register event handlers (onMessage, onChunk, onVisualizationReady, onError)
    Set isConnected = true on open

  sendMessage(content):
    Validate not empty
    Send via WebSocket: { content }
    Set isStreaming = true
    Append user message optimistically to currentSession.messages

  handleChunk(chunk):
    Append chunk to streamBuffer
    Update last assistant message in currentSession.messages

  handleComplete():
    Set isStreaming = false
    Clear streamBuffer
    Finalize last assistant message

  handleVisualizationReady(html, vizId):
    Set isStreaming = false
    Call visualization store to update draft HTML
    Navigate to /visualization/:vizId

  disconnectFromChat():
    Close WebSocket
    Set isConnected = false

  loadSession(vizId):
    GET /api/visualizations/:vizId/chat
    Set currentSession
```

#### `stores/visualization.js`

```
State:
  visualizations: List[VisualizationPublic]
  currentVisualization: VisualizationPublic | null
  isLoading: boolean
  error: string | null

Actions:
  fetchMyVisualizations():
    GET /api/visualizations
    Set visualizations

  fetchVisualization(vizId):
    GET /api/visualizations/:vizId
    Set currentVisualization

  fetchRecentVisualization():
    GET /api/visualizations/recent
    Return result

  createVisualization(title, description):
    POST /api/visualizations
    Add to visualizations list
    Return new visualization

  updateDraftHtml(html):
    Update currentVisualization.current_draft_html locally

  publishVisualization(vizId):
    POST /api/visualizations/:vizId/publish
    Update currentVisualization with response
    Show success notification
```

### 7.3 Views

#### `LoginView.vue`

```
Template:
  - Centered card layout
  - App logo and "Fortuna" title
  - LoginForm component
  - Link to /register

LoginForm.vue:
  - Username input
  - Password input (with show/hide toggle)
  - Submit button with loading state
  - Error message display (inline, below form)
  - Special handling for "pending approval" error: 
    show distinct message "Your account is pending admin approval"
```

#### `RegisterView.vue`

```
Template:
  - Centered card layout
  - RegisterForm component
  - Link back to /login

RegisterForm.vue:
  - Username input
  - Email input
  - Password input (min 8 chars, strength indicator)
  - Confirm password input
  - Submit button with loading state
  - On success: show "Registration submitted. Awaiting admin approval." 
    banner and redirect to /login after 3 seconds
```

#### `DashboardView.vue`

```
Template:
  - AppHeader with user info and logout button
  - Welcome message: "Welcome, {username}"
  - Two primary action cards:
  
    CARD 1: "Create New Visualization"
      - Icon: sparkles/chart icon
      - Description: "Start a new visualization from scratch"
      - Button: "New Visualization" -> onClick: showNewVizModal()
  
    CARD 2: "Continue Recent Visualization"
      - Icon: edit icon
      - Description: Shows title of most recent visualization if exists
      - Button: "Continue" -> onClick: continueRecentVisualization()
      - If no recent visualization: button is disabled with tooltip "No visualizations yet"
  
  - Section: "My Visualizations" (list of VisualizationCard components)
    - Each card shows: title, status badge, last updated, publish button
    - Click card -> navigate to /visualization/:vizId

  - If admin: show "Admin Panel" button in header linking to /admin

Modal: NewVisualizationModal
  - Title input (required)
  - Description input (optional, textarea)
  - Create button -> calls createVisualization() then navigates to /chat/:vizId

Logic:
  ON mount:
    fetchMyVisualizations()
    fetchRecentVisualization() -> store in local ref
```

#### `ChatView.vue`

```
Template:
  Layout: two-pane or single pane based on llm_state
  
  LEFT/MAIN PANE: ChatWindow component
    - Displays all messages from currentSession.messages
    - ChatMessage component for each message:
      - User messages: right-aligned, distinct background
      - Assistant messages: left-aligned, with Fortuna avatar
    - TypingIndicator shown when isStreaming == true
    - Stream buffer content rendered in real-time as last assistant message
    - ChatInput at bottom (disabled while isStreaming)
  
  HEADER BAR:
    - Visualization title
    - "Back to Dashboard" link
    - Status chip: "Clarifying..." or "Generating..." based on llm_state

Logic:
  ON mount(vizId from route params):
    fetchVisualization(vizId)
    loadSession(vizId)
    connectToChat(vizId)
  
  ON unmount:
    disconnectFromChat()
  
  WHEN handleVisualizationReady fires:
    Router push to /visualization/:vizId
```

#### `VisualizationView.vue`

```
Template:
  HEADER BAR:
    - Visualization title
    - Status badge (draft/published, version number)
    - "Edit" button (pencil icon)
    - "Publish" button (cloud-upload icon) - only if status == 'draft' or new changes
    - "Back to Dashboard" link

  MAIN CONTENT AREA:
    - VisualizationFrame component:
      Renders current_draft_html in a sandboxed iframe
      iframe attributes: sandbox="allow-scripts allow-same-origin"
      width: 100%, height: calc(100vh - header height)
  
  VERSION HISTORY SIDEBAR (collapsible):
    - List of published_versions
    - Each entry: "Version {n}" + published_at date
    - Click version -> show that version's html in iframe (read-only mode)
    - "Restore as Draft" button per version

Logic:
  ON mount(vizId from route params):
    fetchVisualization(vizId)
  
  Edit button click:
    Navigate to /chat/:vizId
    (Chat will load existing session and continue from where it left off)
  
  Publish button click:
    Show ConfirmDialog: "Publish this visualization as Version {n+1}?"
    On confirm: publishVisualization(vizId)
    Show success toast

  VisualizationFrame.vue:
    Props: htmlContent: string
    Uses iframe with srcdoc binding
    Watches htmlContent prop, updates iframe srcdoc
    Emits: 'loaded' event when iframe load event fires
```

#### `AdminDashboardView.vue`

```
Template:
  - AppHeader
  - Stats cards: Total Users, Pending Approvals, Active Users
  - PendingApprovals component (prominent, at top)
  - UserTable component (all users)
  - Navigation to /admin/users for full management
```

#### `UserManagementView.vue`

```
Template:
  - Filter tabs: All | Pending | Active | Suspended
  - UserTable component with current filter applied
  - Each row actions: Approve / Suspend / Make Admin / Remove Admin / Delete

UserTable.vue:
  Props: users: List[UserPublic], filter: string
  For each user row:
    - Username, Email, Role badge, Status badge, Created date
    - Action buttons (context-sensitive based on current status/role)
    - Approve button -> PATCH /api/users/:id/approve
    - Suspend button -> PATCH /api/users/:id/suspend  
    - Toggle Admin button -> PATCH /api/users/:id/role

PendingApprovals.vue:
  - Shows count badge
  - Lists pending users with quick-approve and reject (suspend) buttons
  - Polls GET /api/users/pending every 30 seconds for updates
```

### 7.4 WebSocket Service (`services/websocketService.js`)

```
CLASS WebSocketService:

  FUNCTION connect(vizId, token, handlers):
    url = `ws://${API_BASE_HOST}/api/chat/ws/${vizId}?token=${token}`
    this.ws = new WebSocket(url)
    
    this.ws.onmessage = (event):
      data = JSON.parse(event.data)
      SWITCH data.type:
        "init"                -> handlers.onInit(data.session)
        "chunk"               -> handlers.onChunk(data.content)
        "complete"            -> handlers.onComplete()
        "visualization_ready" -> handlers.onVisualizationReady(data.html, data.viz_id)
        "error"               -> handlers.onError(data.message)
    
    this.ws.onclose = (event):
      handlers.onClose(event.code)
    
    this.ws.onerror = (event):
      handlers.onError("WebSocket connection error")
  
  FUNCTION sendMessage(content):
    IF this.ws?.readyState == WebSocket.OPEN:
      this.ws.send(JSON.stringify({ content }))
    ELSE:
      throw Error("WebSocket not connected")
  
  FUNCTION disconnect():
    this.ws?.close(1000, "User navigated away")
```

---

## 8. Authentication & Authorization

### 8.1 JWT Token Flow

```
1. User POSTs credentials to /api/auth/login
2. Backend validates credentials and user status
3. Backend returns signed JWT (HS256) containing:
   { sub: user_id, username: username, role: role, exp: expiry }
4. Frontend stores token in localStorage under key "fortuna_token"
5. Frontend includes token in all API requests:
   Header: Authorization: Bearer <token>
6. For WebSocket: token passed as query param ?token=<jwt>
7. Backend middleware validates token on every protected route
```

### 8.2 Authorization Matrix

| Action | Unauthenticated | Active User | Admin |
|--------|----------------|-------------|-------|
| Register | ✅ | ✅ | ✅ |
| Login | ✅ | ✅ | ✅ |
| View own visualizations | ❌ | ✅ | ✅ |
| Create visualization | ❌ | ✅ | ✅ |
| Edit own visualization | ❌ | ✅ | ✅ |
| Edit other's visualization | ❌ | ❌ | ❌ |
| Publish own visualization | ❌ | ✅ | ✅ |
| View user list | ❌ | ❌ | ✅ |
| Approve users | ❌ | ❌ | ✅ |
| Suspend users | ❌ | ❌ | ✅ |
| Change user roles | ❌ | ❌ | ✅ |

### 8.3 Pending User Behavior

- Pending users can register but cannot log in.
- Login attempt by pending user returns HTTP 403 with body:
  `{ "detail": "Account pending admin approval" }`
- Frontend displays this as a distinct informational message (not an error).

---

## 9. LLM Integration

### 9.1 Conversation State Machine

```
States: clarifying -> generating -> complete -> (edit restarts at clarifying)

CLARIFYING:
  - LLM responds with questions
  - message_type = "clarification"
  - No HTML generated
  - User continues answering
  - Loop until LLM includes <<<VISUALIZATION_READY>>> marker

GENERATING (transitional):
  - LLM response contains <<<VISUALIZATION_READY>>> marker
  - HTML extracted from response
  - Stored as current_draft_html
  - State moves to COMPLETE

COMPLETE:
  - HTML draft exists
  - User views visualization
  - User can click EDIT to re-enter CLARIFYING state
  - New chat messages from user continue the thread
  - LLM has context of previous conversation + "[Previous visualization was shown]" 
  - When LLM again decides changes are complete: <<<VISUALIZATION_READY>>> 
    triggers new HTML update, replaces current_draft_html
```

### 9.2 Message History Strategy

To avoid excessive token usage when the HTML becomes large, the following strategy is applied when building the Claude message history:

```
FOR each message in session.messages:
  IF message_type == "html_output":
    Include as: { role: "assistant", content: "[Visualization was generated and shown to user. User is now requesting changes.]" }
  ELSE:
    Include as-is with role and content
```

This keeps the conversation coherent without re-sending large HTML documents in every turn.

### 9.3 HTML Extraction

```
FUNCTION extract_html_from_response(response: str) -> tuple[str, str | None]:
  IF "<<<VISUALIZATION_READY>>>" in response:
    parts = response.split("<<<VISUALIZATION_READY>>>", maxsplit=1)
    pre_message = parts[0].strip()
    html = parts[1].strip()
    
    # Validate that it looks like an HTML document
    IF html.lower().startswith("<!doctype") OR html.lower().startswith("<html"):
      RETURN (pre_message, html)
    ELSE:
      LOG warning "LLM returned VISUALIZATION_READY marker but invalid HTML"
      RETURN (response, None)  # Treat as clarification
  ELSE:
    RETURN (response, None)
```

---

## 10. Visualization Lifecycle

```
STATE DIAGRAM:

[User Clicks "New Visualization"]
           |
           v
[Create Visualization in DB] -> status: "draft", current_draft_html: null
           |
           v
[Navigate to ChatView] -> WebSocket connected
           |
           v
[User sends initial description]
           |
           v
[LLM: Clarification Loop] <----+
  - Ask 1-3 clarifying questions  |
  - User answers               ----+
           |
           | (LLM satisfied)
           v
[LLM generates HTML with <<<VISUALIZATION_READY>>>]
           |
           v
[Update current_draft_html in DB]
           |
           v
[Navigate to VisualizationView] -> iframe renders HTML
           |
    +------+------+
    |             |
    v             v
[User clicks    [User clicks
 "Edit"]         "Publish"]
    |             |
    v             v
[Navigate to  [version++, append to
 ChatView]     published_versions,
 (continue     status stays "draft"
  existing      until user publishes
  session)]     again]
```

### 10.1 Published Versions

- Publishing does NOT remove the draft.
- `current_draft_html` is copied into `published_versions` with incremented version number.
- Users can view any historical published version in the sidebar.
- A "Restore as Draft" action copies an old version back to `current_draft_html`.
- Visualization `status` field reflects whether any published version exists.

---

## 11. API Specification

### Base URL: `/api`

### 11.1 Authentication Endpoints

```
POST /auth/login
  Request:  { username: string, password: string }
  Response 200: { access_token: string, token_type: "bearer", user: UserPublic }
  Response 401: { detail: "Invalid credentials" }
  Response 403: { detail: "Account pending admin approval" }
  Response 403: { detail: "Account suspended" }

POST /auth/register
  Request:  { username: string, email: string, password: string }
  Response 201: { message: string, user: UserPublic }
  Response 400: { detail: "Username already taken" }
  Response 400: { detail: "Email already registered" }
  Response 422: Validation error
```

### 11.2 User Endpoints

```
GET /users/me
  Auth: Bearer token
  Response 200: UserPublic

GET /users
  Auth: Admin
  Response 200: List[UserPublic]

GET /users/pending
  Auth: Admin
  Response 200: List[UserPublic]

PATCH /users/{user_id}/approve
  Auth: Admin
  Response 200: UserPublic
  Response 404: { detail: "User not found" }

PATCH /users/{user_id}/suspend
  Auth: Admin
  Response 200: UserPublic

PATCH /users/{user_id}/role
  Auth: Admin
  Request: { role: "admin" | "user" }
  Response 200: UserPublic

DELETE /users/{user_id}
  Auth: Admin
  Response 200: { message: "User deleted" }
  Response 400: { detail: "Cannot delete the only admin user" }
```

### 11.3 Visualization Endpoints

```
GET /visualizations
  Auth: Bearer
  Response 200: List[VisualizationPublic]

GET /visualizations/recent
  Auth: Bearer
  Response 200: VisualizationPublic | null

POST /visualizations
  Auth: Bearer
  Request: { title: string, description?: string }
  Response 201: VisualizationPublic

GET /visualizations/{viz_id}
  Auth: Bearer
  Response 200: VisualizationPublic
  Response 403: { detail: "Access denied" }
  Response 404: { detail: "Visualization not found" }

GET /visualizations/{viz_id}/chat
  Auth: Bearer
  Response 200: ChatSessionInDB

POST /visualizations/{viz_id}/publish
  Auth: Bearer (owner only)
  Response 200: VisualizationPublic
  Response 400: { detail: "No draft content to publish" }
  Response 403: { detail: "Only the owner can publish" }

GET /visualizations/{viz_id}/versions/{version_number}
  Auth: Bearer (owner only)
  Response 200: { version_number: int, html_content: string, published_at: datetime }
  Response 404: { detail: "Version not found" }
```

### 11.4 WebSocket Endpoint

```
WS /chat/ws/{viz_id}?token={jwt}

ON CONNECT: 
  Server sends: { type: "init", session: ChatSessionInDB }
  Server sends: { type: "error", message: "..." } then closes if auth fails

CLIENT -> SERVER:
  { content: string }

SERVER -> CLIENT (streaming):
  { type: "chunk", content: string }           # LLM token chunk
  { type: "complete" }                          # Stream ended, clarifying
  { type: "visualization_ready", html: string, viz_id: string }  # HTML generated
  { type: "error", message: string }            # Any error during processing
```

---

## 12. Environment Configuration

### `backend/.env`

```env
# MongoDB
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=fortuna

# JWT
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=480

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Default Admin Seed
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@fortuna.app
DEFAULT_ADMIN_PASSWORD=<strong-initial-password>

# CORS
FRONTEND_ORIGIN=http://localhost:5173
```

### `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### `.env.example` (root)

Provide a documented example file with all keys and no values, committed to the repository as a reference.

---

## 13. Security Requirements

### 13.1 Password Security
- Passwords hashed with bcrypt (work factor 12)
- Minimum password length: 8 characters
- No plaintext passwords stored or logged at any time

### 13.2 JWT Security
- Secret key minimum 32 bytes (256 bits), randomly generated
- Token expiry: 8 hours
- Token not stored in cookies (localStorage for simplicity; note XSS risk for production hardening)
- Backend validates token signature and expiry on every request

### 13.3 HTML Visualization Sandbox
- Visualizations rendered in `<iframe>` with `sandbox` attribute
- Minimum sandbox permissions: `allow-scripts`
- Do NOT allow `allow-top-navigation`, `allow-forms`, `allow-popups` unless necessary
- Backend utility `html_sanitizer.py` performs basic checks:
  - Reject responses containing `<script>` tags that reference external domains not on allowlist
  - Reject responses containing `javascript:` protocol URIs in href/src attributes pointing to data exfiltration patterns
  - Log any suspicious patterns for admin review

### 13.4 API Security
- All state-changing operations verify ownership in the service layer
- Admin-only routes protected by `require_admin` dependency
- Input validation via Pydantic on all request bodies
- MongoDB queries use parameterized ObjectId lookups (Motor handles this natively)
- CORS configured to only allow the configured frontend origin

### 13.5 WebSocket Security
- JWT validated before WebSocket connection is accepted
- Connection rejected with code 4003 (forbidden) if token invalid or user not owner
- Rate limiting consideration: Limit to 1 active WebSocket connection per user per visualization

---

## 14. Error Handling

### 14.1 Backend Error Responses

All errors return consistent JSON:
```json
{ "detail": "Human readable error message" }
```

Standard HTTP status codes:
- `400` Bad Request: Invalid input, business rule violation
- `401` Unauthorized: Missing or invalid token
- `403` Forbidden: Valid token but insufficient permissions or pending status
- `404` Not Found: Resource does not exist
- `422` Unprocessable Entity: Pydantic validation failure
- `500` Internal Server Error: Unexpected errors (log to server, return generic message)

### 14.2 LLM Error Handling

```
- Anthropic API timeout (>60s): Return error message to WebSocket, 
  save partial response to session
- Anthropic API rate limit (429): Retry with exponential backoff (3 attempts)
- Anthropic API error (5xx): Notify user via WebSocket error message, 
  session state preserved for retry
- LLM returns <<<VISUALIZATION_READY>>> with invalid HTML: 
  Treat as clarification, log warning, continue conversation
```

### 14.3 Frontend Error Handling

```
- API errors: Intercepted in axios response interceptor
  - 401: Clear auth, redirect to /login with "Session expired" message
  - 403 (pending): Show pending approval message
  - 403 (other): Show "Access denied" toast
  - 404: Show "Not found" inline message
  - 500: Show "Server error, please try again" toast

- WebSocket disconnection:
  - Show "Connection lost" banner in ChatView
  - Provide manual "Reconnect" button
  - Auto-retry once after 3 seconds

- Empty visualization HTML:
  - Show placeholder state in VisualizationFrame: 
    "No visualization generated yet. Start chatting to create one."
```

---

## 15. Development Setup Guide

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB Atlas account with cluster and database named `fortuna`
- Anthropic API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env with your values
python -c "from app.db.init_db import init_db; import asyncio; asyncio.run(init_db())"
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
cp ../.env.example .env
# Edit .env with your values
npm run dev
```

### Backend `requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
motor==3.4.0
pymongo==4.7.2
pydantic[email]==2.7.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
anthropic>=0.26.0
python-dotenv==1.0.1
pytest==8.2.0
pytest-asyncio==0.23.7
httpx==0.27.0
```

### Frontend `package.json` (key dependencies)

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.0",
    "axios": "^1.7.0",
    "primevue": "^3.52.0",
    "@primevue/themes": "^4.0.0"
  },
  "devDependencies": {
    "vite": "^5.2.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## 16. Key Implementation Notes

1. **Default Admin Safety**: The init_db check prevents creating a duplicate admin only when zero admins exist. This is idempotent on every server start.

2. **Visualization Ownership Immutability**: `owner_id` is set at creation and never updated. All ownership checks compare `visualization.owner_id == current_user.id` in the service layer, not the router.

3. **Chat Session Continuity**: When a user clicks "Continue Recent" from dashboard, the app fetches the most recent visualization and navigates to `/chat/:vizId`. The existing chat session is loaded and appended to. The LLM receives the full message history providing full context continuity.

4. **HTML Storage**: The full HTML string is stored directly in MongoDB. For typical visualizations this will be 10KB-200KB, well within MongoDB's 16MB document limit. If very large visualizations become a concern, consider GridFS for the HTML field.

5. **WebSocket Token Auth**: Since browser WebSocket API does not support custom headers, the JWT is passed as a URL query parameter. The backend validates this immediately on connection and closes the socket if invalid, minimizing exposure.

6. **Admin Cannot Be Locked Out**: The DELETE /users/:id endpoint should check that at least one active admin will remain after deletion. If the target is the last admin, return 400.

7. **LLM Context Window Management**: By replacing full HTML content with a summary placeholder in the message history, token usage is kept manageable across long editing sessions.