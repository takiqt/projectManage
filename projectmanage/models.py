from projectmanage import db
from flask_login import LoginManager, UserMixin
from datetime import datetime
from sqlalchemy import or_, and_, func

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
    deleted  = db.Column(db.Boolean, nullable=False, default=False)
    delTime = db.Column(db.DateTime, nullable=True)
    projects = db.relationship('Project', backref='creator', lazy=True)    
    projectWorkers = db.relationship('Project', secondary=projectWorkers, backref=db.backref('workers', lazy='dynamic'))
    projectLeaders = db.relationship('Project', secondary=projectLeaders, backref=db.backref('leaders', lazy='dynamic'))
    projectJobsCreated = db.relationship('ProjectJob', foreign_keys='ProjectJob.creatorUserId', backref='creator', lazy=True)
    projectJobsWork    = db.relationship('ProjectJob', foreign_keys='ProjectJob.workerUserId', backref='worker', lazy=True)   
    activeJobId = db.Column(db.Integer, db.ForeignKey('project_job.id'), nullable=False, default=0)

    def __repr__(self):
        return f"Felhasználó: #{self.id} - {self.fullName}"
    
    @staticmethod
    def getProjectJobListCategories(userId):
        """ Felhasználó munkáit lekéri kategorizálva
        
        Arguments:
            userId {[int]} -- [Felhasználó azonosító]
        
        Returns:
            [dict] -- Munkák kategorizálva
        """
        user = User.query.get_or_404(userId)
        doneJobs = []
        activeJob = None
        pendingJobs = []
        for projectJob in user.projectJobsWork:
            if projectJob.isDone:
                doneJobs.append(projectJob)
            elif projectJob.id == user.activeJobId:
                activeJob = projectJob
            else:
                pendingJobs.append(projectJob)

        return {
            'activeJob' : activeJob,
            'doneJobs'  : doneJobs,
            'pendingJobs' : pendingJobs,
        }



class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    dateStart = db.Column(db.DateTime, nullable=False, default=datetime.now)
    dateEnd = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creatorUserId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    createTime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    projectJobs = db.relationship('ProjectJob', backref='project', lazy=True)
    isDone = db.Column(db.Boolean, nullable=False, default=False)
    doneTime = db.Column(db.DateTime, nullable=True)
    deleted  = db.Column(db.Boolean, nullable=False, default=False)
    delTime = db.Column(db.DateTime, nullable=True)
    def __repr__(self):
        return f"Project: #{self.id} - {self.name}" 

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
    deleted  = db.Column(db.Boolean, nullable=False, default=False)
    delTime = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'Projekt feladat: {self.name} (#{self.id}) - projekt: #{self.projectId}'

class ProjectJobWorktimeHistory(db.Model):   
    id = db.Column(db.Integer, primary_key=True)
    projectJobId = db.Column(db.Integer, db.ForeignKey('project_job.id'), nullable=False)
    workTime = db.Column(db.Float, nullable=False)
    comment  = db.Column(db.Text, nullable=False)
    createTime = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'Munkaidő - #{self.projectJobId} - Idő: {self.workTime} óra'

class UserMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fromUserId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    toUserId   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50), unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)
    sentTime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    readTime = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def getMessages(userId):
        """[Felhasználó összes üzeneteinek lekérése]
        
        Arguments:
            userId {[int]} -- [Felhasználó azonosító]
        
        Returns:
            [flask_sqlalchemy.BaseQuery] -- [Üzenetek]
        """
        messages = UserMessage.query.filter(
        or_(
            UserMessage.toUserId == userId, 
            UserMessage.fromUserId == userId)
        ).order_by(UserMessage.sentTime.desc())
        return messages
    
    @staticmethod
    def getSentMessages(userId):
        """[Felhasználó kimenő üzeneteinek lekérése]
        
        Arguments:
            userId {[int]} -- [Felhasználó azonosító]
        
        Returns:
            [flask_sqlalchemy.BaseQuery] -- [Üzenetek]
        """
        messages = UserMessage.query.filter(
            UserMessage.fromUserId == userId
        ).order_by(UserMessage.sentTime.desc())
        return messages
    
    @staticmethod
    def getRecievedMessages(userId):
        """[Felhasználó beérkező üzeneteinek lekérése]
        
        Arguments:
            userId {[int]} -- [Felhasználó azonosító]
                    
        Returns:
            [flask_sqlalchemy.BaseQuery] -- [Üzenetek]
        """
        messages = UserMessage.query.filter(
            UserMessage.toUserId == userId
        ).order_by(UserMessage.sentTime.desc())
        return messages

    @staticmethod
    def getUnreadCount(userId):
        """[Felhasználó beérkező olvasatlan üzenetszám]
        
        Arguments:
            userId {[int]} -- [Felhasználó azonosító]
                    
        Returns:
            [int] -- [Üzenetszám]
        """
        count = UserMessage.query.filter(
            and_(
                UserMessage.toUserId == userId,
                UserMessage.readTime == None
            )        
        ).count()
        return count

    @staticmethod
    def setRead(messageId):
        """[Üzenet olvasottra állíása]
        
        Arguments:
            messageId {[int]} -- [Üzenet azonosító]
        """
        message = UserMessage.query.get_or_404(messageId)
        message.readTime = datetime.now()
        db.session.commit()