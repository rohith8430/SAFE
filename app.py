from __future__ import annotations
import os, secrets, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('DATA_DIR', ROOT))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / 'safespot.db'
UPLOADS = Path(os.environ.get('UPLOAD_FOLDER', ROOT / 'static' / 'uploads'))
UPLOADS.mkdir(parents=True, exist_ok=True)
CATEGORIES = ('Broken streetlight', 'Damaged road', 'Pothole', 'Garbage accumulation', 'Blocked pathway', 'Unsafe crossing', 'Flooding / drainage', 'Other hazard')
STATUSES = ('Pending', 'In Progress', 'Resolved')
app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-before-deploy'), ADMIN_TOKEN=os.environ.get('ADMIN_SESSION_TOKEN') or secrets.token_urlsafe(32), MAX_CONTENT_LENGTH=5*1024*1024)

def db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH); g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    conn = g.pop('db', None)
    if conn: conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, public_id TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL, description TEXT NOT NULL, location TEXT NOT NULL,
        latitude REAL NOT NULL, longitude REAL NOT NULL, photo TEXT,
        status TEXT NOT NULL DEFAULT 'Pending', admin_note TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL);''')
    conn.close()

@app.before_request
def admin_state():
    g.is_admin = request.cookies.get('safespot_admin') == app.config['ADMIN_TOKEN']

@app.get('/')
def index():
    stats = db().execute("SELECT COUNT(*) total, SUM(status='Pending') pending, SUM(status='In Progress') active, SUM(status='Resolved') resolved FROM reports").fetchone()
    return render_template('index.html', stats=stats, categories=CATEGORIES, statuses=STATUSES)

@app.get('/api/reports')
def reports_feed():
    sql = 'SELECT public_id,category,description,location,latitude,longitude,photo,status,admin_note,created_at FROM reports WHERE 1=1'; args=[]
    category, status, q = (request.args.get(k,'').strip() for k in ('category','status','q'))
    if category in CATEGORIES: sql += ' AND category=?'; args.append(category)
    if status in STATUSES: sql += ' AND status=?'; args.append(status)
    if q: sql += ' AND (location LIKE ? OR description LIKE ? OR public_id LIKE ?)'; args.extend([f'%{q}%']*3)
    return jsonify([dict(r) for r in db().execute(sql+' ORDER BY created_at DESC',args).fetchall()])

@app.post('/reports')
def create_report():
    category=request.form.get('category','').strip(); description=request.form.get('description','').strip(); location=request.form.get('location','').strip()
    try: lat=float(request.form.get('latitude','')); lon=float(request.form.get('longitude',''))
    except (TypeError,ValueError): lat=lon=999
    if category not in CATEGORIES or not description or len(description)>1200 or not location or len(location)>180 or not (-90<=lat<=90 and -180<=lon<=180):
        flash('Please complete the required fields and choose a valid map location.','error'); return redirect(url_for('index')+'#report')
    photo_path=None; photo=request.files.get('photo')
    if photo and photo.filename:
        suffix=Path(secure_filename(photo.filename)).suffix.lower()
        if suffix not in ('.png','.jpg','.jpeg','.webp'):
            flash('Photo must be a PNG, JPG, JPEG, or WEBP image.','error'); return redirect(url_for('index')+'#report')
        filename=secrets.token_hex(12)+suffix; photo.save(UPLOADS/filename); photo_path=filename
    now=datetime.now(timezone.utc).isoformat(timespec='seconds'); public_id='SS-'+secrets.token_hex(3).upper(); conn=db()
    while conn.execute('SELECT 1 FROM reports WHERE public_id=?',(public_id,)).fetchone(): public_id='SS-'+secrets.token_hex(3).upper()
    conn.execute('INSERT INTO reports (public_id,category,description,location,latitude,longitude,photo,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)',(public_id,category,description,location,lat,lon,photo_path,now,now)); conn.commit()
    flash(f'Report submitted. Your tracking ID is {public_id}.','success'); return redirect(url_for('index')+'#reports')

@app.post('/admin/login')
def admin_login():
    password=os.environ.get('ADMIN_PASSWORD')
    if not password: flash('Admin access is not configured. Set ADMIN_PASSWORD before starting the app.','error'); return redirect(url_for('index')+'#admin')
    if secrets.compare_digest(request.form.get('password',''),password):
        response=redirect(url_for('admin')); response.set_cookie('safespot_admin',app.config['ADMIN_TOKEN'],httponly=True,samesite='Lax',secure=request.is_secure,max_age=28800); return response
    flash('That password was not accepted.','error'); return redirect(url_for('index')+'#admin')

@app.post('/admin/logout')
def admin_logout():
    response=redirect(url_for('index')); response.delete_cookie('safespot_admin'); return response

@app.get('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOADS, filename)

@app.get('/admin')
def admin():
    if not g.is_admin: abort(403)
    rows=db().execute('SELECT * FROM reports ORDER BY created_at DESC').fetchall()
    return render_template('admin.html',reports=rows,statuses=STATUSES)

@app.post('/admin/reports/<public_id>')
def update_report(public_id):
    if not g.is_admin: abort(403)
    status=request.form.get('status',''); note=request.form.get('admin_note','').strip()[:500]
    if status not in STATUSES: abort(400)
    conn=db(); conn.execute('UPDATE reports SET status=?,admin_note=?,updated_at=? WHERE public_id=?',(status,note,datetime.now(timezone.utc).isoformat(timespec='seconds'),public_id)); conn.commit()
    flash(f'Updated {public_id}.','success'); return redirect(url_for('admin'))

init_db()
if __name__ == '__main__': app.run(debug=os.environ.get('FLASK_DEBUG')=='1',port=int(os.environ.get('PORT','5000')))

