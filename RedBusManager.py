from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import LoginManager, login_user, current_user, UserMixin, logout_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'PRAMOD_J'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_staff = db.Column(db.Boolean, nullable=False)

    def __init__(self, name, email, password, is_staff):
        self.name = name
        self.email = email
        self.password = password
        self.is_staff = is_staff

    def __repr__(self):
        return f'email: {self.email}, password: {self.password}'


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about-us')
def about_us():
    return render_template('about.html')


@app.route('/delete/<string:email>')
def delete_user(email):
    user = Users.query.filter_by(email=email).first()
    db.session.delete(user)
    db.session.commit()

    with open("RedBus/users.txt", "r") as f:
        lines = f.readlines()
    with open("RedBus/users.txt", "w") as f:
        for line in lines:
            if email not in line:
                f.write(line)

    flash(user.email, "warning")
    users = Users.query.all()
    return render_template('admin_users_panel.html', users=users)
    pass


@app.route('/admin_users')
def admin_users_panel():
    if current_user.is_authenticated:
        users = Users.query.all()
        return render_template('admin_users_panel.html', users=users)
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin_buses')
def admin_buses_panel():
    if current_user.is_authenticated:
        buses = []

        with open('RedBus/buses.txt', 'rt') as f:
            for line in f.readlines():
                bus_data = line.split("|")
                bus = {
                    "id": bus_data[0],
                    "from": bus_data[1],
                    "to": bus_data[2],
                    "pickup_location": bus_data[3],
                    "boarding_time": bus_data[4],
                    "deboarding_time": bus_data[5]
                }

                buses.append(bus)

        return render_template('admin_buses_panel.html', buses=buses)
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()

        if user:
            if user.password == password:
                login_user(user, True)
                return redirect(url_for('admin_users_panel'))
            else:
                flash('Invalid admin credentials', 'warning')
                return render_template('admin_login.html')
        else:
            flash('No record found, check your credentials', 'warning')
            return render_template('admin_login.html')

    else:
        return render_template('admin_login.html')


@app.route('/logout')
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))


if __name__ == "__main__":
    app.run(debug=True)
