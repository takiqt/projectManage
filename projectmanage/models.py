from projectmanage import db
from flask_login import LoginManager, UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(30), unique=True, nullable=False)
    fullName = db.Column(db.String(150), nullable=False)
    email    = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    admin    = db.Column(db.Boolean, default=False)    

    def __repr__(self):
        return f"User('{self.email}', '{self.userName}') - admin : '{self.admin}'" 

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"Project('{self.id} - {self.name}')"
