from RedBusManager import Users, db
from hashlib import md5


def user_exist(email):
    user = Users.query.filter_by(email=email).first()
    if user:
        return True
    else:
        return False


if __name__ == "__main__":
    db.create_all()
    name = input("Enter name: ")
    email = input("Enter email: ")
    password = input("Enter password: ")

    if not user_exist(email):
        user = Users(name, email, password, True)
        db.session.add(user)
        db.session.commit()

        file = open("RedBus/users.txt", "at")
        file.write(name + "|" + email + "|" + md5(password.encode()).hexdigest() + "|" + str(True) + "\n")
        file.close()
    else:
        print("User already exist")
