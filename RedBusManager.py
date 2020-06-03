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


# "user_login" METHOD IS CALLED WHET THE USER REQUEST FOR "sign-in" PAGE
@app.route('/RedBus/sign-in', methods=['POST', 'GET'])
def user_login():
    # IF THE REQUEST METHOD IS "POST" THEN EXECUTE if BLOCK
    if request.method == 'POST':

        # FETCHING "email" AND "password" FROM THE LOGIN PAGE
        email = request.form['email']
        password = request.form['password']

        # AUTHENTICATING THE USER
        # "user" EQUALS "None" IF THE "email" DOES NOT EXIST
        user = Users.query.filter_by(email=email).first()

        if user:

            if user.password == password:
                # REDIRECTING TO "/RedBus/home" PAGE AFTER SUCCESSFUL LOGIN
                login_user(user, True)
                return redirect(url_for('home'))
            else:
                # REDIRECTING BACK TO "login" IF THE "email" DOES NOT MATCH WITH IT'S THE CORRESPONDING "password"
                flash('Invalid credentials', 'warning')
                return render_template('user_login.html')

        else:
            # REDIRECTING BACK TO "login" IF THE "email" DOES NOT EXIST
            flash('No record found, check your credentials', 'warning')
            return render_template('user_login.html')

    # IF THE REQUEST METHOD IS GET EXECUTE else BLOCK
    else:
        return render_template('user_login.html')


# "user_sign_up" METHOD IS CALLED WHET THE USER REQUEST FOR "sign-up" PAGE
@app.route('/RedBus/sign-up', methods=['POST', 'GET'])
def user_sign_up():
    # IF THE REQUEST METHOD IS "POST" THEN EXECUTE if BLOCK
    if request.method == 'POST':

        # READING THE SENT DATA FROM THE REGISTRATION FORM
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # FORM VALIDATION --> START

        # IF THE USER RECORD WITH THE GIVEN CREDENTIALS DOES NOT EXIST THEN EXECUTE if BLOCK
        if not user_exist(email):

            # CREATING A USER RECORD IN THE "User" TABLE
            user = Users(name, email, password, False)
            db.session.add(user)
            db.session.commit()

            # CREATING A USER RECORD IN THE "RedBus/users.txt" FILE
            with open("RedBus/users.txt", "at") as file:
                file.write(name + "|" + email + "|" + md5(password.encode()).hexdigest() + "|" + str(False) + "\n")

            # REDIRECTING TO "login" PAGE AFTER USER VERIFICATION AND REGISTRATION
            return redirect(url_for('user_login'))

        # IF THE USER RECORD WITH THE GIVEN CREDENTIALS ALREADY EXIST THEN EXECUTE else BLOCK
        else:

            # REDIRECTING THE USER BACK TO THE "sign-up" PAGE
            flash("User already exist!")
            return render_template('user_sign_up.html')

        # FORM VALIDATION --> END

    # IF THE REQUEST METHOD IS GET EXECUTE else BLOCK
    else:
        return render_template('user_sign_up.html')


# "home" METHOD IS CALLED WHET THE USER LOGIN'S IN SUCCESSFULLY AND EVERY-TIME USER REQUESTS FOR "home" PAGE
@app.route('/')
@app.route('/RedBus/home')
def home():
    if current_user.is_authenticated:

        # "buses" IS USED TO HOLD ALL THE ROUTES IN THE FILE "RedBus/buses.txt"
        buses = []
        # "from_locations" IS USED TO HOLD ALL THE "FROM LOCATIONS" IN THE FILE "RedBus/Index/from_location.txt"
        from_locations = []
        # "to_locations" IS USED TO HOLD ALL THE "TO LOCATIONS" IN THE FILE "RedBus/Index/to_location.txt"
        to_locations = []

        # FETCHING ALL RECORDS( i.e, ROUTES) FORM "RedBus/buses.txt" FILE
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
                    "no_of_seats": int(bus_data[6]),
                    "price": bus_data[7]
                }

                # ADDING RECORD TO "buses" LIST
                buses.append(bus)

        # FETCHING ALL RECORDS( i.e, THE FROM LOCATIONS) FORM "RedBus/Index/from_location.txt" FILE
        with open('RedBus/Index/from_location.txt', 'rt') as f:
            from_location = json.load(f)
            for location in from_location['from_location']:

                # ADDING RECORD TO "from_locations" LIST
                from_locations.append(location)

        # FETCHING ALL RECORDS( i.e, THE TO LOCATIONS) FORM "RedBus/Index/to_location.txt" FILE
        with open('RedBus/Index/to_location.txt', 'rt') as f:
            to_location = json.load(f)
            for location in to_location['to_location']:

                # ADDING RECORD TO "to_locations" LIST
                to_locations.append(location)

        # RETURNING THE REQUESTED PAGE( i.e, home.html)
        return render_template('home.html', buses=buses, from_locations=from_locations,
                               to_locations=to_locations, is_search_success=False, is_search=False)

    else:
        return redirect(url_for('user_login'))


