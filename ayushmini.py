import os
import sqlite3
from datetime import date
from functools import wraps
from flask import Flask, request, redirect, url_for, session, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "CHANGE-THIS-LOCAL-DEMO-KEY")
DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

# DEMO LOGIN CREDENTIALS
DEMO_EMAIL = "faculty@example.com"
DEMO_PASSWORD_HASH = generate_password_hash("ChangeMe123!")

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS classes (
                class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                academic_year TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL,
                full_name TEXT NOT NULL,
                class_id INTEGER NOT NULL REFERENCES classes(class_id),
                active INTEGER NOT NULL DEFAULT 1,
                UNIQUE(class_id, roll_no)
            );
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_code TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                class_id INTEGER NOT NULL REFERENCES classes(class_id),
                UNIQUE(class_id, subject_code)
            );
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL REFERENCES classes(class_id),
                subject_id INTEGER NOT NULL REFERENCES subjects(subject_id),
                attendance_date TEXT NOT NULL,
                label TEXT NOT NULL DEFAULT 'Regular',
                created_by TEXT NOT NULL,
                UNIQUE(class_id, subject_id, attendance_date, label)
            );
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES attendance_sessions(session_id)
                    ON DELETE CASCADE,
                student_id INTEGER NOT NULL REFERENCES students(student_id),
                status TEXT NOT NULL CHECK(status IN ('Present','Absent','Late')),
                remarks TEXT,
                UNIQUE(session_id, student_id)
            );
        """)
        if conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0] == 0:
            conn.execute("INSERT INTO classes(class_name, academic_year) VALUES (?,?)", ("TYBSc CS - Demo", "2026-2027"))
            class_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO subjects(subject_code, subject_name, class_id) VALUES (?,?,?)",
                         ("CS-DEMO", "Computer Science (Demo)", class_id))
            conn.executemany(
                "INSERT INTO students(roll_no, full_name, class_id) VALUES (?,?,?)",
                [("D01", "Demo Student One", class_id),
                 ("D02", "Demo Student Two", class_id),
                 ("D03", "Demo Student Three", class_id)]
            )

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("faculty_email"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

# --- DESIGN, COLORS & ANIMATIONS ---
COMMON_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Poppins', sans-serif; }

body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    color: #2d3748;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    width: 100%;
    max-width: 800px;
    padding: 40px;
    border-radius: 16px;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
    animation: fadeIn 0.5s ease-out forwards;
}

h1, h2, h3 { color: #1a202c; margin-bottom: 15px; font-weight: 600; }
p { color: #4a5568; margin-bottom: 20px; }

label {
    display: block;
    font-weight: 500;
    margin-bottom: 6px;
    color: #4a5568;
    font-size: 14px;
}

input, select {
    width: 100%;
    padding: 12px 15px;
    margin-bottom: 20px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 15px;
    transition: all 0.3s ease;
    background: #f8fafc;
}

input:focus, select:focus {
    border-color: #667eea;
    background: #fff;
    outline: none;
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
}

button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 20px;
    width: 100%;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.nav-links {
    display: flex;
    justify-content: flex-end;
    gap: 15px;
    margin-bottom: 20px;
}

.nav-links a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s;
}

.nav-links a:hover { color: #764ba2; text-decoration: underline; }

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 0 20px rgba(0,0,0,0.05);
}

th, td {
    padding: 12px 15px;
    text-align: left;
}

th {
    background: #667eea;
    color: white;
    font-weight: 500;
}

tr:nth-child(even) { background: #f8fafc; }
tr:hover { background: #edf2f7; }

.alert-error {
    color: #e53e3e;
    background: #fff5f5;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
    border-left: 4px solid #e53e3e;
    font-weight: 500;
}

.alert-success {
    color: #38a169;
    background: #f0fff4;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
    border-left: 4px solid #38a169;
    font-weight: 500;
}
"""

LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
    <title>Login - Attendance Portal</title>
    <style>""" + COMMON_STYLE + """</style>
</head>
<body>
<div class="container" style="max-width: 420px;">
    <h2 style="text-align: center; color: #667eea;">Attendance Portal</h2>
    <h3 style="text-align: center; color: #718096; font-size: 16px; margin-bottom: 25px;">Faculty Sign In</h3>
    
    {% with messages = get_flashed_messages() %}
      {% for message in messages %}
        <div class="alert-error">{{ message }}</div>
      {% endfor %}
    {% endwith %}
    
    <form method="post">
        <label>Email Address</label>
        <input name="email" type="email" placeholder="faculty@example.com" required>
        
        <label>Password</label>
        <input name="password" type="password" placeholder="••••••••" required>
        
        <button type="submit">Sign In to Dashboard</button>
    </form>
    
    <p style="text-align: center; margin-top: 20px; font-size: 13px; color: #a0aec0;">
        Demo account: <b>faculty@example.com</b> / <b>ChangeMe123!</b>
    </p>
</div>
</body>
</html>
"""

ATTENDANCE_HTML = """
<!doctype html>
<html lang="en">
<head>
    <title>Mark Attendance</title>
    <style>""" + COMMON_STYLE + """</style>
