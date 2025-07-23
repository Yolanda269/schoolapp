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
        return render_template("student_dashboard.html", name = session.get("user_name"))
    return redirect(url_for("login"))

# teacher dashboard
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if session.get("role") == "teacher":
        return render_template("teacher_dashboard.html", name = session.get("user_name"))
    return redirect(url_for("login"))

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# run the app
app.run(debug=True)