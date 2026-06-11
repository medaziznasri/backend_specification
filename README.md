# PFE Specification Manager - Unified API

A comprehensive FastAPI-based specification management system designed for managing project specifications, handling client sessions, and generating professional PDF documents. This system combines robust authentication, role-based access control (RBAC), and dynamic form management.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Architecture](#project-architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Core Modules](#core-modules)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Authentication & Authorization](#authentication--authorization)

## 🎯 Overview


The **PFE Specification Manager** is an enterprise-grade API for managing technical specifications and project requirements. It enables:

- **Admins** to create and manage project types, categories, and questions
- **Clients** to create sessions, answer dynamic forms, and generate specification documents
- **Secure access** through JWT-based authentication and role-based permissions
- **Automated PDF generation** from collected client responses

The system is built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**, providing high performance and scalability.

## ✨ Features

### Authentication & Security
- ✅ JWT-based token authentication
- ✅ Bcrypt password hashing
- ✅ Role-based access control (RBAC)
- ✅ Permission-based endpoint protection
- ✅ CORS support for cross-origin requests

### Admin Capabilities
- 📝 Manage project types and their properties
- 📂 Create and organize specification categories
- ❓ Define dynamic questions with multiple answer types
- 🔐 Control access through role-based permissions
- 📊 Monitor all system activities

### Client Features
- 🎯 Browse available project types and categories
- 📋 Create specification sessions with selected categories
- ✍️ Submit answers to dynamic questions
- 📄 Generate professional PDF specification documents
- 💾 Access generated documents via HTTP

### System Features
- 🗄️ PostgreSQL database with UUID-based records
- 📁 Static file serving for generated PDFs
- 🏥 Health check endpoint for system monitoring
- 🔄 Automatic database table creation on startup
- 📖 Auto-generated Swagger/OpenAPI documentation

## 🏗️ Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Auth API   │  │  Admin API   │  │  Client API  │     │
│  │   /auth      │  │ /api/admin   │  │/api/client   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                 │
│                    ┌───────┴────────┐                       │
│                    │     RBAC       │                       │
│                    │  Permissions   │                       │
│                    └────────────────┘                       │
│                            │                                 │
│            ┌───────────────┼───────────────┐               │
│            │               │               │               │
│      ┌──────────────┐ ┌─────────────┐ ┌──────────────┐    │
│      │   Database   │ │     PDF     │ │   Storage    │    │
│      │ PostgreSQL   │ │ Generation  │ │   (Files)    │    │
│      └──────────────┘ └─────────────┘ └──────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Prerequisites

- **Python** 3.10+
- **PostgreSQL** 12+
- **pip** (Python package manager)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd adminpy
```

### 2. Create a Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic jose passlib[bcrypt] fpdf2 python-multipart python-jose[cryptography]
```

Or using a requirements file (if available):
```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection
Update `database.py` with your PostgreSQL connection string:

```python
DATABASE_URL = "postgresql://username:password@localhost/specifications_manager"
```

### 5. Run the Application
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Frontend (UI):** Open `http://127.0.0.1:8000/` in a browser. The app serves the frontend from the `frontend/` folder.
- **API docs:** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health`

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:password@localhost/specifications_manager
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=2
STORAGE_PATH=storage/specifications
```

### Database Configuration
- **Host**: `localhost`
- **Port**: `5432` (default)
- **Database**: `specifications_manager`
- **User**: `postgres`
- **Password**: Configure as needed

## 📖 API Documentation

### Interactive Documentation
Once the server is running, access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Check
```http
GET /
```
**Response**:
```json
{
  "status": "Online",
  "systems": {
    "auth": "Active",
    "admin": "Active",
    "client": "Active",
    "storage": "Ready"
  },
  "docs": "/docs"
}
```

## 📁 Project Structure

```
adminpy/
├── main.py                      # FastAPI application entry point
├── database.py                  # SQLAlchemy database configuration
├── models.py                    # SQLAlchemy ORM models
├── schemas.py                   # Pydantic schemas for client API
├── schemas_admin.py             # Pydantic schemas for admin API
├── router_admin.py              # Admin API endpoints
├── client.py                    # Client API endpoints
├── pdf_generator.py             # PDF generation logic
├── check_db.py                  # Database utility scripts
├── seed.py                      # Database seeding script
│
├── auth/
│   ├── __init__.py
│   ├── auth.py                  # Authentication routes
│   ├── auth_routes.py           # Additional auth endpoints
│   └── __pycache__/
│
├── rbac/
│   ├── __init__.py
│   ├── rbac.py                  # RBAC logic
│   ├── dependencies.py          # Permission & authentication dependencies
│   └── __pycache__/
│
├── pdf/
│   └── pdf_generator.py         # PDF generation utilities
│
├── storage/
│   └── specifications/          # Generated PDF storage directory
│
└── __pycache__/
```

## 🔧 Core Modules

### `main.py` - Application Entry Point
Initializes the FastAPI application with:
- CORS middleware configuration
- Database table creation
- Router registration (Auth, Admin, Client)
- Static file mounting for PDFs
- Health check endpoint

### `database.py` - Database Configuration
- PostgreSQL connection setup using SQLAlchemy
- Session factory creation
- Database dependency injection

### `models.py` - Data Models
Defines 8 core SQLAlchemy models:

| Model | Purpose |
|-------|---------|
| `ProjectType` | Project categories/types |
| `Category` | Specification categories |
| `Question` | Form questions (TEXT, MULTI_CHOICE) |
| `ClientSpecificationSession` | User sessions |
| `SessionCategory` | Session-Category mapping |
| `ClientAnswer` | User answers to questions |
| `GeneratedSpecificationDocument` | PDF document records |
| `AdminUser` / `Role` | User authentication & RBAC |

### `schemas.py` - Pydantic Schemas
Request/response data validation for client API:
- `ProjectTypeResponse`
- `CategoryResponse`
- `QuestionForClient`
- `SessionCreate` / `SessionResponse`
- `AnswerItem` / `AnswersSubmit`

### `schemas_admin.py` - Admin Schemas
Request/response validation for admin operations:
- Category CRUD operations
- Question management
- Permission management

### `router_admin.py` - Admin Routes
Protected endpoints for administrators:
- `POST /api/admin/categories` - Create category
- `PATCH /api/admin/categories/{id}` - Update category
- `POST /api/admin/questions` - Create question
- `PATCH /api/admin/questions/{id}` - Update question
- All endpoints require RBAC permissions

### `client.py` - Client Routes
Public/protected endpoints for clients:
- `GET /api/client/project-types` - List project types
- `GET /api/client/categories` - List categories
- `POST /api/client/sessions` - Create session
- `POST /api/client/answers` - Submit answers
- `POST /api/client/generate` - Generate PDF

### `pdf_generator.py` - PDF Generation
- Converts structured answers into professional PDF format
- Handles multi-line cells for long responses
- Customizable styling and headers
- Automatic file saving

### `auth/auth.py` - Authentication
- JWT token creation and validation
- Login endpoint with OAuth2 password flow
- Password hashing using bcrypt
- Token expiration management

### `rbac/rbac.py` - Role-Based Access Control
- Permission verification against roles
- Admin user authentication from tokens
- Resource-action-based permission checking

## 🗄️ Database Schema

### Core Tables

#### `project_types`
```sql
CREATE TABLE project_types (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP DEFAULT now()
);
```

#### `categories`
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    is_general BOOLEAN DEFAULT false,
    status VARCHAR DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

#### `questions`
```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY,
    label VARCHAR NOT NULL,
    description VARCHAR,
    answer_type VARCHAR DEFAULT 'TEXT',
    options JSONB,
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 1,
    status VARCHAR DEFAULT 'ACTIVE',
    category_id UUID REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT now()
);
```

#### `client_specification_session`
```sql
CREATE TABLE client_specification_session (
    id UUID PRIMARY KEY,
    project_type_id UUID REFERENCES project_types(id),
    selected_category_ids JSONB,
    started_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP
);
```

#### `client_answers`
```sql
CREATE TABLE client_answers (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES client_specification_session(id),
    question_id UUID REFERENCES questions(id),
    value VARCHAR,
    answered_at TIMESTAMP DEFAULT now()
);
```

#### `generated_documents`
```sql
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES client_specification_session(id),
    file_path VARCHAR,
    content_summary VARCHAR,
    created_at TIMESTAMP DEFAULT now()
);
```

#### RBAC Tables
```sql
-- Admin users
CREATE TABLE admin_users (
    id UUID PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL
);

-- Roles
CREATE TABLE admin_roles (
    id INTEGER PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description VARCHAR
);

-- Permissions
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    resource VARCHAR,
    action VARCHAR
);

-- Role-Permission mapping
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES admin_roles(id),
    permission_id INTEGER REFERENCES permissions(id)
);
```

## 🔌 API Endpoints

### Authentication
```http
POST   /auth/login
```

### Admin Management (Requires Authentication & Permission)
```http
POST   /api/admin/categories
PATCH  /api/admin/categories/{id}
DELETE /api/admin/categories/{id}

POST   /api/admin/questions
PATCH  /api/admin/questions/{id}
DELETE /api/admin/questions/{id}

GET    /api/admin/permissions
```

### Client Operations
```http
GET    /api/client/project-types
GET    /api/client/categories
GET    /api/client/categories/{category_id}/questions

POST   /api/client/sessions
GET    /api/client/sessions/{session_id}

POST   /api/client/answers
GET    /api/client/answers/{session_id}

POST   /api/client/generate
GET    /files/{pdf_filename}
```

## 🔐 Authentication & Authorization

### JWT Token Flow
```
1. Client sends credentials → POST /auth/login
2. Server validates credentials and returns JWT token
3. Client includes token in Authorization header: "Bearer <token>"
4. Server validates token for protected endpoints
5. Token expires after configured hours (default: 2)
```

### Token Structure
```json
{
  "sub": "admin@example.com",
  "role_id": "1",
  "exp": 1705123456
}
```

### Permission Levels
Three-part permission model: `[action, resource]`

**Actions**: `create`, `read`, `update`, `delete`
**Resources**: `category`, `question`, `session`, `document`

Example:
- `create:category` - Can create categories
- `update:question` - Can update questions
- `delete:session` - Can delete sessions

## 📝 Usage Examples

### 1. Login as Admin
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=yourpassword"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Create a Category (Admin)
```bash
curl -X POST "http://localhost:8000/api/admin/categories" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d {
    "name": "Functional Requirements",
    "description": "Core system functionality",
    "is_general": false
  }
```

### 3. Get Project Types (Client)
```bash
curl -X GET "http://localhost:8000/api/client/project-types"
```

### 4. Create a Specification Session (Client)
```bash
curl -X POST "http://localhost:8000/api/client/sessions" \
  -H "Content-Type: application/json" \
  -d {
    "project_type_id": "550e8400-e29b-41d4-a716-446655440000",
    "selected_category_ids": [
      "550e8400-e29b-41d4-a716-446655440001",
      "550e8400-e29b-41d4-a716-446655440002"
    ]
  }
```

### 5. Submit Answers (Client)
```bash
curl -X POST "http://localhost:8000/api/client/answers" \
  -H "Content-Type: application/json" \
  -d {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "answers": [
      {
        "question_id": "550e8400-e29b-41d4-a716-446655440003",
        "answer_value": "This is my answer"
      }
    ]
  }
```

### 6. Generate PDF (Client)
```bash
curl -X POST "http://localhost:8000/api/client/generate" \
  -H "Content-Type: application/json" \
  -d {
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
```

## 📄 PDF Generation

The system automatically generates professional specification documents with:

### PDF Features
- 📋 Session ID and generation timestamp
- 🎨 Professional styling with formatted headers
- 📊 Structured Q&A table layout
- 📝 Multi-line text handling for long responses
- 💾 Persistent storage in `storage/specifications/`
- 🌐 HTTP accessible via `/files/` endpoint

```







