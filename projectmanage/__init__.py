from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt
from flask_script import Command, Manager, Option
from flask_migrate import Migrate, MigrateCommand
from sqlalchemy import or_, and_
from flask_datepicker import datepicker

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
datepicker(app)
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.session_protection = "strong"
loginManager.login_view = 'login'
loginManager.login_message = 'Folytatáshoz bejelentkezés szükséges!'
loginManager.needs_refresh_message = 'Folytatáshoz bejelentkezés megerősítése szükséges!'
loginManager.needs_refresh_message_category = 'info'

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

from .models import User
 
class CreateAdmin(Command):
    """ Admin felhasználó létrehozás parancssorból

        python run.py createAdmin --userName="adminTest" --password="123456" --fullName="AdminTeszt" --email="admin@admin.hu"
    """
    option_list = (
        Option('--userName', '-u', dest='userName', required=True, help='Felhasználó név'),
        Option('--fullName', '-f', dest='fullName', required=True, help='Teljes név'),
        Option('--email', '-e', dest='email', required=True, help='E-mail cím'),
        Option('--password', '-p', dest='password', required=True, help='Jelszó'),
    )

    def run(self, userName, fullName, email, password):
        user = User.query.filter(or_(User.userName == userName, User.email == email)).first()
        if len(password) < 6 or len(password) > 30:
            print('Jelszó hosszának 6 és 30 karakter között kell lenni!')
        if user is not None:
            print('Adott felhasználónév vagy email foglalt!')
        else:
            newUserData = {
                'userName' : userName,
                'fullName' : fullName,
                'email' :  email,
                'password' : bcrypt.generate_password_hash(password).decode('utf-8'),
                'admin' : True
            }
            newUser = User(**newUserData)
            db.session.add(newUser)
            db.session.commit()
            print(f'Admin felhasználó hozzáadva {userName} - {email}')

manager.add_command('createAdmin', CreateAdmin())

from projectmanage import routes