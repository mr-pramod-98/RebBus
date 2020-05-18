from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import LoginManager, login_user, current_user, UserMixin, logout_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

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
    return render_template('about.html', is_search=False)


@app.route('/search', methods=['POST'])
def search():
    buses = []
    from_location = request.form['from']

    # from
    with open('RedBus/Index/from_location.txt', 'r') as f:
        from_location_data = json.load(f)
        try:
            route_ids = from_location_data['from_location'][from_location]
        except KeyError:
            return render_template('home.html', buses=buses, is_search_success=False, is_search=True)

    with open('RedBus/buses.txt', 'r') as f:
        for route_id in route_ids:
            for line in f.readlines():
                if str(route_id) in line:
                    bus_data = line.split("|")
                    bus = {
                        "id": bus_data[0],
                        "from": bus_data[1],
                        "to": bus_data[2],
                        "pickup_location": bus_data[3],
                        "boarding_time": bus_data[4],
                        "traveling_time": bus_data[5]
                    }
                    buses.append(bus)

    return render_template('home.html', buses=buses, is_search_success=True, is_search=True)


@app.route('/admin_delete_user/<string:email>')
def admin_delete_user(email):
    if current_user.is_authenticated:
        user = Users.query.filter_by(email=email).first()
        db.session.delete(user)
        db.session.commit()

        with open("RedBus/users.txt", "r") as f:
            lines = f.readlines()
        with open("RedBus/users.txt", "w") as f:
            for line in lines:
                if email not in line:
                    f.write(line)

        flash(f'User with mail-id "{email}" deleted successfully', 'success')

        return redirect(url_for('admin_users_panel'))


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
                    "traveling_time": bus_data[5]
                }

                buses.append(bus)

        return render_template('admin_buses_panel.html', buses=buses)
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin_add_route', methods=['POST'])
def admin_add_route():
    if request.method == 'POST':
        route_id = abs(hash(str(datetime.now())) % (10 ** 8))
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        pickup_location = request.form['pickup_location']
        boarding_time = request.form['boarding_time']
        traveling_time = request.form['traveling_time'] + " hour"

        with open('RedBus/buses.txt', 'at') as f:
            f.write(str(route_id) + "|"
                    + from_location + "|"
                    + to_location + "|"
                    + pickup_location + "|"
                    + boarding_time + "|"
                    + traveling_time + "\n")

        # from
        with open('RedBus/Index/from_location.txt', 'r') as f:
            from_location_data = json.load(f)
            try:
                route_ids = from_location_data['from_location'][from_location]
                route_ids.append(route_id)
            except KeyError:
                from_location_data['from_location'][from_location] = [route_id]

        with open('RedBus/Index/from_location.txt', 'w') as f:
            locations = json.dumps(from_location_data)
            f.write(locations)

        # to
        with open('RedBus/Index/to_location.txt', 'r') as f:
            to_location_data = json.load(f)
            try:
                route_ids = to_location_data['to_location'][to_location]
                route_ids.append(route_id)
            except KeyError:
                to_location_data['to_location'][to_location] = [route_id]

        with open('RedBus/Index/to_location.txt', 'w') as f:
            locations = json.dumps(to_location_data)
            f.write(locations)

        flash(f'Route {route_id} add successfully', 'success')
        return redirect(url_for('admin_buses_panel'))


@app.route('/admin_delete_route/<string:route_id>')
def admin_delete_route(route_id):
    if current_user.is_authenticated:
        from_location = None
        to_location = None

        with open("RedBus/buses.txt", "r") as f:
            lines = f.readlines()
        with open("RedBus/buses.txt", "w") as f:
            for line in lines:
                if route_id not in line:
                    f.write(line)
                else:
                    from_location = line.split("|")[1]
                    to_location = line.split("|")[2]

        # from
        with open('RedBus/Index/from_location.txt', 'r') as f:
            from_location_data = json.load(f)
            route_ids = from_location_data['from_location'][from_location]
            route_ids.remove(int(route_id))

            if len(route_ids) == 0:
                del from_location_data['from_location'][from_location]

        with open('RedBus/Index/from_location.txt', 'w') as f:
            locations = json.dumps(from_location_data)
            f.write(locations)


        # to
        with open('RedBus/Index/to_location.txt', 'r') as f:
            to_location_data = json.load(f)
            route_ids = to_location_data['to_location'][to_location]
            route_ids.remove(int(route_id))

            if len(route_ids) == 0:
                del to_location_data['to_location'][to_location]

        with open('RedBus/Index/to_location.txt', 'w') as f:
            locations = json.dumps(to_location_data)
            f.write(locations)

        flash(f'Route with id "{route_id}" deleted successfully', 'success')
        return redirect(url_for('admin_buses_panel'))


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
