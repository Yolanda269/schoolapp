from flask import *
import pymysql


# create a new app basd on flask
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
        data = (fullname, email, phone, password, role)

        # execute
        cursor.execute(sql, data)

        # commit changes to db
        connection.commit()

        message = "User registered successfully"

        # if successful, render message back
        return render_template("register.html", message=message)
    

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
        sql = "select * from users where email=%s and password=%s"

        # tuple
        data = (email, password)

        # execute
        cursor.execute(sql, data)

        # if the details are correct, put them into a usrs variable
        user = cursor.fetchone()

        if user:
            return render_template("login.html", message = "Login successful")
        else:
             return render_template("login.html", message = "Login failed")
        
       



# run the app
app.run(debug=True)