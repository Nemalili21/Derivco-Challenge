from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"  # For session tracking
DB_NAME = 'database.db'

# ==============================
# CREATE TABLES
# ==============================
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    ''')

    # Projects table
    c.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        project_name TEXT,
        stage TEXT,
        support_needed TEXT,
        tags TEXT,
        completed INTEGER DEFAULT 0
    )
    ''')

    # Milestones table
    c.execute('''
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        milestone TEXT,
        date_created TEXT
    )
    ''')

    # Comments table
    c.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        username TEXT,
        comment TEXT,
        date_created TEXT
    )
    ''')

    conn.commit()
    conn.close()

create_tables()

# ==============================
# HOME PAGE
# ==============================
@app.route('/')
def home():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM projects")
    projects = c.fetchall()

    projects_with_details = []
    for project in projects:
        project_id = project[0]

        # Milestones
        c.execute("SELECT milestone FROM milestones WHERE project_id=?", (project_id,))
        milestones = [m[0] for m in c.fetchall()]

        # Comments
        c.execute("SELECT username, comment, date_created FROM comments WHERE project_id=? ORDER BY id ASC", (project_id,))
        comments = c.fetchall()

        projects_with_details.append(list(project) + [milestones, comments])

    conn.close()
    return render_template(
        'index.html',
        projects=projects_with_details,
        username=session.get('username')
    )

# ==============================
# SIGNUP
# ==============================
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, password)
    )
    conn.commit()
    conn.close()
    return redirect('/')

# ==============================
# LOGIN
# ==============================
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()

    if user:
        session['username'] = user[0]
        return redirect('/')
    else:
        return "Invalid login ❌"

# ==============================
# LOGOUT
# ==============================
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# ==============================
# ADD PROJECT
# ==============================
@app.route('/add_project', methods=['POST'])
def add_project():
    if 'username' not in session:
        return "Login required"

    username = session['username']
    project_name = request.form['project_name']
    stage = request.form['stage']
    support = request.form['support']
    tags = request.form.get('tags', '')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user_id = c.fetchone()[0]

    c.execute('''
        INSERT INTO projects (user_id, project_name, stage, support_needed, tags)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, project_name, stage, support, tags))

    conn.commit()
    conn.close()
    return redirect('/')

# ==============================
# ADD MILESTONE
# ==============================
@app.route('/add_milestone', methods=['POST'])
def add_milestone():
    if 'username' not in session:
        return "Login required"

    project_id = request.form['project_id']
    milestone = request.form['milestone']
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO milestones (project_id, milestone, date_created)
        VALUES (?, ?, ?)
    ''', (project_id, milestone, date_created))
    conn.commit()
    conn.close()
    return redirect('/')

# ==============================
# COMPLETE PROJECT
# ==============================
@app.route('/complete_project', methods=['POST'])
def complete_project():
    if 'username' not in session:
        return "Login required"

    project_id = request.form['project_id']

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE projects SET completed=1 WHERE id=?", (project_id,))
    conn.commit()
    conn.close()
    return redirect('/')

# ==============================
# ADD COMMENT
# ==============================
@app.route('/add_comment', methods=['POST'])
def add_comment():
    if 'username' not in session:
        return "Login required"

    project_id = request.form['project_id']
    comment = request.form['comment']
    username = session['username']
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO comments (project_id, username, comment, date_created)
        VALUES (?, ?, ?, ?)
    ''', (project_id, username, comment, date_created))
    conn.commit()
    conn.close()
    return redirect('/')

# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    app.run(debug=True)

# ==============================
# FILTER / SEARCH PROJECTS
# ==============================
@app.route('/search', methods=['GET'])
def search_projects():
    query = request.args.get('q', '').lower()  # Get search query from URL
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM projects")
    projects = c.fetchall()

    # Filter projects that match the query in name, stage, or support_needed
    filtered_projects = []
    for project in projects:
        project_id = project[0]
        c.execute("SELECT milestone FROM milestones WHERE project_id=?", (project_id,))
        milestones = [m[0] for m in c.fetchall()]

        project_data = list(project) + [milestones]
        if query in project[2].lower() or query in project[3].lower() or query in project[4].lower():
            filtered_projects.append(project_data)

    conn.close()
    return render_template(
        'index.html',
        projects=filtered_projects,
        username=session.get('username'),
        search_query=query
    )