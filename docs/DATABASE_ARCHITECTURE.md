# SmartLegal AI — Database Architecture & Schema Specification

## 1. Overview & Data Tier

SmartLegal AI utilizes **PostgreSQL** hosted on **Supabase** as its relational datastore. The application interacts with PostgreSQL using `asyncpg` connection pooling in Python.

### Connection & Caching Topology
- **Connection Pool**: `asyncpg.create_pool` with `min_size=2`, `max_size=10`, and `command_timeout=60s`.
- **L1 Cache (Redis)**: Async Redis client (`cache.py`) with 24-hour default TTL (`REDIS_CACHE_TTL`), storing serialized JSON analysis results for document IDs. Falls back gracefully to PostgreSQL on cache miss or connection unavailability.
- **L2 Datastore (PostgreSQL)**: Persistent relational store holding user credentials, document metadata, JSON analysis payloads, Q&A chat histories, and civic hub application checklists.

---

## 2. Entity-Relationship Diagram

```
+--------------------+
|       users        |
+--------------------+
| id (PK)            |
| name               |
| email (UNIQUE)     |
| password           |
| created_at         |
+---------+----------+
          |
          +----------------------+----------------------+----------------------+
          | 1:N                  | 1:N                  | 1:N                  | 1:N
+---------v----------+ +---------v----------+ +---------v----------+ +---------v----------+
|     documents      | |  id_applications   | |prop_applications   | |biz_applications    |
+--------------------+ +--------------------+ +--------------------+ +--------------------+
| id (PK)            | | id (PK)            | | id (PK)            | | id (PK)            |
| user_id (FK)       | | user_id (FK)       | | user_id (FK)       | | user_id (FK)       |
| filename           | | id_type            | | property_type      | | business_type      |
| file_url           | | service            | | service            | | service            |
| file_size          | | status             | | status             | | status             |
| document_type      | | notes              | | notes              | | notes              |
| status             | | created_at         | | created_at         | | created_at         |
| uploaded_at        | | updated_at         | | updated_at         | | updated_at         |
+---------+----------+ +---------+----------+ +---------+----------+ +---------+----------+
          |                      |                      |                      |
          | 1:1                  | 1:N                  | 1:N                  | 1:N
+---------v----------+ +---------v----------+ +---------v----------+ +---------v----------+
|      analyses      | |id_checklist_items  | |prop_checklist_items| |biz_checklist_items |
+--------------------+ +--------------------+ +--------------------+ +--------------------+
| id (PK)            | | id (PK)            | | id (PK)            | | id (PK)            |
| document_id (FK)   | | application_id (FK)| | application_id (FK)| | application_id (FK)|
| result_json        | | item_text          | | item_text          | | item_text          |
| analyzed_at        | | is_done            | | is_done            | | is_done            |
+--------------------+ | updated_at         | | updated_at         | | updated_at         |
                       +--------------------+ +--------------------+ +--------------------+
```

---

## 3. Table Schema Definitions

### 1. `users`
Stores user identity profiles.
- `id` (`TEXT PRIMARY KEY`): Unique UUID string.
- `name` (`TEXT NOT NULL`): User's full display name.
- `email` (`TEXT UNIQUE NOT NULL`): Lowercase verified email address.
- `password` (`TEXT NOT NULL`): bcrypt password hash (or empty string for Google OAuth users).
- `created_at` (`TEXT NOT NULL`): ISO 8601 creation timestamp.

### 2. `documents`
Tracks metadata and storage URIs for uploaded legal files.
- `id` (`TEXT PRIMARY KEY`): Unique document UUID.
- `user_id` (`TEXT NOT NULL FK`): References `users(id)`.
- `filename` (`TEXT NOT NULL`): Original uploaded filename.
- `file_url` (`TEXT NOT NULL`): Storage location (`local://<path>` or Cloudinary secure URL).
- `file_size` (`INTEGER NOT NULL`): File size in bytes.
- `document_type` (`TEXT DEFAULT ''`): Detected legal contract category (e.g. "Rental Agreement").
- `status` (`TEXT DEFAULT 'ready'`): Upload state (`ready`, `processing`, `error`).
- `uploaded_at` (`TEXT NOT NULL`): ISO 8601 upload timestamp.

### 3. `analyses`
Stores raw AI analysis JSON results.
- `id` (`TEXT PRIMARY KEY`): Unique analysis ID.
- `document_id` (`TEXT UNIQUE NOT NULL FK`): References `documents(id)`.
- `result_json` (`TEXT NOT NULL`): Complete serialized JSON containing summary metrics, parties, key dates, and clause risk breakdowns.
- `analyzed_at` (`TEXT NOT NULL`): ISO 8601 analysis completion timestamp.

### 4. `chat_messages`
Stores Q&A conversation history grounded in document context.
- `id` (`TEXT PRIMARY KEY`): Unique message ID.
- `document_id` (`TEXT NOT NULL FK`): References `documents(id)`.
- `user_id` (`TEXT NOT NULL FK`): References `users(id)`.
- `role` (`TEXT NOT NULL`): `"user"` or `"assistant"`.
- `content` (`TEXT NOT NULL`): Text body of message.
- `timestamp` (`TEXT NOT NULL`): ISO 8601 timestamp.

### 5. Application & Checklist Tables (`id_applications`, `property_applications`, `business_applications`)
Store user application progress and corresponding checklist items across Indian Civic Service Hubs.
- `id` (`TEXT PRIMARY KEY`): Unique application or checklist item ID.
- `user_id` (`TEXT NOT NULL FK`): References `users(id)`.
- `status` (`TEXT DEFAULT 'in_progress'`): Status indicator (`in_progress`, `submitted`, `completed`).
- `is_done` (`INTEGER DEFAULT 0`): Boolean flag (0 or 1) indicating checklist task completion.
