from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import LoginManager, login_user, current_user, UserMixin, logout_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashlib import md5
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


def user_exist(email):
    user = Users.query.filter_by(email=email).first()
    if user:
        return True
    else:
        return False


@app.route('/RedBus/sign-in', methods=['POST', 'GET'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()

        if user:
            if user.password == password:
                login_user(user, True)
                return redirect(url_for('home'))
            else:
                flash('Invalid admin credentials', 'warning')
                return render_template('home.html')
        else:
            flash('No record found, check your credentials', 'warning')
            return render_template('user_login.html')

    else:
        return render_template('user_login.html')


@app.route('/RedBus/sign-up', methods=['POST', 'GET'])
def user_sign_up():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if not user_exist(email):
            user = Users(name, email, password, False)
            db.session.add(user)
            db.session.commit()

            with open("RedBus/users.txt", "at") as file:
                file.write(name + "|" + email + "|" + md5(password.encode()).hexdigest() + "|" + str(False) + "\n")

            return redirect(url_for('user_login'))

        else:
            print("User already exist")
            return render_template('user_sign_up.html')
    else:
        return render_template('user_sign_up.html')


@app.route('/')
@app.route('/RedBus/home')
def home():
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
                    "traveling_time": bus_data[5],
                    "no_of_seats": bus_data[6],
                    "price": bus_data[7]
                }

                buses.append(bus)

        return render_template('home.html', buses=buses, is_search=False)

    else:
        return redirect(url_for('user_login'))


@app.route('/RedBus/about-us')
def about_us():
    return render_template('about.html', is_search=False)


@app.route('/RedBus/current_user/<string:route_id>/booking', methods=['POST'])
def ticket_booking(route_id):
    form_data = {}
    with open('RedBus/buses.txt', 'rt') as f:
        for line in f.readlines():
            if route_id in line:
                data = line.split("|")
                form_data = {
                    "route_id": route_id,
                    "name": current_user.name,
                    "email": current_user.email,
                    "max_seat": data[-2],
                    "cost": data[-1]
                }
                break
    return render_template('booking.html', form_data=form_data)


@app.route('/RedBus/current_user/<string:route_id>/confirm_booking', methods=['POST'])
def confirm_booking(route_id):
    name = request.form['name']
    email = request.form['email']
    number_of_seats = request.form['number_of_seats']
    cost = request.form['cost']

    seats = None
    global lines

    with open('RedBus/buses.txt', 'rt') as f:
        lines = f.readlines()
        for line in lines:
            if route_id in line:
                data = line.split("|")
                seats = str(int(data[-2]) - int(number_of_seats))
                break

    with open('RedBus/buses.txt', 'wt') as f:
        for line in lines:
            if route_id in line:

                data = line.split("|")
                data[6] = seats
                f.write(route_id + "|"
                        + data[1] + "|"
                        + data[2] + "|"
                        + data[3] + "|"
                        + data[4] + "|"
                        + data[5] + "|"
                        + data[6] + "|"
                        + data[7])
            else:
                f.write(line)

    with open('RedBus/bookings.txt', 'rt') as f:
        bookings = json.load(f)
        try:
            bookings_list = bookings["bookings"][route_id]
            bookings_list.append({
                "booking_id": ("RedBus:" + ".".join(str(datetime.now().date()).replace("-", ""))),
                "name": name,
                "email": email,
                "number_of_seats": number_of_seats,
                "cost": cost
            })
        except KeyError:
            bookings["bookings"][route_id] = [{
                "booking_id": ("RedBus:" + ".".join(str(datetime.now().date()).replace("-", ""))),
                "name": name,
                "email": email,
                "number_of_seats": number_of_seats,
                "cost": cost
            }]

    with open('RedBus/bookings.txt', 'wt') as f:
        new_bookings = json.dumps(bookings)
        f.write(new_bookings)

    return redirect(url_for('home'))


@app.route('/RedBus/home/search', methods=['POST'])
def search():
    if current_user.is_authenticated:
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
                            "traveling_time": bus_data[5],
                            "no_of_seats": bus_data[6],
                            "price": bus_data[7]
                        }
                        buses.append(bus)

        return render_template('home.html', buses=buses, is_search_success=True, is_search=True)
    else:
        return redirect(url_for('user_login'))


@app.route('/logout')
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))


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
    if current_user.is_authenticated and current_user.is_staff:
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
                    "traveling_time": bus_data[5],
                    "no_of_seats": bus_data[6],
                    "price": bus_data[7]
                }

                buses.append(bus)

        return render_template('admin_buses_panel.html', buses=buses)
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin_booking')
def admin_booking_panel():
    if current_user.is_authenticated and current_user.is_staff:
        bookings = []
        route_ids = []

        with open('RedBus/bookings.txt', 'rt') as f:
            items = json.load(f)
            for item in items['bookings']:
                route_ids.append(item)

        with open('RedBus/buses.txt', 'rt') as f:
            for line in f.readlines():
                data = line.split("|")
                route_id = data[0]

                if route_id in route_ids:
                    booking = {
                        "route_id": route_id,
                        "from": data[1],
                        "to": data[2]
                    }

                    bookings.append(booking)

        return render_template('admin_booking_panel.html', bookings=bookings, show_specific_item_details=False)
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin_booking/<string:route_id>/details')
def admin_booking_item_details_panel(route_id):
    if current_user.is_authenticated and current_user.is_staff:

        with open('RedBus/bookings.txt', 'rt') as f:
            bookings_data = json.load(f)
            bookings = bookings_data["bookings"][route_id]

        return render_template('admin_booking_panel.html', bookings=bookings, show_specific_item_details=True)
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
        no_of_seats = request.form['no_of_seats']
        price = request.form['price']

        with open('RedBus/buses.txt', 'at') as f:
            f.write(str(route_id) + "|"
                    + from_location + "|"
                    + to_location + "|"
                    + pickup_location + "|"
                    + boarding_time + "|"
                    + traveling_time + "|"
                    + no_of_seats + "|"
                    + price + "\n")

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
    if current_user.is_authenticated and current_user.is_staff:
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
        logout_user()
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()

        if user:
            if user.password == password and user.is_staff:
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
