import os
import sqlite3
import html
import hmac
import time
import datetime
import re
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory

# Try importing pymongo and bson
try:
    from pymongo import MongoClient
    from bson import ObjectId
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

app = Flask(__name__, static_folder=None)

# Load environment variables manually from .env if present
def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    v = v.strip().strip("'").strip('"')
                    os.environ[k.strip()] = v

load_env()

# Configuration
DATABASE = 'velora_leads.db'
DEFAULT_ADMIN_PASSWORD = 'veloratech2026'
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', DEFAULT_ADMIN_PASSWORD).strip()
MONGO_URI = os.environ.get('MONGO_URI', '').strip()
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
FIELD_LIMITS = {
    'firstName': 80,
    'lastName': 80,
    'email': 254,
    'company': 160,
    'service': 40,
    'budget': 80,
    'message': 2000,
}
PUBLIC_FILES = {
    'about.html',
    'admin.html',
    'contact.html',
    'index.html',
    'internship.html',
    'portfolio.html',
    'services.html',
    'style.css',
    'main.js',
    'robots.txt',
    'sitemap.xml',
    'about_team.png',
    'hero_bg.png',
    'logo.png',
    'portfolio_bg.png',
    'product_ai.png',
    'product_mobile.png',
    'product_saas.png',
}
PUBLIC_CACHE_EXTENSIONS = ('.css', '.js', '.png')

USE_MONGO = bool(HAS_PYMONGO and MONGO_URI)
mongo_client = None

if USE_MONGO:
    try:
        # Connect to MongoDB client (5-second timeout for quick fallback check)
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')
    except Exception as e:
        print(f"Warning: MongoDB connection test failed: {e}")
        print("Falling back to local SQLite database mode.")
        USE_MONGO = False

# Rate Limiter
class SimpleRateLimiter:
    def __init__(self, limit=10, period=60):
        self.limit = limit
        self.period = period
        self.requests = defaultdict(list)
        self.last_cleanup = 0

    def is_allowed(self, ip):
        now = time.time()
        if now - self.last_cleanup > self.period:
            self.requests = defaultdict(
                list,
                {
                    key: [t for t in hits if now - t < self.period]
                    for key, hits in self.requests.items()
                    if any(now - t < self.period for t in hits)
                }
            )
            self.last_cleanup = now
        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.period]
        if len(self.requests[ip]) >= self.limit:
            return False
        self.requests[ip].append(now)
        return True

submit_limiter = SimpleRateLimiter(limit=5, period=60)      # 5 submissions per minute per IP
login_limiter = SimpleRateLimiter(limit=10, period=60)     # 10 login attempts per minute per IP

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

