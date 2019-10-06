from flask import render_template, url_for, request, session, redirect, flash, Response
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from sqlalchemy import or_, and_, text
from projectmanage import app, db, bcrypt, loginManager
from projectmanage.models import User, Project, ProjectJob, ProjectJobWorktimeHistory, UserMessage
from projectmanage.forms import *
from datetime import datetime
import pprint

# Felhasználó beléptetés segédfunkció
@loginManager.user_loader
def load_user(userId):    
    return User.query.get(int(userId))

# Valós url vizsgálat
def is_safe_url(urlTarget):
    refUrl  = urlparse(request.host_url)
    testUrl = urlparse(urljoin(request.host_url, urlTarget))
    return testUrl.scheme in ('http', 'https') and \
            refUrl.netloc == testUrl.netloc

# Admin felhasználói jog lekérése
def isAdmin(userId):
    user = User.query.filter_by(admin=1, id=userId).first()
    if user is not None:
        return True
    else:
        return False

# Error handler oldal
@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('login'))

# Template helper funkciók
@app.context_processor
def my_utility_processor():
    def getProjectName(projectId):
        project = Project.query.get_or_404(projectId)
        return project.name
    return dict(getProjectName=getProjectName)

# Kezdőlap / Dashboard
@app.route('/')
@app.route('/home')
@login_required
def index():
    doneJobs = []
    activeJob = None
    pendingJobs = []
    for projectJob in current_user.projectJobsWork:
        if projectJob.isDone:
            doneJobs.append(projectJob)
        elif projectJob.id == current_user.activeJobId:
            activeJob = projectJob
        else:
            pendingJobs.append(projectJob)
    
    data = {
        'activeLink' : 'home',
        'activeJob' : activeJob,
        'pendingJobs' : pendingJobs,
        'doneJobs' : doneJobs,
        'form' : AddProjectWorkTimeForm(),
    }

    return render_template('home.html', **data)

# Felhasználó felvitele
@app.route("/register", methods=['GET', 'POST'])
@login_required
def register():
    form = RegisterFrom()
    if form.validate_on_submit():
        oldUser = User.query.filter(or_(User.userName == form.userName.data, User.email == form.email.data)).first()
        if oldUser is not None:
            flash(f'Adott felhasználónév vagy email foglalt!', 'danger')
            data = {
                'form' : form,
                'activeLink' : 'users',  
            }              
            return render_template('register.html', **data)
        else:
            hashedPassword = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            userData = {
                'userName' : form.userName.data,
                'fullName' : form.fullName.data,
                'password' : hashedPassword,
                'email'    : form.email.data
            }
            user = User(**userData)
            db.session.add(user)
            db.session.commit()
            flash(f'Felhasználó regisztrálva {form.userName.data}', 'success')        
            return redirect(url_for('users'))
    else:
        if current_user.admin != True:
            return render_template('home.html')
        data = {
            'form' : form,    
            'activeLink' : 'users',
        }
        return render_template('register.html', **data)

# Bejelentkezés
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        userName = form.userName.data
        password = form.password.data
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(userName=userName).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)

            if 'next' in session:
                next = session['next']
                if is_safe_url(next):
                    return redirect(next)

            return redirect(url_for('index'))        
        
        flash(f'Hibás felhasználó név vagy jelszó!', 'success')
        return redirect(url_for('login'))
    else:
        if current_user.is_authenticated == True:
            return redirect(url_for('index'))
        data = {
            'form' : form,             
        }
        return render_template('login.html', **data)

# Kijelentkezés
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Felhasználó lista oldal
@app.route("/users")
@login_required
def users():
    users = User.query.order_by(User.fullName).all()
    data = {
        'users' : users,
        'activeLink' : 'users',
    }
    return render_template('User/users.html', **data)

# Felhasználó adatlap megtekintése
@app.route('/userData/<int:userId>')
@login_required
def userData(userId):
    app.logger.info(userId)
    return redirect(url_for('users'))

# Projekt lista oldal
@app.route("/projects")
@login_required
def projects():
    projects = Project.query.order_by(Project.name).all()
    data = {
        'projects' : projects,
        'activeLink' : 'projects',
    }
    return render_template('Project/projects.html', **data)

