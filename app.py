import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    send_from_directory,
    url_for,
)

from db import (
    create_user_record,
    get_db_connection,
    hash_password,
    init_db_if_needed,
    search_tickets_query,
)
from parser import format_parsed_tags, parse_ticket_metadata

app = Flask(__name__)
app.secret_key = "campusdesk-default-dev-secret-key-2026"

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            flash("Please sign in to access CampusDesk.", "warning")
            return redirect(url_for("login_get"))
        return view_func(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------------------
# Endpoint 1: GET / (Dashboard, Search & Equipment Loans)
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
@login_required
def dashboard():
    search_q = request.args.get("q", "").strip()
    category = request.args.get("category", "all").strip()
    status = request.args.get("status", "all").strip()
    debug_sql = request.args.get("debug", "false").lower() == "true"

    role = session.get("role", "user")
    username = session.get("username", "")

    tickets = []
    executed_sql = ""
    error_message = None

    try:
        tickets, executed_sql = search_tickets_query(
            search_q, category, status, role, username
        )
    except Exception as exc:
        error_message = f"Database query error: {exc}"

    conn = get_db_connection()
    loans = conn.execute(
        "SELECT asset_tag, item_name, borrower_username, due_date FROM equipment_loans ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        tickets=tickets,
        loans=loans,
        search_q=search_q,
        category=category,
        status=status,
        executed_sql=executed_sql if debug_sql else None,
        error_message=error_message,
    )


# ---------------------------------------------------------------------------
# Endpoint 2: GET /login (Show Login Form)
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET"])
def login_get():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


# ---------------------------------------------------------------------------
# Endpoint 3: POST /login (Process Login Submission)
# ---------------------------------------------------------------------------
@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Both username and password are required.", "danger")
        return redirect(url_for("login_get"))

    pw_hash = hash_password(password)
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, pw_hash),
    ).fetchone()
    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["department"] = user["department"]
        flash(f"Welcome back, {user['username']} ({user['role']})!", "success")
        return redirect(url_for("dashboard"))

    flash("Invalid login credentials for username: " + username, "danger")
    return redirect(url_for("login_get"))


# ---------------------------------------------------------------------------
# Endpoint 4: GET /register (Show Registration Form)
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET"])
def register_get():
    return render_template("register.html")


# ---------------------------------------------------------------------------
# Endpoint 5: POST /register (Create New Account)
# ---------------------------------------------------------------------------
@app.route("/register", methods=["POST"])
def register_post():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    department = request.form.get("department", "Computer Science").strip()

    if not username or not email or not password:
        flash("All registration fields are required.", "danger")
        return redirect(url_for("register_get"))

    created = create_user_record(username, email, password, department)
    if not created:
        flash("Username already exists. Please choose another.", "danger")
        return redirect(url_for("register_get"))

    flash("Account registered! You can now sign in.", "success")
    return redirect(url_for("login_get"))


# ---------------------------------------------------------------------------
# Endpoint 6: POST /logout (End User Session)
# ---------------------------------------------------------------------------
@app.route("/logout", methods=["POST"])
def logout_post():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login_get"))


# ---------------------------------------------------------------------------
# Endpoint 7: GET /tickets/new (Show New Ticket Form)
# ---------------------------------------------------------------------------
@app.route("/tickets/new", methods=["GET"])
@login_required
def ticket_new_get():
    return render_template("ticket_new.html")


# ---------------------------------------------------------------------------
# Endpoint 8: POST /tickets/new (Submit Ticket, Parse Tags & Upload File)
# ---------------------------------------------------------------------------
@app.route("/tickets/new", methods=["POST"])
@login_required
def ticket_new_post():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "Network").strip()
    priority = request.form.get("priority", "normal").strip()
    description = request.form.get("description", "").strip()
    raw_tags = request.form.get("tags", "").strip()
    is_public = 1 if request.form.get("is_public") == "on" else 0

    if not title or not description:
        flash("Ticket title and description are required.", "danger")
        return redirect(url_for("ticket_new_get"))

    # Parse user-supplied metadata tags using custom parser module
    parsed_metadata = parse_ticket_metadata(raw_tags)
    normalized_tags = format_parsed_tags(parsed_metadata)

    # Handle optional diagnostic file upload
    attachment_name = None
    uploaded_file = request.files.get("attachment")
    if uploaded_file and uploaded_file.filename:
        attachment_name = uploaded_file.filename
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], attachment_name)
        uploaded_file.save(save_path)

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tickets (
            owner_id, owner_username, title, category, priority,
            status, description, parsed_tags, attachment_name, is_public, created_at
        )
        VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            session["username"],
            title,
            category,
            priority,
            description,
            normalized_tags,
            attachment_name,
            is_public,
            now_str,
        ),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    flash(f"Support ticket #{new_id} created.", "success")
    return redirect(url_for("ticket_detail_get", ticket_id=new_id))


# ---------------------------------------------------------------------------
# Endpoint 9: GET /tickets/<int:ticket_id> (View Ticket & Comments)
# ---------------------------------------------------------------------------
@app.route("/tickets/<int:ticket_id>", methods=["GET"])
@login_required
def ticket_detail_get(ticket_id: int):
    download_file = request.args.get("download")
    if download_file:
        return send_from_directory(app.config["UPLOAD_FOLDER"], download_file)

    conn = get_db_connection()
    ticket = conn.execute(
        "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
    ).fetchone()

    if not ticket:
        conn.close()
        flash("Ticket not found.", "warning")
        return redirect(url_for("dashboard"))

    comments = conn.execute(
        "SELECT * FROM comments WHERE ticket_id = ? ORDER BY id ASC",
        (ticket_id,),
    ).fetchall()
    conn.close()

    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        comments=comments,
    )


# ---------------------------------------------------------------------------
# Endpoint 10: POST /tickets/<int:ticket_id>/comment (Add Comment / Status)
# ---------------------------------------------------------------------------
@app.route("/tickets/<int:ticket_id>/comment", methods=["POST"])
@login_required
def ticket_comment_post(ticket_id: int):
    body = request.form.get("body", "").strip()
    new_status = request.form.get("status", "").strip()

    conn = get_db_connection()
    ticket = conn.execute(
        "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
    ).fetchone()

    if not ticket:
        conn.close()
        flash("Ticket does not exist.", "danger")
        return redirect(url_for("dashboard"))

    if new_status in ("open", "in_progress", "resolved", "closed"):
        conn.execute(
            "UPDATE tickets SET status = ? WHERE id = ?",
            (new_status, ticket_id),
        )

    if body:
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """
            INSERT INTO comments (ticket_id, author_username, author_role, body, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                session["username"],
                session.get("role", "user"),
                body,
                now_str,
            ),
        )

    conn.commit()
    conn.close()
    flash("Ticket updated.", "success")
    return redirect(url_for("ticket_detail_get", ticket_id=ticket_id))


if __name__ == "__main__":
    init_db_if_needed()
    app.run(host="0.0.0.0", port=8000, debug=True)