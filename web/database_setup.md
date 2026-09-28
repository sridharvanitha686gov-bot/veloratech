# Velora Tech Solutions — Database & Backend Setup

The Velora Tech Solutions application features a hybrid backend supporting both local development (**SQLite**) and production-ready cloud storage (**MongoDB Atlas**). This is managed dynamically via environment configurations.

---

## 🏗️ Database Modes

The server determines its storage engine on startup:
1. **MongoDB Atlas Mode (Cloud)**: Triggered if `MONGO_URI` is provided in the `.env` file. Logs all submissions directly to your MongoDB Atlas cluster.
2. **SQLite Fallback (Local)**: Runs if `MONGO_URI` is empty or if the MongoDB client fails to connect on startup. Automatically creates and writes submissions locally to `velora_leads.db` in the workspace root.

---

## 🚀 Getting Started

### 1. Install Dependencies
Ensure you have Python installed. Install the backend dependencies:
```bash
pip install flask pymongo dnspython
```

### 2. Configure Environment (`.env`)
Create or edit the `.env` file in the root directory:
```env
# Dashboard Admin Authentication password
ADMIN_PASSWORD=veloratech2026

# MongoDB Atlas URI (leave blank to use local SQLite)
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
```

---

## 🔒 Admin Dashboard

Access the secure dashboard at:  
👉 **`http://127.0.0.1:5000/admin`** (or `admin.html` locally)

To prevent public users from finding this page, there is no visible text link on the website. Instead, you can trigger navigation to the admin panel using one of these two hidden methods on any page:
1. **Secret Keyboard Shortcut**: Press **`Ctrl + Shift + A`** on your keyboard.
2. **Hidden Click Sequence**: Click the copyright text (e.g. `© 2025-2026 Velora Tech Solutions. All rights reserved.`) at the bottom of any footer **5 times quickly**.

* **Default Dashboard Password:** `veloratech2026`
* Manage, filter, search, view full syllabi selections, download details as CSV, or remove rows instantly.

---

## 📊 Fields Description

| SQLite Field | MongoDB Document Field | Type | Description |
|---|---|---|---|
| `id` | `_id` | `ObjectId` (string representation) | Unique Primary Key |
| `timestamp` | `timestamp` | `string` (ISO UTC format) | Submission time |
| `first_name` | `first_name` | `string` | User's first name |
| `last_name` | `last_name` | `string` | User's last name |
| `email` | `email` | `string` | User's email address |
| `company` | `company` | `string` | Company / School name |
| `service` | `service` | `string` | Selected service/option tag |
| `budget` | `budget` | `string` | Project budget / Internship course selection |
| `message` | `message` | `string` | Cover letter / message body |