</head>
<body>
<div class="container">
    <div class="nav-links">
        <a href="{{ url_for('reports') }}">📊 View Reports</a>
        <a href="{{ url_for('logout') }}" style="color: #e53e3e;">🚪 Logout</a>
    </div>
    
    <h1>Mark Attendance</h1>
    <p>Welcome back, <b>{{ email }}</b></p>
    
    {% with messages = get_flashed_messages() %}
      {% for message in messages %}
        <div class="alert-success">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="post">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
                <label>Select Class</label>
                <select name="class_id" required>
                    {% for c in classes %}
                    <option value="{{ c.class_id }}">{{ c.class_name }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div>
                <label>Select Subject</label>
                <select name="subject_id" required>
                    {% for s in subjects %}
                    <option value="{{ s.subject_id }}">{{ s.subject_name }}</option>
                    {% endfor %}
                </select>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
                <label>Attendance Date</label>
                <input type="date" name="attendance_date" value="{{ today }}" max="{{ today }}" required>
            </div>
            
            <div>
                <label>Session Label</label>
                <input name="label" value="Regular" required>
            </div>
        </div>

        <h3 style="margin-top: 20px;">Students Roster</h3>
        <table>
            <tr>
                <th>Roll No</th>
                <th>Student Name</th>
                <th>Status</th>
            </tr>
            {% for student in students %}
            <tr>
                <td><b>{{ student.roll_no }}</b></td>
                <td>{{ student.full_name }}</td>
                <td>
                    <select name="status_{{ student.student_id }}" required style="margin-bottom: 0; padding: 6px 10px;">
                        <option value="Present">Present</option>
                        <option value="Absent">Absent</option>
                        <option value="Late">Late</option>
                    </select>
                </td>
            </tr>
            {% endfor %}
        </table>

        <button type="submit" style="margin-top: 15px;">💾 Save Attendance Record</button>
    </form>
</div>
</body>
</html>
"""

REPORTS_HTML = """
<!doctype html>
<html lang="en">
<head>
    <title>Attendance Summary Report</title>
    <style>""" + COMMON_STYLE + """</style>
</head>
<body>
<div class="container">
    <div class="nav-links">
        <a href="{{ url_for('attendance_page') }}">← Back to Attendance</a>
        <a href="{{ url_for('logout') }}" style="color: #e53e3e;">🚪 Logout</a>
    </div>
    
    <h2>Attendance Summary Report</h2>
    <p>Overview of student attendance counts and percentages.</p>
    
    <table>
        <tr>
            <th>Roll No</th>
            <th>Full Name</th>
            <th>Present/Late Count</th>
            <th>Total Sessions</th>
            <th>Attendance %</th>
        </tr>
        {% for r in result %}
        <tr>
            <td><b>{{ r[0] }}</b></td>
            <td>{{ r[1] }}</td>
            <td>{{ r[2] }}</td>
            <td>{{ r[3] }}</td>
            <td>
                <span style="font-weight: 600;">
                    {{ r[4] if r[4] is not none else 'N/A' }}%
                </span>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>
"""

# --- ROUTES ---

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if email == DEMO_EMAIL and check_password_hash(DEMO_PASSWORD_HASH, password):
            session.clear()
            session["faculty_email"] = email
            return redirect(url_for("attendance_page"))
        flash("Invalid email or password.")
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance_page():
    with connect_db() as conn:
        classes = conn.execute("SELECT * FROM classes ORDER BY class_name").fetchall()
        subjects = conn.execute("SELECT * FROM subjects ORDER BY subject_name").fetchall()
        students = conn.execute("SELECT * FROM students WHERE active=1 ORDER BY roll_no").fetchall()
        
        if request.method == "POST":
            try:
                class_id = int(request.form["class_id"])
                subject_id = int(request.form["subject_id"])
                attendance_date = request.form["attendance_date"]
                label = request.form.get("label", "Regular").strip() or "Regular"
                
                date.fromisoformat(attendance_date)
                if attendance_date > date.today().isoformat():
                    raise ValueError("Future attendance dates are not allowed.")

                valid = conn.execute("SELECT 1 FROM subjects WHERE subject_id=? AND class_id=?", (subject_id, class_id)).fetchone()
                if not valid:
                    raise ValueError("The selected subject does not belong to this class.")

                cur = conn.execute(
                    """INSERT INTO attendance_sessions (class_id, subject_id, attendance_date, label, created_by)
                       VALUES (?, ?, ?, ?, ?)""",
                    (class_id, subject_id, attendance_date, label, session["faculty_email"])
                )
                session_id = cur.lastrowid
                
                roster = conn.execute("SELECT student_id FROM students WHERE class_id=? AND active=1", (class_id,)).fetchall()
                if not roster:
                    raise ValueError("No active students found in this class.")

                rows = []
                for row in roster:
                    field = "status_" + str(row["student_id"])
                    status = request.form.get(field, "")
                    if status not in {"Present", "Absent", "Late"}:
                        raise ValueError("Select a valid status for every student.")
                    rows.append((session_id, row["student_id"], status, None))

                conn.executemany(
                    "INSERT INTO attendance(session_id, student_id, status, remarks) VALUES (?, ?, ?, ?)", rows
                )
                conn.commit()
                flash("Attendance saved successfully!")
            except (ValueError, KeyError, sqlite3.IntegrityError) as exc:
                conn.rollback()
                flash("Error: " + str(exc))
            return redirect(url_for("attendance_page"))

    return render_template_string(
        ATTENDANCE_HTML, classes=classes, subjects=subjects,
        students=students, today=date.today().isoformat(),
        email=session["faculty_email"]
    )

@app.route("/reports")
@login_required
def reports():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT s.roll_no, s.full_name,
                   SUM(CASE WHEN a.status='Present' THEN 1 WHEN a.status='Late' THEN 1 ELSE 0 END) AS counted_present,
                   COUNT(a.attendance_id) AS total_sessions
            FROM students s
            LEFT JOIN attendance a ON a.student_id=s.student_id
            GROUP BY s.student_id
            ORDER BY s.roll_no
        """).fetchall()
        
    result = []
    for row in rows:
        total = row["total_sessions"] or 0
        present = row["counted_present"] or 0
        percent = round((present / total) * 100, 2) if total else None
        result.append((row["roll_no"], row["full_name"], present, total, percent))
        
    return render_template_string(REPORTS_HTML, result=result)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)