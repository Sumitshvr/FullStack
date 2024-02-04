from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_manager, LoginManager
from flask_login import login_required, current_user
import json
from sqlalchemy import text


# MY db connection
local_server = True
app = Flask(__name__)
app.secret_key = 'sushilandsumit'


# this is for getting unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@127.0.0.1:3608/childdbms'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# db.create_all()

# here we will create db models that is tables


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    programme = db.Column(db.String(100))
    teacher_name = db.Column(db.String(100))


class Attendance(db.Model):
    aid = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(100))
    attendance = db.Column(db.Integer())


class Reminders(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(100))
    action = db.Column(db.String(100))
    timestamp = db.Column(db.String(100))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    teacher_email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))


class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(50))
    name = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    programme = db.Column(db.String(50))
    parent_email = db.Column(db.String(50))
    parent_number = db.Column(db.String(12))
    address = db.Column(db.String(100))

# db.create_all()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/childdetails')
def childdetails():
    query = db.session.execute(text(f"SELECT * FROM `child`"))
    return render_template('childdetails.html', query=query)


@app.route('/triggers')
def triggers():
    query = db.session.execute(text(f"SELECT * FROM `reminders`"))
    return render_template('triggers.html', query=query)


@app.route('/department', methods=['POST', 'GET'])
def department():
    if request.method == "POST":
        programme = request.form.get('classroom')
        teacher_name = request.form.get('teacher_name')
        query = Classroom.query.filter_by(programme=programme).first()
        if query:
            flash("Class Already Exist", "warning")
            return redirect('/department')
        dep = Classroom(programme=programme, teacher_name=teacher_name)
        db.session.add(dep)
        db.session.commit()
        flash("Class Added", "success")
    return render_template('department.html')


@app.route('/addattendance', methods=['POST', 'GET'])
def addattendance():
    query = db.session.execute(text(f"SELECT * FROM `child`"))
    if request.method == "POST":
        rollno = request.form.get('rollno')
        attend = request.form.get('attend')
        print(attend, rollno)
        atte = Attendance(rollno=rollno, attendance=attend)
        db.session.add(atte)
        db.session.commit()
        flash("Attendance added", "warning")

    return render_template('attendance.html', query=query)


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == "POST":
        rollno = request.form.get('roll')
        bio = Child.query.filter_by(rollno=rollno).first()
        attend = Attendance.query.filter_by(rollno=rollno).first()
        return render_template('search.html', bio=bio, attend=attend)

    return render_template('search.html')


@app.route("/delete/<string:id>", methods=['POST', 'GET'])
@login_required
def delete(id):
    db.session.execute(text(f"DELETE FROM `child` WHERE `child`.`id`={id}"))
    flash("Slot Deleted Successful", "danger")
    return redirect('/childdetails')


@app.route("/edit/<string:id>", methods=['POST', 'GET'])
@login_required
def edit(id):
    dept = db.session.execute(text("SELECT * FROM `classroom`"))
    posts = Child.query.filter_by(id=id).first()
    if request.method == "POST":
        rollno = request.form.get('rollno')
        name = request.form.get('name')
        gender = request.form.get('gender')
        programme = request.form.get('programme')
        parent_email = request.form.get('parent_email')
        parent_number = request.form.get('parent_number')
        address = request.form.get('address')
        query = db.session.execute(text(
            f"UPDATE `child` SET `rollno`='{rollno}',`name`='{name}',`gender`='{gender}',`programme`='{programme}',`parent_email`='{parent_email}',`parent_number`='{parent_number}',`address`='{address}'WHERE `id` = {id}"))
        flash("Slot is Updated", "success")
        return redirect('/childdetails')

    return render_template('edit.html', posts=posts, dept=dept)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        teacher_email = request.form.get('teacher_email')
        password = request.form.get('password')
        user = User.query.filter_by(teacher_email=teacher_email).first()
        if user:
            flash("Email Already Exist", "warning")
            return render_template('/signup.html')
        encpassword = generate_password_hash(password)

        # new_user = db.session.execute(text(
        #     f"INSERT INTO `user` (`username`,`teacher_email`,`password`) VALUES ('{username}','{teacher_email}','{encpassword}')"))
        new_user = User(username=username, teacher_email=teacher_email, password=encpassword)

        # this is method 2 to save data in db
        # newuser=User(username=username,email=teacher_email,password=encpassword)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup Succes Please Login", "success")
        return render_template('login.html')

    return render_template('signup.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        teacher_email = request.form.get('teacher_email')
        password = request.form.get('password')
        user = User.query.filter_by(teacher_email=teacher_email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Success", "primary")
            return redirect(url_for('index'))
        else:
            flash("invalid credentials", "danger")
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul", "warning")
    return redirect(url_for('login'))


@app.route('/addchild', methods=['POST', 'GET'])
@login_required
def addchild():
    dept = db.session.execute(text("SELECT * FROM `classroom`"))
    if request.method == "POST":
        rollno = request.form.get('rollno')
        name = request.form.get('name')
        gender = request.form.get('gender')
        programme = request.form.get('programme')
        parent_email = request.form.get('parent_email')
        parent_number = request.form.get('parent_number')
        address = request.form.get('address')
        # query = db.session.execute(text(
            # f"INSERT INTO `child` (`rollno`,`name`,`gender`,`programme`,`parent_email`,`parent_number`,`address`) VALUES ('{rollno}','{name}','{gender}','{programme}','{parent_email}','{parent_number}','{address}')"))
        child = Child(rollno=rollno, name=name, gender=gender, programme=programme, 
                      parent_email=parent_email, parent_number=parent_number, address=address)
        
        db.session.add(child)
        db.session.commit()
        flash("Booking Confirmed", "info")

    return render_template('child.html', dept=dept)


@app.route('/test')
def test():
    try:
        Assessment.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'


app.run(debug=True)
