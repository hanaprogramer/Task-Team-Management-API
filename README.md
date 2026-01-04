# ✅ Task & Team Management API

A **Trello/Jira-like backend API** built with **Django REST Framework**, featuring **JWT authentication**, **role-based permissions**, **tests**, **Swagger documentation**, **pagination**, **filtering**, and **file attachments**.

---

## 🚀 Features

✅ **JWT Authentication (Login/Register/Logout)**  
✅ **Role-based Access Control (Admin / Team Owner / Member)**  
✅ **Teams Management (Owner + Members)**  
✅ **Projects inside Teams**  
✅ **Tasks inside Projects**
  - status (todo / doing / done)
  - priority (high / medium / low)
  - due date validation   
✅ **Comments on Tasks** (nested route)  
✅ **Filtering & Pagination** (for tasks)  
✅ **File Attachment Upload for Tasks** (similar to Jira/Trello attachments)  
✅ **Swagger API Documentation**  
✅ **Full Test Coverage for Serializers & ViewSets**  
✅ Clean Git workflow (**feature branches + PRs + commits**)
---

## 🧠 Roles & Permissions

### 👑 Admin
- Can view all users (and optionally manage system resources)

### 👤 Team Owner
- Can create teams  
- Can update/delete their teams  
- Can manage projects/tasks under their teams  

### 👥 Member
- Can view projects/tasks where they are a member  
- Can update task execution fields (like status) if assigned  

🔐 Permissions are enforced through a combination of:
- ViewSet access rules
- Serializer validation

---

## 🏗️ Tech Stack

- **Python**
- **Django**
- **Django REST Framework**
- **JWT Authentication** (`SimpleJWT`)
- **Swagger / OpenAPI** (`drf-spectacular`)
- Testing with **APITestCase**
- SQLite (default, easily replaceable with PostgreSQL)

---

## 📌 API Endpoints

### 🔑 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/registration/` | Register new user |
| POST | `/api/users/login/` | Login and get access/refresh tokens |
| POST | `/api/users/logout/` | Logout (blacklist refresh token) |

---

### 👥 Teams
| Method | Endpoint |
|--------|----------|
| GET | `/api/teams/` | List teams |
| POST | `/api/teams/` | Create team |
| PATCH | `/api/teams/<id>/` | Update team |
| DELETE | `/api/teams/<id>/` | Delete team |

---

### 📁 Projects
| Method | Endpoint |
|--------|----------|
| GET | `/api/projects/` | List projects |
| POST | `/api/projects/` | Create project |
| PATCH | `/api/projects/<id>/` | Update project |
| DELETE | `/api/projects/<id>/` | Delete project |

---

### ✅ Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks/` | List tasks |
| POST | `/api/tasks/` | Create task |
| PATCH | `/api/tasks/<id>/` | Update task |
| DELETE | `/api/tasks/<id>/` | Delete task |

✅ Filtering:
- `/api/tasks/?status=done`
- `/api/tasks/?assigned_to=me`

✅ Pagination:
- `/api/tasks/?page=2`

✅ Attachment upload:
- multipart upload supported on create/update

---

### 💬 Comments (Nested)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks/<task_id>/comments/` | List comments |
| POST | `/api/tasks/<task_id>/comments/` | Create comment |
| PATCH | `/api/tasks/<task_id>/comments/<id>/` | Update comment |
| DELETE | `/api/tasks/<task_id>/comments/<id>/` | Delete comment |

---

## 📖 Swagger / API Documentation

✅ Swagger UI:
- `/api/docs/`

✅ OpenAPI Schema JSON:
- `/api/schema/`

---

## ⚙️ Setup & Installation

### 1) Clone the repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```
### 2) Create virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```
### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Apply migrations
```bash
python manage.py migrate
```

### 5) Run the server
```bash
python manage.py runserver
Run tests for a specific app:
```
## ✅ Running Tests
```bash
python manage.py test apps.tasks.tests
python manage.py test apps.projects.tests
python manage.py test apps.teams.tests
python manage.py test apps.users.tests
```
Run a single test file:

```bash
python manage.py test apps.tasks.tests.test_task_viewset
```
## 📎 File Upload (Task Attachments)

Tasks support optional file uploads via `attachment`.
✅ Upload example:

- Create or update a task using `multipart/form-data`
Uploaded files stored in:

```bash
media/task_attachments/
```

📌 `media/` is ignored in git to keep the repository clean.
## 📌 Project Structure

```bash
apps/
 ├── users/
 ├── teams/
 ├── projects/
 ├── tasks/
 └── comments/
```

## ⭐ Why This Project Matters (Portfolio Value)

This project demonstrates real-world backend skills including:
- API design
- Authentication & security
- Permissions & access control
- Validation logic
- Nested resources
- Testing
- Documentation (Swagger)
- Scalability-ready structure

## 👤 Author

**Hosna (hanaprogramer)**  
Backend Developer | Django REST Framework