# Projekt hozzáadása oldal
@app.route("/addProject", methods=['GET', 'POST'])
@login_required
def addProject():
    form = AddProjectForm()
    if form.validate_on_submit():
        oldProject = Project.query.filter_by(name=form.name.data).first()
        if oldProject is not None:
            flash(f'{form.name.data} - Adott néven már van rögzített projekt!', 'danger')
            data = {
                'form' : form,
                'activeLink' : 'addProject',                
            }
            return render_template('Project/addProject.html', **data)
        else:
            projectData = {
                'name' : form.name.data,
                'description' : form.description.data,
                'dateStart' : form.dateStart.data,
                'dateEnd' : form.dateEnd.data,
                'creatorUserId' : current_user.id,
            }
            project = Project(**projectData)              
            db.session.add(project)
            project.leaders.append(current_user)
            db.session.commit()
            flash(f'Sikeres projekt felvitel', 'success')
            return redirect(url_for('projects'))
    else:
        data = {
            'form' : form,
            'activeLink' : 'addProject',
        }
        return render_template('Project/addProject.html', **data)

# Projekt adatai aloldal
@app.route("/projectData/<int:projectId>")
@login_required
def projectData(projectId):
    project = Project.query.get_or_404(projectId)
    return render_template('Project/projectData.html', project=project, menuTitle='adatlap', activeLink='projects')
    
# Vezető lista aloldal
@app.route("/projectLeaders/<int:projectId>", methods=['POST', 'GET'])
@login_required
def projectLeaders(projectId):
    project = Project.query.get_or_404(projectId)
    form = AddProjectLeader()
    form.users.query = User.query.order_by(User.fullName).all()

    if form.validate_on_submit():
        userId = form.users.data.id
        sql = text('select COUNT(*) AS count from projectleaders WHERE userId = :userId AND projectId = :projectId')
        result = db.engine.execute(sql, { 'userId' : userId, 'projectId' : project.id })   
        r = result.fetchone()    
        if r['count'] == 0:
            user = User.query.filter_by(id=userId).first()
            project.leaders.append(user)
            db.session.commit()    
            flash(f'Vezető rögzítve!', 'success')
        else:
            flash(f'Vezető már rögzítve van!', 'danger')   
        
    return render_template('Project/projectUsers.html', project=project, mode='leaders', menuTitle='vezetők', form=form, activeLink='projects')

# Munkatárs lista aloldal
@app.route("/projectWorkers/<int:projectId>", methods=['POST', 'GET'])
@login_required
def projectWorkers(projectId):
    project = Project.query.get_or_404(projectId)
    form = AddProjectWorker()
    form.users.query = User.query.order_by(User.fullName).all()
    
    if form.validate_on_submit():
        userId = form.users.data.id        
        sql = text('select COUNT(*) AS count from projectworkers WHERE userId = :userId AND projectId = :projectId')
        result = db.engine.execute(sql, { 'userId' : userId, 'projectId' : project.id })
        r = result.fetchone()
        if r['count'] == 0:
            user = User.query.filter_by(id=userId).first()      
            project.workers.append(user)
            db.session.commit() 
            flash(f'Munkatárs rögzítve!', 'success')
        else:
            flash(f'Munkatárs már rögzítve van!', 'danger')        

    return render_template('Project/projectUsers.html', project=project, mode='workers',  menuTitle='munkatársak', form=form, activeLink='projects')

# Vezető törlése a projektből
@app.route('/projectLeaders/<int:projectId>/delete', methods=['POST'])
@login_required
def deleteProjectLeader(projectId):
    project = Project.query.get_or_404(projectId)
    if current_user == project.creator:
        userId = request.form.get('delUserId')
        user = User.query.filter_by(id=userId).first()
        if user is not None:
            project.leaders.remove(user)
            db.session.commit() 
            flash(f'Vezető törölve!', 'success')
        
    return redirect(url_for('projectLeaders', projectId=project.id))

# Munkatárs törlése a projektből
@app.route('/projectWorkers/<int:projectId>/delete', methods=['POST'])
@login_required
def deleteProjectWorker(projectId):
    project = Project.query.get_or_404(projectId)
    if current_user == project.creator:
        userId = request.form.get('delUserId')
        user = User.query.filter_by(id=userId).first()
        if user is not None:
            project.workers.remove(user)
            db.session.commit() 
            flash(f'Munkatárs törölve!', 'success')
        
    return redirect(url_for('projectWorkers', projectId=project.id))

