from flask import *
import pymysql
import functions
from datetime import datetime

# create a new app based on flask
app = Flask(__name__)

# below is the register route


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        role = "student"

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()

        # Insert user
        sql = "INSERT INTO users(fullname, email, phone, password, role) VALUES (%s, %s, %s, %s, %s)"
        data = (fullname, email, phone, functions.hash_password_salt(password), role)
        cursor.execute(sql, data)
        connection.commit()

        # Log registration
        try:
            timestamp = datetime.now()
            performed_by = session.get("user_name", "Anonymous")  # Could be 'admin' or self-registration
            action = f"Registered new user: {fullname} ({email}) as a {role}"
            log_sql = "INSERT INTO logs (timestamp, performed_by, action) VALUES (%s, %s, %s)"
            cursor.execute(log_sql, (timestamp, performed_by, action))
            connection.commit()
        except Exception as e:
            print("Failed to log action:", e)

        cursor.close()
        connection.close()

        message = "User registered successfully"
        return render_template("register.html", message=message)

    
app.secret_key = "gfyr6458692nwvcud8292enfu4funmwimdof02n10cnf58"

# login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        password = request.form["password"]

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()

        cursor.execute("select * from users where email=%s", (email,))
        user = cursor.fetchone()

        if user:
            db_password = user[3]
            role = user[5]
            fullname = user[1]

            if functions.verify_password_salt(db_password, password):
                session["user_name"] = fullname
                session["role"] = role
                session["user_id"] = user[0]
                session["user_email"] = email

                
                log_sql = "INSERT INTO logs (user_id, action, timestamp) VALUES (%s, %s, NOW())"
                cursor.execute(log_sql, (user[0], f"{role.capitalize()} '{fullname}' logged in"))
                connection.commit()

                
                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif role == "teacher":
                    return redirect(url_for("teacher_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))
            else:
                return render_template("login.html", message="Incorrect password")
        else:
            return render_template("login.html", message="Email not found")

# student dashboard    
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") == "student":
        connection = pymysql.connect(
            host="localhost", user="root", password="", database="school_db"
        )
        cursor = connection.cursor()

        # Log the dashboard view
        log_message = f"Student '{session.get('user_name')}' viewed the student dashboard"
        cursor.execute("""
            INSERT INTO logs (user_id, action)
            VALUES (%s, %s)
        """, (session.get("user_id"), log_message))

        # Get all upcoming assignments, ordered by due date
        cursor.execute("""
            SELECT title, description, due_date, posted_at, attachment_url
            FROM assignments
            ORDER BY due_date ASC
        """)
        assignments = cursor.fetchall()

        connection.commit()
        cursor.close()
        connection.close()

        return render_template(
            "student_dashboard.html",
            name=session.get("user_name"),
            assignments=assignments
        )
    return redirect(url_for("login"))



# teacher dashboard
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()

    cursor.execute("SELECT user_id FROM users WHERE email=%s", (session.get("user_email"),))
    teacher = cursor.fetchone()

    if not teacher:
        return "Teacher not found"

    teacher_id = teacher[0]

    cursor.execute("""
        INSERT INTO logs (user_id, action, timestamp)
        VALUES (%s, %s, NOW())
    """, (teacher_id, "Accessed Teacher Dashboard"))
    connection.commit()

    cursor.execute("""
        SELECT title, description, due_date, posted_at 
        FROM assignments 
        WHERE teacher_id=%s 
        ORDER BY posted_at DESC
    """, (teacher_id,))
    assignments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("teacher_dashboard.html", name=session.get("user_name"), assignments=assignments)

# admin dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") == "admin":
        return render_template("admin_dashboard.html", name=session.get("user_name"))
    return redirect(url_for("login"))
  
# editing
@app.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()

    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]

        # Update the user info
        cursor.execute("""
            UPDATE users
            SET fullname = %s, email = %s, phone = %s, role = %s
            WHERE user_id = %s
        """, (fullname, email, phone, role, user_id))

        connection.commit()

        # Log the edit action
        admin_id = session.get("user_id")
        action = f"Edited user with ID {user_id}"
        cursor.execute("INSERT INTO logs (action, user_id) VALUES (%s, %s)", (action, admin_id))
        connection.commit()

        flash("User updated successfully!", "success")
        cursor.close()
        connection.close()
        return redirect(url_for("admin_dashboard"))

    # For GET request
    cursor.execute("SELECT user_id, fullname, email, phone, role FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    
    return render_template("edit_user.html", user=user)


# view users
@app.route("/admin/users")
def admin_users():
    if session.get("role") == "admin":
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, fullname, email, phone, role FROM users")
        users = cursor.fetchall()
        connection.close()
        return render_template("view_users.html", users=users, name=session.get("user_name"))
    return redirect(url_for("login"))

# admin recheck
@app.route("/admin/confirm", methods=["GET", "POST"])
def confirm_admin_password():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        entered_password = request.form["password"]

        if entered_password == "admin1234":
            session["admin_confirmed"] = True
            return redirect(url_for("view_logs"))  
        else:
            return render_template("confirm_admin.html", error="Incorrect password")

    return render_template("confirm_admin.html")


# view logs
@app.route("/admin/logs")
def view_logs():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()

    # Join logs and users to get full log details
    cursor.execute("""
        SELECT logs.timestamp, users.fullname, users.email, logs.action
        FROM logs
        JOIN users ON logs.user_id = users.user_id
        ORDER BY logs.timestamp DESC
    """)
    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("view_logs.html", logs=logs)



# update
@app.route("/admin/user/<int:user_id>/update", methods=["POST"])
def update_user(user_id):
    if session.get("role") == "admin":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()

        sql = "update users set fullname=%s, email=%s, phone=%s, role=%s where user_id=%s"
        data = (fullname, email, phone, role, user_id)
        cursor.execute(sql, data)

        connection.commit()

        return redirect(url_for("admin_users"))
    return redirect(url_for("login"))

# assignment
@app.route("/teacher/assignments/create", methods=["GET", "POST"])
def create_assignment():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        teacher_email = session.get("user_email")

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()

        cursor.execute("SELECT user_id FROM users WHERE email=%s", (teacher_email,))
        teacher = cursor.fetchone()

        if teacher:
            teacher_id = teacher[0]

            # Insert assignment
            sql = """
                INSERT INTO assignments (title, description, due_date, teacher_id)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (title, description, due_date, teacher_id))
            connection.commit()

            
            log_action = f"Posted new assignment: {title}"
            cursor.execute("INSERT INTO logs (user_id, action, timestamp) VALUES (%s, %s, NOW())", (teacher_id, log_action))
            connection.commit()

            cursor.close()
            connection.close()
            return redirect(url_for("teacher_dashboard"))
        else:
            return "Teacher not found"

    return render_template("create_assignment.html")


# delete
@app.route("/admin/user/<int:user_id>/delete", methods=["GET", "POST"])
def delete_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()

    cursor.execute("SELECT fullname FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if request.method == "POST":
        if user:
            user_name = user[0]
            
            # Delete the user
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            
            # Log the deletion
            action = f"Deleted user {user_name}"
            admin_id = session.get("user_id")  # Make sure this is set at login!
            cursor.execute("INSERT INTO logs (action, user_id) VALUES (%s, %s)", (action, admin_id))
            
            connection.commit()
            flash(f"User '{user_name}' has been deleted.", "success")
        else:
            flash("User not found.", "danger")

        cursor.close()
        connection.close()
        return redirect(url_for("admin_dashboard"))

    cursor.close()
    connection.close()
    return render_template("delete_user.html", user=user)






@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    user_name = session.get("user_name")
    role = session.get("role")

    # Only log if user is logged in
    if user_id and user_name and role:
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        log_sql = "INSERT INTO logs (user_id, action, timestamp) VALUES (%s, %s, NOW())"
        cursor.execute(log_sql, (user_id, f"{role.capitalize()} '{user_name}' logged out"))
        connection.commit()
        cursor.close()
        connection.close()

    session.clear()
    return redirect(url_for("login"))



# run the app
app.run(debug=True)