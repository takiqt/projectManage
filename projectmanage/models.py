from projectmanage import db, app
from flask_login import LoginManager, UserMixin, current_user
from datetime import datetime
from sqlalchemy import or_, and_, func, text

# Projekt munkatársak kapcsoló tábla
projectWorkers = db.Table('projectWorkers',
    db.Column('userId', db.Integer, db.ForeignKey('user.id')),
    db.Column('projectId', db.Integer, db.ForeignKey('project.id')),
    db.PrimaryKeyConstraint('userId', 'projectId')
)
# Projekt vezetők kapcsoló tábla
projectLeaders = db.Table('projectLeaders',
    db.Column('userId', db.Integer, db.ForeignKey('user.id')),
    db.Column('projectId', db.Integer, db.ForeignKey('project.id')),
    db.PrimaryKeyConstraint('userId', 'projectId')
)

class User(UserMixin, db.Model):
    """ Felhasználó Model 
    """
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
    def getUserVisibleProjects(userId):
        """ Felhasználó által látható projektek lekérése
        
        Arguments:
            userId {int} -- [Felhasználó azonosító]
        
        Returns:
            dict -- Projektek
        """
        projects = []
        # Rögzített projektek
        sql = text('select `id` from `project` WHERE `creatorUserId` = :userId')
        result = db.engine.execute(sql, { 'userId' : userId })
        res = result.fetchall()        
        for resProject in res:            
            project = Project.query.get(resProject['id'])
            projects.append(project)                    
        # Vezető projektben
        sql = text('select `projectId` from `projectLeaders` WHERE `userId` = :userId')
        result = db.engine.execute(sql, { 'userId' : userId })        
        res = result.fetchall()
        for resProject in res:            
            project = Project.query.get(resProject['projectId'])
            projects.append(project)  
        # Munkatárs projektben
        sql = text('select `projectId` from `projectWorkers` WHERE `userId` = :userId')
        result = db.engine.execute(sql, { 'userId' : userId })        
        res = result.fetchall()
        for resProject in res:            
            project = Project.query.get(resProject['projectId'])
            projects.append(project) 
            
        return sorted(list({v.id:v for v in projects}.values()), key=lambda k: k.name)

    @staticmethod
    def getProjectJobListCategories(userId):
        """ Felhasználó munkáit lekéri kategorizálva
        
        Arguments:
            userId {int} -- [Felhasználó azonosító]
        
        Returns:
            list -- Munkák kategorizálva
        """
        user = User.query.get_or_404(userId)
        doneJobs = []
        activeJob = None
        pendingJobs = []
        for projectJob in user.projectJobsWork:
            project = Project.query.get(projectJob.projectId)
            if projectJob.seen == False and Project.isActive(project):
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

    @staticmethod
    def isPassivable(self, user):
        """ User passzíválását ellenőrzi
        
        Arguments:
            user {User} -- Passziváló User objektum
        
        Returns:
            bool
        """
        if user.admin != True:
            return False
        
        if self.activeJobId > 0:
            return False
        
        jobsAll = User.getProjectJobListCategories(self.id)
        if len(jobsAll['pendingJobs']) > 0:
            return False
            
        return True

    @staticmethod
    def getJobWorkerRiportData(self):
        """ User feladat végző riport
        
        Returns:
            list
        """
        riport = {}
        sumEstimatedTime = sumBookedTime = jobCount = 0
        for projectJob in self.projectJobsWork:
            sumEstimatedTime += projectJob.estimatedTime            
            sumBookedTime += ProjectJob.getJobWorktimesByUser(projectJob.id, self.id)
            jobCount += 1

        if sumEstimatedTime != 0:
            percent = sumBookedTime / sumEstimatedTime * 100
        else:
            percent = 0

        riport['estimated'] = round(sumEstimatedTime, 2)
        riport['booked']    = round(sumBookedTime, 2) 
        riport['percent']   = round(percent, 2)       
        riport['jobCount']  = jobCount

        return riport

    @staticmethod
    def getJobCreatorRiportData(self):
        """ User feladat kiíró riport
        
        Returns:
            list
        """
        riport = {}
        sumEstimatedTime = sumBookedTime = jobCount = 0
        for projectJob in self.projectJobsCreated:
            # Nem maganak írta ki
            if not (projectJob.workerUserId == self.id and projectJob.creatorUserId):                
                sumEstimatedTime += projectJob.estimatedTime                            
                sumBookedTime += ProjectJob.getJobWorktimesAll(projectJob.id)
                jobCount += 1

        if sumEstimatedTime != 0:
            percent = sumBookedTime / sumEstimatedTime * 100
        else:
            percent = 0

        riport['estimated'] = round(sumEstimatedTime, 2)
        riport['booked']    = round(sumBookedTime, 2)
        riport['percent']   = round(percent, 2)   
        riport['jobCount']  = jobCount

        return riport

    @property
    def serialize(self):
        """ Objektum serializálása
        """
        return {
            'id'         : self.id,
            'name'       : self.fullName,
        }