# Projekt munka felvitele
@app.route('/addProjectJob/<int:projectId>', methods=['POST', 'GET'])
@login_required
def addProjectJob(projectId):
    form = AddProjectJobForm()
    form.users.query = User.query.order_by(User.fullName).all()
    app.logger.info(form.dateStart.data)
    if form.validate_on_submit():
        projectJobData = {
            'name' : form.name.data,
            'description' : form.description.data,
            'estimatedTime' : form.estimatedTime.data,
            'dateStart' : form.dateStart.data,
            'dateEnd' : form.dateEnd.data,
            'creatorUserId' : current_user.id,
            'workerUserId' : form.users.data.id,
            'projectId' : projectId,
        }
        projectJob = ProjectJob(**projectJobData)
        db.session.add(projectJob)
        db.session.commit()
        flash(f'Sikeres munka felvitel!', 'success')
        return redirect(url_for('projectData', projectId=projectId))
    else:
        data = {
            'form' : form,
            'activeLink' : 'projects',
            'projectId' : projectId,
        }
        return render_template('ProjectJob/addProjectJob.html', **data)

# Projekt munka adatlap
@app.route('/projectJobData/<int:projectJobId>')
@login_required
def projectJobData(projectJobId):
    projectJob = ProjectJob.query.get_or_404(projectJobId)
    project = Project.query.get_or_404(projectJob.projectId)
    return render_template('ProjectJob/projectJobData.html', projectJob=projectJob, project=project, activeLink='projects')

# Projekt munka levétele
@app.route('/startJob/<int:projectJobId>')
@login_required
def startJob(projectJobId):    
    current_user.activeJobId = projectJobId
    db.session.commit()
    return redirect(url_for('index'))

# Projekt munka állapot változatás
@app.route('/manageJob/<int:projectJobId>', methods=['POST'])
@login_required
def manageJob(projectJobId):
    comment = request.form.get('comment')
    workTimeString = request.form.get('workTime')
    workTime = float(workTimeString.replace(',', '.'))
    done = request.form.get('done')
    pending = request.form.get('pending')

    if comment.strip() != '' and workTime > 0:
        workTimeHistoryData = {
            'comment' : comment,
            'workTime' : workTime,
            'projectJobId' : projectJobId,
        }
        projectJobWorktimeHistory = ProjectJobWorktimeHistory(**workTimeHistoryData)
        db.session.add(projectJobWorktimeHistory)
        current_user.activeJobId = 0
        if done is not None:
            projectJob = ProjectJob.query.get_or_404(projectJobId)
            projectJob.isDone = True
            projectJob.doneTime = datetime.now()
            flash(f'Feladat elkészült!', 'success')
        elif pending is not None:
            flash(f'Feladat várakozó állapotra állítva!', 'success')
        
        db.session.commit()
    else: 
        flash(f'Hibás munkaidő adatok!', 'danger')

    return redirect(url_for('index'))


# Üzenet küldés
@app.route('/sendMessage/<int:targetUserId>', methods=['POST', 'GET'])
@login_required
def sendMessage(targetUserId):    
    form = SendMessageForm()
    form.toUserId.query = User.query.filter(User.id!=current_user.id).order_by(User.fullName).all()    
    if form.validate_on_submit() and form.toUserId.data.id != current_user.id:
        app.logger.info(form.text.data)
        messageData = {
            'text' : form.text.data,
            'subject' : form.subject.data,
            'fromUserId' : current_user.id,
            'toUserId' : form.toUserId.data.id,
        }
        message = UserMessage(**messageData)
        db.session.add(message)
        db.session.commit()
        flash(f'Üzenet elküldve!', 'success')
        return redirect(url_for('users'))
    else:
        if not form.is_submitted():
            form.toUserId.default = load_user(targetUserId)
            form.process()
        data = {
            'form' : form,
            'activeLink' : 'messages',
        }
        return render_template('User/sendMessage.html', **data)


@app.route('/loadMessage/<int:messageId>')
@login_required
def loadMessage(messageId):
    message = UserMessage.query.get_or_404(messageId)
    app.logger.info(message.text)
    # return redirect(url_for('users'))
    return render_template('User/messages.html')

@app.route('/messages')
@login_required
def messages():
    messages = UserMessage.query.filter(
        or_(
            UserMessage.toUserId == current_user.id, 
            UserMessage.fromUserId == current_user.id)
        ).order_by(UserMessage.sentTime)
    for message in messages:        
        message.text = message.text.replace('\n', '<br />')

    return render_template('User/messages.html', messages=messages)
    
##############################
## Test chartok
@app.route('/test1')
@login_required
def test1():
    return render_template('test1.html')