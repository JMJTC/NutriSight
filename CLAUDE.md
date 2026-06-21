# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

食智眸 (Smart Food Eye) — a fullstack admin management system with food recognition. Built with FastAPI (Python 3.11+) + Vue 3 (Composition API) + Naive UI. Uses YOLOv8 for real-time food detection and nutritional analysis.

## Commands

### Backend (Python/FastAPI)

```bash
# Start dev server (port 9999, auto-reload)
python run.py

# Install dependencies (uses uv)
uv sync

# Lint
ruff check ./app

# Format
black ./
isort ./ --profile black

# Database migration (Tortoise ORM + Aerich)
aerich migrate      # generate migration files
aerich upgrade      # apply migrations

# Reset database
make clean-db       # deletes migrations/ and db.sqlite3
```

### Frontend (Vue 3 / Vite)

```bash
cd web

# Install dependencies (uses pnpm)
pnpm install

# Dev server (port 3100, proxies /api to backend)
pnpm dev

# Production build → web/dist/
pnpm build

# Lint & format
pnpm lint
pnpm prettier
```

### Docker

```bash
docker build -t smart-food-eye .
docker run -d -p 9999:9999 -p 3100:3100 smart-food-eye
```

### Test Scripts (one-off verification)

```bash
python test_recognition.py    # food recognition test
python test_food_api.py       # API interface test
python test_flow.py           # full flow verification
```

## Architecture

### Backend (FastAPI + Tortoise ORM)

```
app/
├── api/v1/         # HTTP route handlers — wiring only, thin
│   ├── base/       # Login, userinfo, profile (no permission check)
│   ├── users/      # CRUD for users (DependPermission)
│   ├── roles/      # CRUD for roles
│   ├── menus/      # CRUD for menus
│   ├── apis/       # API permission management
│   ├── depts/      # Department tree management
│   ├── auditlog/   # Audit log queries
│   └── food/       # Food recognition endpoints
├── controllers/    # Business logic layer (CRUDBase subclasses per model)
├── models/         # Tortoise ORM models (admin.py: User/Role/Menu/Api/Dept/AuditLog, food.py: FoodCategory/Nutrition/RecognitionRecord)
├── schemas/        # Pydantic request/response schemas
├── services/       # External services — yolo_service.py (singleton model inference), food_recognition_service.py, food_catalog_service.py
├── core/
│   ├── crud.py     # Generic CRUDBase[Model, CreateSchema, UpdateSchema]
│   ├── dependency.py # AuthControl (JWT) + PermissionControl (RBAC, checks role→api access)
│   ├── middlewares.py # HttpAuditLogMiddleware (logs all requests), BackGroundTaskMiddleware
│   ├── init_app.py # App factory: registers routes, exceptions, middleware, inits DB/superuser/menus/YOLO
│   └── exceptions.py # Custom exception handlers
├── settings/config.py # Pydantic BaseSettings — DB config, JWT settings, CORS
└── utils/          # JWT encode/decode, password hashing (argon2)
```

**Key patterns:**
- Each controller extends `CRUDBase[Model, CreateSchema, UpdateSchema]` and is module-level singleton (e.g. `user_controller = UserController()`).
- API routes are thin — they call controllers directly. Standard CRUD endpoints: `/list`, `/get`, `/create`, `/update`, `/delete`.
- Permission is checked via `DependPermission` FastAPI dependency on each router. Superusers bypass all checks. Role-based: user → roles → apis → (method, path) match.
- JWT auth via `AuthControl.is_authed` dependency. A special `token: "dev"` header bypasses JWT verification for local development.
- Database: SQLite by default via Tortoise ORM. Switch to MySQL/PostgreSQL in `app/settings/config.py` `TORTOISE_ORM["connections"]`.
- YOLO service is a thread-safe singleton with separate locks for loading and inference (`YoloService` in `app/services/yolo_service.py`). Model weights in `weights/best.pt`.
- App startup (`lifespan`) runs migrations, initializes YOLO model, creates admin user (`admin`/`123456`), seeds menus/APIs/roles/food data.

### Frontend (Vue 3 + Naive UI + Pinia)

```
web/src/
├── api/index.js         # All API calls in one file (axios-based request wrapper)
├── views/
│   ├── system/          # User/Role/Menu/API/Dept/AuditLog management pages
│   ├── food/            # recognition/, history/, management/ (food recognition feature)
│   ├── workbench/       # Dashboard/home page
│   ├── login/           # Login page
│   └── profile/         # User profile
├── components/
│   ├── common/          # Shared UI components (e.g. CommonTable)
│   ├── food/            # Food-specific: NutritionDashboard, ConfidenceHeatmap, FoodEncyclopedia
│   ├── query-bar/       # Search/filter bar
│   └── table/           # Table wrapper
├── router/
│   ├── routes/          # Route definitions (basic + dynamic from backend menus)
│   └── guard/           # Navigation guards (auth check)
├── store/modules/
│   ├── user/            # User info, token
│   ├── permission/      # Dynamic menus & API permissions from backend
│   ├── app/             # App-wide settings (theme, sidebar, etc.)
│   └── tags/            # Tab/tag view state
├── layout/              # Layout shell (sidebar, header, content area)
├── utils/http/          # Axios instance with interceptors (token injection, error handling)
├── composables/         # useCRUD.js — generic CRUD composition function
└── styles/              # Global SCSS + UnoCSS
```

**Key patterns:**
- Menu/permissions are dynamic: fetched from `GET /base/usermenu` and `GET /base/userapi` after login, used to build routes and restrict actions.
- `useCRUD.js` composable provides a generic CRUD pattern for list pages (pagination, search, create/edit/delete).
- API layer: all requests in `web/src/api/index.js`, using the axios wrapper at `web/src/utils/http/`. Token automatically attached via interceptor; `{ noNeedToken: true }` option for login/register.
- UnoCSS for utility styling, Naive UI for component library.
- Environment config: `web/.env.development` / `web/.env.production`. Proxy config in `web/build/constant.js` routes `/api` to `http://localhost:9999`.

## Key Files to Know

- `app/__init__.py` — FastAPI app creation, lifespan, static mounts
- `app/settings/config.py` — All backend configuration (DB, JWT, CORS)
- `app/core/init_app.py` — Database initialization, seed data, YOLO model loading on startup
- `app/core/dependency.py` — JWT authentication + RBAC permission checking
- `app/api/v1/food/food.py` — All food recognition API endpoints (~15K, largest route file)
- `web/src/router/index.js` — Dynamic route generation from backend menus
- `web/src/store/modules/permission/index.js` — Permission/menu generation logic
- `web/src/utils/http/` — Axios wrapper with token injection

## Git Commits

- Message format: `<prefix>: <brief description>` — concise, key information only.
- Prefixes: `feat`, `fix`, `doc`, `refactor`, `test`, `chore`.
- No `Co-Authored-By` trailers or other footers.