from projectmanage import db
from flask_login import LoginManager, UserMixin
from datetime import datetime

projectWorkers = db.Table('projectWorkers',
    db.Column('userId', db.Integer, db.ForeignKey('user.id')),
    db.Column('projectId', db.Integer, db.ForeignKey('project.id')),
    db.PrimaryKeyConstraint('userId', 'projectId')
)

projectLeaders = db.Table('projectLeaders',
    db.Column('userId', db.Integer, db.ForeignKey('user.id')),
    db.Column('projectId', db.Integer, db.ForeignKey('project.id')),
    db.PrimaryKeyConstraint('userId', 'projectId')
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(30), unique=True, nullable=False)
    fullName = db.Column(db.String(150), nullable=False)
    email    = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    admin    = db.Column(db.Boolean, default=False)
    projects = db.relationship('Project', backref='creator', lazy=True)    
    projectWorkers = db.relationship('Project', secondary=projectWorkers, backref=db.backref('workers', lazy='dynamic'))
    projectLeaders = db.relationship('Project', secondary=projectLeaders, backref=db.backref('leaders', lazy='dynamic'))
    projectJobsCreated = db.relationship('ProjectJob', foreign_keys='ProjectJob.creatorUserId', backref='creator', lazy=True)
    projectJobsWork    = db.relationship('ProjectJob', foreign_keys='ProjectJob.workerUserId', backref='worker', lazy=True)   

    def __repr__(self):
        return f"'{self.fullName}'" 

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    dateStart = db.Column(db.DateTime, nullable=False, default=datetime.now)
    dateEnd = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creatorUserId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    createTime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    projectJobs = db.relationship('ProjectJob', backref='project', lazy=True)

    def __repr__(self):
        return f"Project('{self.id} - {self.name}')"


class ProjectJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    projectId = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(50), unique=False, nullable=False)
    description = db.Column(db.Text, nullable=False)
    dateStart = db.Column(db.DateTime, nullable=False, default=datetime.now)
    dateEnd = db.Column(db.DateTime, nullable=False, default=datetime.now)
    estimatedTime = db.Column(db.Float, nullable=False)
    workerUserId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parentJobId = db.Column(db.Integer, nullable=True, default=0)
    creatorUserId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    createTime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    isDone = db.Column(db.Boolean, nullable=False, default=False)
    doneTime = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'Projekt munka: {self.name} ({self.id}) - projekt: {self.projectId}'