class UserMessage(db.Model):
    """ Üzenet Model 
    """
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
            userId {int} -- [Felhasználó azonosító]
        
        Returns:
            flask_sqlalchemy.BaseQuery -- Üzenetek
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
            userId {int} -- [Felhasználó azonosító]
        
        Returns:
            flask_sqlalchemy.BaseQuery -- Üzenetek
        """
        messages = UserMessage.query.filter(
            UserMessage.fromUserId == userId
        ).order_by(UserMessage.sentTime.desc())
        return messages
    
    @staticmethod
    def getRecievedMessages(userId):
        """[Felhasználó beérkező üzeneteinek lekérése]
        
        Arguments:
            userId {int} -- [Felhasználó azonosító]
                    
        Returns:
            flask_sqlalchemy.BaseQuery -- Üzenetek
        """
        messages = UserMessage.query.filter(
            UserMessage.toUserId == userId
        ).order_by(UserMessage.sentTime.desc())
        return messages

    @staticmethod
    def getUnreadCount(userId):
        """[Felhasználó beérkező olvasatlan üzenetszám]
        
        Arguments:
            userId {int} -- [Felhasználó azonosító]
                    
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
    def isVisibleByUser(self, userId):
        """ Felhasználó láthatja-e az üzenetet
        
        Arguments:
            userId {int} -- Felhasználó azonosító
                    
        Returns:
            bool
        """
        if userId == self.toUserId or userId == self.fromUserId:
            return True
        return False

    @staticmethod
    def setRead(messageId):
        """[Üzenet olvasottra állíása]
        
        Arguments:
            messageId {int} -- [Üzenet azonosító]
        """
        message = UserMessage.query.get_or_404(messageId)
        message.readTime = datetime.now()
        db.session.commit()

class Project(db.Model):
    """ Projekt Model 
    """
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
        return f"Projekt: #{self.id} - {self.name}" 

    @staticmethod
    def isClosable(self, userId):
        """ Projekt lezárható-e
        
        Arguments:
            userId {int} -- Felhasználó azonosító
        
        Returns:
            bool
        """
        if self.creatorUserId != userId:
            return False
        for job in self.projectJobs:
            if job.deleted == False and job.isDone == False:
                return False
        return True

    @staticmethod
    def isArchivable(self, userId):
        """ Projekt archiválható-e
        
        Arguments:
            userId {int} -- Felhasználó azonosító
        
        Returns:
            bool
        """        
        if self.creatorUserId != userId:
            return False
        sql = text('select COUNT(*) AS `count` from `project_job` INNER JOIN `user` ON `user`.`activeJobId` = `project_job`.`id` WHERE `projectId` = :projectId')
        result = db.engine.execute(sql, { 'projectId' : self.id })
        res = result.fetchone()        
        if res['count'] > 0:
            return False
        return True

    @staticmethod 
    def isModifiable(self, userId):
        """ Projekt módosítható-e
        
        Arguments:
            userId {int} -- Felhasználó azonosító
        
        Returns:
            bool
        """   
        if self.creatorUserId != userId:
            return False
        if self.isDone == True or self.deleted == True:
            return False

        return True

    @staticmethod
    def isActive(self):
        """ Projekt folyamatban van-e        
        
        Returns:
            bool
        """  
        if self.isDone == True or self.deleted == True:
            return False

        return True

    @staticmethod
    def isVisible(self, userId):
        """ Projekt látható-e az adott usernek

        Arguments:
            userId {int} -- Felhasználó azonosító
        
        Returns:
            bool
        """
        if self.creatorUserId == userId:     
            return True

    @staticmethod
    def getProjectUsers(self):
        """ Projekt összes felhasználóját adja vissza, vezetők + munkatársak

        Returns:
            list - Felhasználók
        """
        usersAll = []
        leaders  = [self.creatorUserId]
        for user in self.workers:
            if not user.deleted:
                usersAll.append({'id': user.id, 'name': user.fullName})
        for user in self.leaders:
            if not user.deleted:
                usersAll.append({'id': user.id, 'name': user.fullName})  
                leaders.append(user.id)  

        return list({u['id']:u for u in usersAll}.values())

    @staticmethod
    def getRiportData(self):
        """ Projekt riport adatok összegyüjtése
         
        Returns:
            list
        """
        riport = {}
        sumEstimatedTime = sumBookedTime = 0
        for projectJob in self.projectJobs:
            sumEstimatedTime += projectJob.estimatedTime            
            if not ProjectJob.hasSubJob(projectJob):                
                sumBookedTime += ProjectJob.getJobWorktimesAll(projectJob.id)

        if sumEstimatedTime != 0:
            percent = sumBookedTime / sumEstimatedTime * 100
        else:
            percent = 0

        riport['estimated'] = round(sumEstimatedTime, 2)
        riport['booked']    = round(sumBookedTime, 2)  
        riport['percent']   = round(percent, 2)  

        return riport