# SQLite Fallback helpers
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not USE_MONGO:
        with get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    company TEXT,
                    service TEXT,
                    budget TEXT,
                    message TEXT NOT NULL
                )
            ''')
            conn.commit()

# Ensure local DB is initialized if fallback is active
init_db()

# Input sanitation helper
def sanitize(val, max_length=500):
    if not val:
        return ''
    return html.escape(val.strip()[:max_length])

def is_public_file(path):
    normalized = path.replace('\\', '/').lstrip('/')
    return '/' not in normalized and normalized in PUBLIC_FILES

# Security Headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if request.path.endswith(PUBLIC_CACHE_EXTENSIONS):
        response.headers['Cache-Control'] = 'public, max-age=86400'
    return response

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin_page():
    return send_from_directory('.', 'admin.html')

@app.route('/api/submit', methods=['POST'])
def submit_form():
    ip = get_client_ip()
    if not submit_limiter.is_allowed(ip):
        return jsonify({'result': 'error', 'message': 'Too many submissions. Please try again later.'}), 429

    try:
        first_name = sanitize(request.form.get('firstName', ''), FIELD_LIMITS['firstName'])
        last_name = sanitize(request.form.get('lastName', ''), FIELD_LIMITS['lastName'])
        email = sanitize(request.form.get('email', ''), FIELD_LIMITS['email'])
        company = sanitize(request.form.get('company', ''), FIELD_LIMITS['company'])
        service = sanitize(request.form.get('service', ''), FIELD_LIMITS['service'])
        budget = sanitize(request.form.get('budget', ''), FIELD_LIMITS['budget'])
        message = sanitize(request.form.get('message', ''), FIELD_LIMITS['message'])

        if not first_name or not last_name or not email or not message:
            return jsonify({'result': 'error', 'message': 'Missing required fields'}), 400
        if not EMAIL_RE.match(email):
            return jsonify({'result': 'error', 'message': 'Please enter a valid email address'}), 400

        if USE_MONGO:
            db = mongo_client['velora_db']
            doc = {
                'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'company': company,
                'service': service,
                'budget': budget,
                'message': message
            }
            db.submissions.insert_one(doc)
        else:
            with get_db() as conn:
                conn.execute('''
                    INSERT INTO submissions (first_name, last_name, email, company, service, budget, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (first_name, last_name, email, company, service, budget, message))
                conn.commit()

        return jsonify({'result': 'success', 'message': 'Submission saved successfully!'})
    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)}), 500

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    ip = get_client_ip()
    if not login_limiter.is_allowed(ip):
        return jsonify({'result': 'error', 'message': 'Too many attempts. Please try again later.'}), 429

    token = request.headers.get('X-Admin-Token')
    if not token or not hmac.compare_digest(token, ADMIN_PASSWORD):
        return jsonify({'result': 'error', 'message': 'Unauthorized'}), 401
        
    try:
        if USE_MONGO:
            db = mongo_client['velora_db']
            cursor = db.submissions.find().sort('timestamp', -1)
            submissions = []
            for doc in cursor:
                submissions.append({
                    'id': str(doc['_id']),
                    'timestamp': doc.get('timestamp'),
                    'first_name': doc.get('first_name'),
                    'last_name': doc.get('last_name'),
                    'email': doc.get('email'),
                    'company': doc.get('company'),
                    'service': doc.get('service'),
                    'budget': doc.get('budget'),
                    'message': doc.get('message')
                })
        else:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM submissions ORDER BY timestamp DESC')
                rows = cursor.fetchall()
                submissions = []
                for row in rows:
                    submissions.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'email': row['email'],
                        'company': row['company'],
                        'service': row['service'],
                        'budget': row['budget'],
                        'message': row['message']
                    })
        return jsonify({'result': 'success', 'submissions': submissions})
    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)}), 500

@app.route('/api/submissions/<sub_id>', methods=['DELETE'])
def delete_submission(sub_id):
    token = request.headers.get('X-Admin-Token')
    if not token or not hmac.compare_digest(token, ADMIN_PASSWORD):
        return jsonify({'result': 'error', 'message': 'Unauthorized'}), 401
        
    try:
        if USE_MONGO:
            db = mongo_client['velora_db']
            db.submissions.delete_one({'_id': ObjectId(sub_id)})
        else:
            with get_db() as conn:
                conn.execute('DELETE FROM submissions WHERE id = ?', (sub_id,))
                conn.commit()
        return jsonify({'result': 'success', 'message': f'Submission {sub_id} deleted successfully.'})
    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    if 'text/html' in request.accept_mimetypes:
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>404 — Page Not Found — Velora Tech Solutions</title>
  <link rel="stylesheet" href="style.css">
  <style>
    body {
      background: #000;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      text-align: center;
      font-family: 'Inter', sans-serif;
    }
    .error-container {
      max-width: 500px;
      padding: 40px;
    }
    h1 {
      font-size: 120px;
      font-weight: 800;
      background: linear-gradient(135deg, #0066cc, #6e40c9);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 20px;
    }
    p {
      color: #86868b;
      margin-bottom: 30px;
      font-size: 16px;
    }
  </style>
</head>
<body>
  <div class="error-container">
    <h1>404</h1>
    <h2>Lost in Space?</h2>
    <p>The page you are looking for doesn't exist or has been moved to a new galaxy.</p>
    <a href="index.html" class="btn-primary">Back to Home</a>
  </div>
</body>
</html>""", 404
    return jsonify({'result': 'error', 'message': 'Not Found'}), 404

@app.route('/<path:path>')
def serve_static(path):
    if '..' in path or path.startswith('/') or not is_public_file(path):
        return "Invalid path", 400
    return send_from_directory('.', path)

if __name__ == '__main__':
    print("--------------------------------------------------")
    print("Velora Tech Solutions Backend running on:")
    print("http://127.0.0.1:5000")
    if USE_MONGO:
        print("Database Mode: MONGODB ACTIVE")
    else:
        print("Database Mode: LOCAL SQLITE FALLBACK")
        print(f"File: {DATABASE}")
    if ADMIN_PASSWORD == DEFAULT_ADMIN_PASSWORD:
        print("Warning: ADMIN_PASSWORD is using the default development value.")
    print("Admin dashboard available at:")
    print("http://127.0.0.1:5000/admin")
    print("--------------------------------------------------")
    app.run(host='127.0.0.1', port=5000, debug=True)