# "contact" METHOD IS CALLED WHET THE USER REQUEST FOR "contact" PAGE
@app.route('/RedBus/about-us')
def contact():
    if current_user.is_authenticated:

        # RETURNING THE REQUESTED PAGE( i.e, contact.html)
        return render_template('contact.html')
    else:
        return redirect(url_for('user_login'))


# "ticket_booking" METHOD IS CALLED WHET THE USER CLICK'S ON "Book" BUTTON
@app.route('/RedBus/current_user/<string:route_id>/booking', methods=['POST'])
def ticket_booking(route_id):

    # "form_data" IS USED TO HOLD THE DATA THAT IS REQUIRED TO SHOW ON "booking" PAGE
    form_data = {}
    with open('RedBus/buses.txt', 'rt') as f:
        for line in f.readlines():

            # FETCHING ALL THE DETAILS RELATED TO THE PARTICULAR "route_id" FROM "RedBus/buses.txt" FILE
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

    # RETURNING THE REQUESTED PAGE( i.e, booking.html)
    return render_template('booking.html', form_data=form_data)


# "confirm_booking" METHOD IS CALLED WHET THE USER CLICK'S ON "Confirm" BUTTON
@app.route('/RedBus/current_user/<string:route_id>/confirm_booking', methods=['POST'])
def confirm_booking(route_id):

    # READING THE SENT DATA FROM THE "booking" PAGE
    name = request.form['name']
    email = request.form['email']
    number_of_seats = request.form['number_of_seats']
    cost = request.form['cost']

    seats = None
    global lines

    # UPDATING THE NUMBER OF SEATS LEFT --> START
    with open('RedBus/buses.txt', 'rt') as f:
        lines = f.readlines()
        for line in lines:
            if route_id in line:
                data = line.split("|")

                # GET NUMBER OF SEATS LEFT
                seats = str(int(data[-2]) - int(number_of_seats))
                break

    with open('RedBus/buses.txt', 'wt') as f:
        for line in lines:
            if route_id in line:

                # UPDATE NUMBER OF SEATS LEFT
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

    # UPDATING THE NUMBER OF SEATS LEFT --> END

    # INSERT THE RECORD INTO "RedBus/bookings.txt" FILE --> START
    with open('RedBus/bookings.txt', 'rt') as f:

        # READ THE DATA FROM "RedBus/bookings.txt"
        bookings = json.load(f)
        try:
            bookings_list = bookings["bookings"][route_id]

            # GENERATING "booking_id" BY CONCATENATING "RedBus:" AND THE "DATE AND TIME" OF BOOKING
            booking_id = ("RedBus:" + ".".join(str(datetime.now().date()).replace("-", "")))
            bookings_list.append({
                "booking_id": booking_id,
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

        # WRITE THE DATA FROM "bookings" DICTIONARY TO "new_bookings"
        new_bookings = json.dumps(bookings)
        f.write(new_bookings)

    # INSERT THE RECORD INTO "RedBus/bookings.txt" FILE --> START

    # REDIRECTING TO "/RedBus/home" PAGE AFTER SUCCESSFUL BOOKING TO THE TICKET ( i.e, home.html)
    return redirect(url_for('home'))


# "search" METHOD IS CALLED WHET THE USER CLICK'S ON "Search" BUTTON
@app.route('/RedBus/home/<string:from_location>/<string:to_location>/search-result')
def search(from_location, to_location):
    if current_user.is_authenticated:

        # "buses" IS USED TO HOLD ALL THE ROUTES IN THE FILE "RedBus/buses.txt"
        buses = []
        # "from_locations" IS USED TO HOLD ALL THE "FROM LOCATIONS" IN THE FILE "RedBus/Index/from_location.txt"
        from_locations = []
        # "to_locations" IS USED TO HOLD ALL THE "TO LOCATIONS" IN THE FILE "RedBus/Index/to_location.txt"
        to_locations = []

        with open('RedBus/Index/from_location.txt', 'rt') as f:
            from_location_data = json.load(f)

            # FETCHING THE ROUTE-ID'S FORM THE SPECIFIED FROM LOCATION "from_location" AND
            # STORE INTO "from_route_ids"
            if from_location != "-":
                from_route_ids = from_location_data['from_location'][from_location]
            for location in from_location_data['from_location']:

                # ADDING RECORD TO "from_locations" LIST
                from_locations.append(location)

        with open('RedBus/Index/to_location.txt', 'rt') as f:
            to_location_data = json.load(f)

            # FETCHING THE ROUTE-ID'S FORM THE SPECIFIED FROM LOCATION "from_location" AND
            # STORE INTO "to_route_ids"
            if to_location != "-":
                to_route_ids = to_location_data['to_location'][to_location]
            for location in to_location_data['to_location']:

                # ADDING RECORD TO "to_locations" LIST
                to_locations.append(location)

        # IF "from_location" IS NOT SPECIFIED THEN "to_route_ids" IS THE FINAL LIST OF ROUTE-ID'S ( i.e, route_ids)
        if from_location == "-":
            route_ids = to_route_ids

        # IF "to_location" IS NOT SPECIFIED THEN "from_route_ids" IS THE FINAL LIST OF ROUTE-ID'S ( i.e, route_ids)
        elif to_location == "-":
            route_ids = from_route_ids

        # IF BOTH "to_location" AND "from_location" IS SPECIFIED THEN
        # FINAL LIST OF ROUTE-ID'S ( i.e, route_ids) IS THE COMMON ROUTE-ID FORM "from_route_ids" AND "to_route_ids"
        else:
            route_ids = list(filter(lambda r_id: r_id in from_route_ids, to_route_ids))

        # IF "route_ids" IS EMPTY THEN SET "is_search_success" TO "False"
        if len(route_ids) == 0:
            return render_template('home.html', buses=buses, from_locations=from_locations,
                                   to_locations=to_locations, is_search_success=False, is_search=True)

        # FETCHING ALL RELATED RECORDS OF THE PARTICULAR "route_id" FROM "RedBus/buses.txt" FILE
        with open('RedBus/buses.txt', 'r') as f:
            for line in f.readlines():
                bus_data = line.split("|")
                route_id = bus_data[0]
                if int(route_id) in route_ids:
                    bus = {
                        "id": bus_data[0],
                        "from": bus_data[1],
                        "to": bus_data[2],
                        "pickup_location": bus_data[3],
                        "boarding_time": bus_data[4],
                        "traveling_time": bus_data[5],
                        "no_of_seats": int(bus_data[6]),
                        "price": bus_data[7]
                    }

                    # ADDING RECORD TO "buses" LIST
                    buses.append(bus)

        # RETURNING THE REQUESTED PAGE( i.e, home.html)
        return render_template('home.html', buses=buses, from_locations=from_locations,
                               to_locations=to_locations, is_search_success=True, is_search=True)
    else:
        return redirect(url_for('user_login'))


# "user_logout" METHOD IS CALLED WHET THE USER LOGOUT'S OF HIS ACCOUNT
@app.route('/logout')
def user_logout():

    # LOGGING-OUT THE USER
    logout_user()

    # REDIRECTING THE USER TO THE LOGIN PAGE
    return redirect(url_for('user_login'))


# "admin_delete_user" METHOD IS CALLED WHET THE ADMIN CLICK'S ON "Remove" BUTTON
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


# "admin_users_panel" METHOD IS CALLED WHET THE ADMIN LOGIN'S IN SUCCESSFULLY AND
# EVERY-TIME USER REQUESTS FOR "admin-users-panel" PAGE
@app.route('/admin_users')
def admin_users_panel():
    if current_user.is_authenticated:

        # FETCHING ALL RECORDS( i.e, USERS) FOR "Users" TABLE
        users = Users.query.all()
        return render_template('admin_users_panel.html', users=users)
    else:
        return redirect(url_for('admin_login'))


# "admin_buses_panel" METHOD IS CALLED WHET THE ADMIN REQUEST FOR "admin-buses-panel" PAGE
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


# "admin_booking_panel" METHOD IS CALLED WHET THE ADMIN REQUEST FOR "admin-booking-panel" PAGE
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


# "admin_booking_item_details_panel" METHOD IS CALLED WHET THE ADMIN REQUESTS FOR "bookings-details" PAGE
@app.route('/admin_booking/<string:route_id>/details')
def admin_booking_item_details_panel(route_id):
    if current_user.is_authenticated and current_user.is_staff:

        with open('RedBus/bookings.txt', 'rt') as f:
            bookings_data = json.load(f)
            bookings = bookings_data["bookings"][route_id]

        return render_template('admin_booking_panel.html', bookings=bookings, show_specific_item_details=True)
    else:
        return redirect(url_for('admin_login'))


# "admin_add_route" METHOD IS CALLED WHET THE ADMIN CLICK'S ON "Add" BUTTON
@app.route('/admin_add_route', methods=['POST'])
def admin_add_route():
    # IF THE REQUEST METHOD IS "POST" THEN EXECUTE if BLOCK
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


# "admin_delete_route" METHOD IS CALLED WHET THE ADMIN CLICK'S ON "Delete" BUTTON
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


# "admin_login" METHOD IS CALLED WHET THE ADMIN REQUEST FOR "sign-in" PAGE
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    # IF THE REQUEST METHOD IS "POST" THEN EXECUTE if BLOCK
    if request.method == 'POST':

        # LOGOUT THE ADMIN FROM THEIR PREVIOUS SESSION
        logout_user()

        # FETCHING "email" AND "password" FROM THE LOGIN PAGE
        email = request.form['email']
        password = request.form['password']

        # AUTHENTICATING THE USER
        # "user" EQUALS "None" IF THE "email" DOES NOT EXIST
        user = Users.query.filter_by(email=email).first()

        if user:

            if user.password == password and user.is_staff:

                # REDIRECTING TO "/admin_users" PAGE AFTER SUCCESSFUL LOGIN
                login_user(user, True)
                return redirect(url_for('admin_users_panel'))
            else:
                # REDIRECTING BACK TO "login" IF THE "email" DOES NOT MATCH WITH IT'S THE CORRESPONDING "password" OR
                # USER IS NOT A STAFF
                flash('Invalid admin credentials', 'warning')
                return render_template('admin_login.html')

        else:
            # REDIRECTING BACK TO "login" IF THE "email" DOES NOT EXIST
            flash('No record found, check your credentials', 'warning')
            return render_template('admin_login.html')

    # IF THE REQUEST METHOD IS GET EXECUTE else BLOCK
    else:
        return render_template('admin_login.html')


# "admin_logout" METHOD IS CALLED WHET THE ADMIN LOGOUT'S OF HIS ACCOUNT
@app.route('/logout')
def admin_logout():

    # LOGGING-OUT THE ADMIN
    logout_user()

    # REDIRECTING THE ADMIN TO THE ADMIN-LOGIN PAGE
    return redirect(url_for('admin_login'))


if __name__ == "__main__":
    app.run(debug=True)
