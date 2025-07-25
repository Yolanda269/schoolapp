from flask import *
import pymysql
import functions


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

        # establish connection to db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        # create a cursor that enables executing sql
        cursor = connection.cursor()

        # structure the sql query for insert
        sql = "INSERT INTO users(fullname, email, phone, password, role) values(%s, %s, %s, %s, %s)"

        # put the data into a tuple
        data = (fullname, email, phone, functions.hash_password_salt(password), role)

        # execute
        cursor.execute(sql, data)

        # commit changes to db
        connection.commit()

        message = "User registered successfully"

        # if successful, render message back
        return render_template("register.html", message=message)
    
app.secret_key = "gfyr6458692nwvcud8292enfu4funmwimdof02n10cnf58"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        password = request.form["password"]

        # create connection
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        # create a cursor that enables executing sql
        cursor = connection.cursor()

        # structure query for login
        sql = "select * from users where email=%s"

        data = (email,)

        # execute
        cursor.execute(sql, data)

        # if the details are correct, put them into a usrs variable
        user = cursor.fetchone()

        if user:
            db_password = user[3]
            role = user[5]
            fullname = user[1]

            # verify
            if functions.verify_password_salt(db_password, password):
                session["user_name"] = fullname
                session["role"] = role
                session["user_id"] = user[0]
                session["user_email"] = email

                # based on role redirect a person to a given dashoard
                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif role == "teacher":
                    return redirect(url_for("teacher_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))
            else: 
                return render_template("login.html", message = "Incorrect password")
        else:
            return render_template("login.html", message = "Email not found")
        
# student dashboard    
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") == "student":
        connection = pymysql.connect(
            host="localhost", user="root", password="", database="school_db"
        )
        cursor = connection.cursor()

        # Get all upcoming assignments, ordered by due date
        cursor.execute("""
            SELECT title, description, due_date, posted_at, attachment_url
            FROM assignments
            ORDER BY due_date ASC
        """)
        assignments = cursor.fetchall()

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

    cursor.execute("select user_id from users where email=%s", (session.get("user_email")))
    teacher = cursor.fetchone()

    if not teacher:
        return "Teacher not found"
    
    teacher_id = teacher[0]

    cursor.execute("select title, description, due_date, posted_at from assignments where teacher_id=%s order by posted_at DESC", (teacher_id,))

    assignments = cursor.fetchall()

    return render_template("teacher_dashboard.html", name=session.get("user_name"), assignments = assignments)
    

# admin dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") == "admin":
        # create connection
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()
        cursor.execute("select user_id, fullname, email, phone, role from users")

        users = cursor.fetchall()

        return render_template("admin_dashboard.html", name = session.get("user_name"), users = users)
    return redirect(url_for("login"))  

# editing
@app.route("/admin/user/<int:user_id>/edit", methods=["GET"])
def edit_user(user_id):
    if session.get("role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()
        cursor.execute("select user_id, fullname, email, phone, role from users where user_id = %s", (user_id, ))
        user = cursor.fetchone()
        return render_template("edit_user.html", user = user)
    return redirect(url_for("login"))

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

        return redirect(url_for("admin_dashboard"))
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

        # Get teacher ID from session (assuming you store user_id after login)
        teacher_email = session.get("user_email")

        # Connect to DB to fetch teacher ID
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (teacher_email,))
        teacher = cursor.fetchone()

        if teacher:
            teacher_id = teacher[0]

            sql = "INSERT INTO assignments (title, description, due_date, teacher_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (title, description, due_date, teacher_id))
            connection.commit()
            return redirect(url_for("teacher_dashboard"))
        else:
            return "Teacher not found"

    return render_template("create_assignment.html")

# delete
@app.route("/admin/user/<int:user_id>/delete", methods=["GET", "POST"])
def delete_user(user_id):
    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()

    cursor.execute("SELECT fullname FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if request.method == "POST":
        if user:
            user_name = user[0]
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
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
    session.clear()
    return redirect(url_for("login"))


# run the app
app.run(debug=True)