class ProjectJob(db.Model):
    """ Projekt feladat Model 
    """
    id = db.Column(db.Integer, primary_key=True)
    projectId = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(50), unique=False, nullable=False)
    description = db.Column(db.Text, nullable=False)
    dateStart = db.Column(db.DateTime, nullable=False, default=datetime.now)
    dateEnd = db.Column(db.DateTime, nullable=False, default=datetime.now)
    duration = db.Column(db.Integer, nullable=False)
    estimatedTime = db.Column(db.Float, nullable=False)
    workerUserId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parentJobId = db.Column(db.Integer, nullable=True, default=0)
    creatorUserId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    createTime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    isDone = db.Column(db.Boolean, nullable=False, default=False)
    doneTime = db.Column(db.DateTime, nullable=True)
    seen = db.Column(db.Boolean, nullable=False, default=False)
    seenTime = db.Column(db.DateTime, nullable=True)
    deleted  = db.Column(db.Boolean, nullable=False, default=False)
    delTime = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'{self.name} (#{self.id})'
    
    @staticmethod
    def isActive(self):
        """ Projekt feladat folyamatban van-e        
        
        Returns:
            bool
        """
        if self.deleted == True or self.isDone == True:
            return False
        return True

    @staticmethod
    def isModifiable(self, userId):
        """ Projekt feladat módosítható-e
        
        Arguments:
            userId {int} -- Felhasználó azonosító
        
        Returns:
            bool
        """        
        project = Project.query.get_or_404(self.projectId)
        if self.creatorUserId != userId or not ProjectJob.isActive(self) or not Project.isActive(project):
            return False
        else:
            return True

    @staticmethod
    def setDeleted(projectJobId):
        """Feladat töröltre állítása
        
        Arguments:
            projectJobId {int} -- Feladat azonosító
        """
        projectJob = ProjectJob.query.get_or_404(projectJobId)
        projectJob.deleted = True
        projectJob.delTime = datetime.now()

        # Van alfeladata, azokat is törölni
        if ProjectJob.hasSubJob(projectJob):
            jobs = ProjectJob.getSubJobs(projectJob)
            for job in jobs:
                ProjectJob.setDeleted(job)

        db.session.commit()

    @staticmethod
    def setDone(projectJobId):
        """Feladat elkszültre állítása
        
        Arguments:
            projectJobId {int} -- Feladat azonosító
        """
        projectJob = ProjectJob.query.get_or_404(projectJobId)
        projectJob.isDone = True
        projectJob.doneTime = datetime.now()
        db.session.commit()

        # Ha alfeladat , megnézzük h a szülő minden alfeladata elkészült-e
        # Ilyenkor lehet a szülőt elkészültre állítani
        if ProjectJob.isSubJob(projectJob):
            parentJob = ProjectJob.query.get_or_404(projectJob.parentJobId)
            # Van alfeladata
            if ProjectJob.hasSubJob(parentJob):
                # Alfeladatok
                completed = True
                jobs = ProjectJob.getSubJobs(parentJob)
                for job in jobs:
                    if job.isDone == False:
                        completed = False
            
            if completed == True: # Ha minden alfeladat kész, kész a szülő is 
                ProjectJob.setDone(parentJob.id)

    @staticmethod
    def getJobWorktimes(projectJobId):
        """ Feladathoz tartozó könyvelt munkaidők lekérése
        
        Arguments:
            projectJobId {int} -- Feladat azonosító

        Returns:
            flask_sqlalchemy.BaseQuery -- Munkaidők
        """
        worktimes = ProjectJobWorktimeHistory.query.filter(
            ProjectJobWorktimeHistory.projectJobId == projectJobId
        ).order_by(ProjectJobWorktimeHistory.createTime.desc())
        return worktimes

    @staticmethod
    def getJobWorktimesAll(projectJobId):
        """ Feladathoz tartozó szumma könyvelt munkaidő lekérése
        
        Arguments:
            projectJobId {int} -- Feladat azonosító

        Returns:
            float
        """
        projectJob = ProjectJob.query.get(projectJobId)
        if ProjectJob.hasSubJob(projectJob):
            sumJobsWorkHour = 0
            subJobs = ProjectJob.getSubJobs(projectJob)
            for subJob in subJobs:
                sumJobsWorkHour += ProjectJob.getJobWorktimesAll(subJob.id)
            return sumJobsWorkHour
        else:
            sql = text('select SUM(`workTime`) AS `sum` from `project_job_worktime_history` WHERE `projectJobId` = :projectJobId')
            result = db.engine.execute(sql, { 'projectJobId' : projectJobId })
            res = result.fetchone()                
            return res['sum'] if res['sum'] is not None else 0

    @staticmethod
    def getJobWorktimesByUser(projectJobId, userId):
        """ Feladathoz tartozó szumma könyvelt munkaidő lekérése adott felhasználóhoz
        
        Arguments:
            projectJobId {int} -- Feladat azonosító
            userId {int} -- Felhasználó azonosító

        Returns:
            float
        """
        sql = text('select SUM(`workTime`) AS `sum` from `project_job_worktime_history` WHERE `projectJobId` = :projectJobId and `createUserId` = :userId')
        result = db.engine.execute(sql, { 'projectJobId' : projectJobId, 'userId' : userId })
        res = result.fetchone()                
        return res['sum'] if res['sum'] is not None else 0

    @staticmethod
    def canCreateSubJob(self, userId):
        """ Feladathoz lehet-e rögzíteni alfeladatot
        
        Arguments:
            self {Object} -- Feladat
            userId {int}  -- Felhasználó azonosító

        Returns:
            bool
        """ 

        # Nem aktív feladat
        sql = text('select COUNT(*) AS `count` from `project_job` INNER JOIN `user` ON `user`.`activeJobId` = `project_job`.`id` WHERE `project_job`.`id` = :id')
        result = db.engine.execute(sql, { 'id' : self.id })
        res = result.fetchone()        
        if res['count'] > 0:
            return False

        # Van munkaidő rögzítve
        if self.getJobWorktimesAll(self.id) != 0:
            return False

        # Már egy alfeladat, tovább nem bontható
        if self.parentJobId > 0:
            return False

        # Mástól kaptam, én végzem el 
        if self.workerUserId == self.creatorUserId or self.workerUserId != userId:
            return False

        # Nem törölt, nem elkészült
        if not ProjectJob.isActive(self):
            return False

        # Projektje nem törölt, nem elkészült
        project = Project.query.get_or_404(self.projectId)
        if not Project.isActive(project):
            return False

        return True      

    @staticmethod
    def isSubJob(self):
        """ Feladat alfeladat-e
        
        Returns:
            bool
        """
        return True if self.parentJobId > 0 else False

    @staticmethod 
    def hasSubJob(self):
        """ Feladathoz tartozik-e alfeladat ami nem archívált (törölt)
        
        Returns:
            bool
        """
        sql = text('select COUNT(*) AS `count` from `project_job` WHERE `deleted` = 0 AND `project_job`.`parentJobId` = :id')
        result = db.engine.execute(sql, { 'id' : self.id })
        res = result.fetchone()                
        if res['count'] > 0:
            return True

        return False

    @staticmethod
    def getSubJobs(self):
        """ Alfeladatok lekérdezése

        Returns:
            flask_sqlalchemy.BaseQuery -- Feladatok
        """
        jobs = ProjectJob.query.filter(ProjectJob.parentJobId == self.id).all()

        return jobs

    @property
    def serialize(self):
        """ Objektum serializálása
        """
        project = Project.query.get(self.projectId)
        leaders = [project.creatorUserId]
        for user in project.leaders:         
            leaders.append(user.id)
        return {
            'id'         : self.id,
            'text'       : self.name,
            'desc'       : self.description,
            'start_date' : self.dateStart.strftime("%d-%m-%Y %H:%M'"),            
            'end_date'   : self.dateEnd.strftime("%d-%m-%Y %H:%M'"),            
            'duration'   : self.duration,            
            'userId'     : self.workerUserId,  
            'projectId'  : self.projectId,
            'color'      : 'green' if self.isDone == True else 'd',
            'open'       : True,
            'readonly'   : True if not ProjectJob.isModifiable(self, current_user.id) else False,
        }

class ProjectJobLink(db.Model):
    """ Projekt feladat kapcsolat Model 
    """
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Integer, db.ForeignKey('project_job.id'), nullable=False)
    target = db.Column(db.Integer, db.ForeignKey('project_job.id'), nullable=False)
    type   = db.Column(db.String(1), unique=False, nullable=False)

    @property
    def serialize(self):
        """ Objektum serializálása
        """
        return {
            'id' : self.id,
            'source' : self.source,
            'target' : self.target,
            'type' : self.type,
        }

class ProjectJobWorktimeHistory(db.Model):
    """ Projekt feladat munkaidő Model 
    """   
    id = db.Column(db.Integer, primary_key=True)
    projectJobId = db.Column(db.Integer, db.ForeignKey('project_job.id'), nullable=False)
    workTime = db.Column(db.Float, nullable=False)
    comment  = db.Column(db.Text, nullable=False)
    createTime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    createUserId =  db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)