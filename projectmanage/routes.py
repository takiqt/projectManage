from flask import render_template, url_for, request, session, redirect, flash, Response, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, and_, text
from projectmanage import app, db, bcrypt, loginManager
from projectmanage.models import User, Project, ProjectJob, ProjectJobLink, ProjectJobWorktimeHistory, UserMessage
from projectmanage.forms import *
from projectmanage.functions import *
from projectmanage.api import *
from datetime import datetime
import pprint

# ----
# Projektre / Projekt feladatra vonatkozó URL-k
# ----
@app.route('/')
@app.route('/home')
@login_required
def index():
    """ Dashboard megjelenítése
    
    Returns:
        [response]
    """
    jobs = User.getProjectJobListCategories(current_user.id)
    data = {
        'activeLink' : 'home',
        'activeJob' : jobs['activeJob'],
        'pendingJobs' : jobs['pendingJobs'],
        'doneJobs' : jobs['doneJobs'],
        'form' : AddProjectWorkTimeForm(),
    }
    return render_template('home.html', **data)

@app.route('/gantt')
@login_required
def userGantt():
    """ Felhasználó Gantt megjelenítése
    
    Returns:
        [response]
    """
    data = {
        'activeLink' : 'home',        
        'mode'       : 'user',
        'users'      : [{'id': current_user.id, 'name': current_user.fullName }],
    }
    return render_template('gantt.html', **data)

@app.route("/projects")
@login_required
def projects():
    """ Projekt lista
    
    Returns:
        [response]
    """
    projects = Project.query.order_by(Project.name).all()
    data = {
        'activeLink' : 'projects',
        'projects' : projects,
    }
    return render_template('Project/projects.html', **data)

@app.route("/addProject", methods=['GET', 'POST'])
@login_required
def addProject():
    """ Projekt hozzáadása oldal
    
    Returns:
        [response]
    """
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

@app.route("/projectData/<int:projectId>")
@login_required
def projectData(projectId):
    """ Projekt adatai aloldal
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
    project = Project.query.get_or_404(projectId)
    return render_template('Project/projectData.html', project=project, menuTitle='adatlap', activeLink='projects')

@app.route("/projectGantt/<int:projectId>")
@login_required
def projectGantt(projectId):
    """ Projekt Gantt oldal
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
    project = Project.query.get_or_404(projectId) 
    usersAll = []
    leaders  = [project.creatorUserId]
    for user in project.workers:
        usersAll.append({'id': user.id, 'name': user.fullName})
    for user in project.leaders:
        usersAll.append({'id': user.id, 'name': user.fullName})  
        leaders.append(user.id)  
    users = list({u['id']:u for u in usersAll}.values())
    
    data = {
        'activeLink' : 'projects',
        'mode'       : 'project',
        'project'    : project,
        'users'      : users,
        'canModify'  : True if current_user.id in leaders else False,
    }
    return render_template('gantt.html', **data)

@app.route("/projectLeaders/<int:projectId>", methods=['POST', 'GET'])
@login_required
def projectLeaders(projectId):
    """ Vezető lista aloldal
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
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

@app.route("/projectWorkers/<int:projectId>", methods=['POST', 'GET'])
@login_required
def projectWorkers(projectId):
    """ Munkatárs lista aloldal
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
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

@app.route('/projectLeaders/<int:projectId>/delete', methods=['POST'])
@login_required
def deleteProjectLeader(projectId):
    """ Vezető törlése a projektből
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
    project = Project.query.get_or_404(projectId)
    if current_user == project.creator:
        userId = request.form.get('delUserId')
        user = User.query.filter_by(id=userId).first()
        if user is not None:
            project.leaders.remove(user)
            db.session.commit() 
            flash(f'Vezető törölve!', 'success')
        
    return redirect(url_for('projectLeaders', projectId=project.id))

@app.route('/projectWorkers/<int:projectId>/delete', methods=['POST'])
@login_required
def deleteProjectWorker(projectId):
    """ Munkatárs törlése a projektből
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
    project = Project.query.get_or_404(projectId)
    if current_user == project.creator:
        userId = request.form.get('delUserId')
        user = User.query.filter_by(id=userId).first()
        if user is not None:
            project.workers.remove(user)
            db.session.commit() 
            flash(f'Munkatárs törölve!', 'success')
        
    return redirect(url_for('projectWorkers', projectId=project.id))

@app.route('/addProjectJob/<int:projectId>', methods=['POST', 'GET'])
@login_required
def addProjectJob(projectId):
    """ Projekt feladat felvitele
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
    form = AddProjectJobForm()
    form.users.query = User.query.order_by(User.fullName).all()    
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
            'duration' : 10,
        }
        projectJob = ProjectJob(**projectJobData)
        db.session.add(projectJob)
        db.session.commit()
        flash(f'Sikeres feladat felvitel!', 'success')
        return redirect(url_for('projectData', projectId=projectId))
    else:
        data = {
            'form' : form,
            'activeLink' : 'projects',
            'projectId' : projectId,
        }
        return render_template('ProjectJob/addProjectJob.html', **data)

@app.route('/projectJobData/<int:projectJobId>')
@login_required
def projectJobData(projectJobId):
    """ Projekt feladat adatlap
    
    Arguments:
        projectId {[int]} -- Projekt azonosító
    
    Returns:
        [response]
    """
    projectJob = ProjectJob.query.get_or_404(projectJobId)
    project = Project.query.get_or_404(projectJob.projectId)
    return render_template('ProjectJob/projectJobData.html', projectJob=projectJob, project=project, activeLink='projects')

@app.route('/startJob/<int:projectJobId>')
@login_required
def startJob(projectJobId):    
    """ Projekt feladat levétele
    
    Arguments:
        projectJobId {[int]} -- Projekt feladat azonosító
    
    Returns:
        [response]
    """
    current_user.activeJobId = projectJobId
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/manageJob/<int:projectJobId>', methods=['POST'])
@login_required
def manageJob(projectJobId):
    """ Projekt feladat állapot változatás
    
    Arguments:
        projectJobId {[int]} -- Projekt feladat azonosító
    
    Returns:
        [response]
    """
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

# ----
# Felhasználókra vonatkozó URL-k
# ----
@app.route("/register", methods=['GET', 'POST'])
@login_required
def register():
    """ Felhasználó felvitele
    
    Returns:
        [response]
    """
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

@app.route("/login", methods=['GET', 'POST'])
def login():
    """ Bejelentkezés 

    Returns:
        [response]
    """
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
        
        flash(f'Hibás felhasználó név vagy jelszó!', 'danger')
        return redirect(url_for('login'))
    else:
        if current_user.is_authenticated == True:
            return redirect(url_for('index'))
        data = {
            'form' : form,             
        }
        return render_template('login.html', **data)

@app.route("/logout")
@login_required
def logout():
    """ Kijelentkezés 
    
    Returns:
        [response]
    """
    logout_user()
    return redirect(url_for('index'))

@app.route("/users")
@login_required
def users():
    """ Felhasználó lista oldal
    
    Returns:
        [response]
    """
    users = User.query.order_by(User.fullName).all()
    data = {
        'users' : users,
        'activeLink' : 'users',
    }
    return render_template('User/users.html', **data)

@app.route('/userData/<int:userId>')
@login_required
def userData(userId):
    """ Felhasználó adatlap megtekintése
    
    Arguments:
        userId {[int]} -- Felhasználó azonosító
    
    Returns:
        [response]
    """    
    user = User.query.get_or_404(userId)    
    jobs = User.getProjectJobListCategories(userId)
    data = {
        'user' : user,
        'projectCount' : len(user.projects),
        'pendingJobCount' : len(jobs['pendingJobs']),
        'doneJobCount' : len(jobs['doneJobs']),
        'activeLink' : 'users',
    }
    return render_template('User/userData.html', **data)

@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    """ Adataim menüpont
    
    Returns:
        [response]
    """
    form = ModifyAccountBaseDataForm()
    user = User.query.get_or_404(current_user.id)
    jobs = User.getProjectJobListCategories(current_user.id)
    data = {
        'user' : user,       
        'projectCount' : len(user.projects),
        'pendingJobCount' : len(jobs['pendingJobs']),
        'doneJobCount' : len(jobs['doneJobs']),
        'activeLink' : 'account',
    }

    if form.validate_on_submit():
        email = form.email.data
        userName =  form.userName.data
        oldUser = User.query.filter(
            or_(User.userName == userName, User.email == email), 
            and_(User.id != current_user.id)
        ).first()
        if oldUser is None or oldUser.id == current_user.id:
            user.userName = userName
            user.email = email
            db.session.commit()
            flash(f'Sikeres módosítás', 'success')
            return redirect(url_for('account'))
        else:
            flash(f'Adott felhasználónév vagy email foglalt!', 'danger')
            data['form'] = form
            return render_template('User/account.html', **data)
    else:
        if not form.is_submitted():
            form.userName.default = user.userName
            form.email.default = user.email
            form.process()
    
        data['form'] = form
        return render_template('User/account.html', **data)

@app.route('/changePassword', methods=['POST', 'GET'])
@login_required
def changePassword():
    """ Jelszó módosítás
    
    Returns:
        [response]
    """
    form = ModifyAccountPasswordForm()
    if form.validate_on_submit():
        user = load_user(current_user.id)
        passwordOld = form.passwordOld.data
        passwordNew = form.passwordNew.data
        confirmPassword = form.confirmPassword.data
        if bcrypt.check_password_hash(user.password, passwordOld) and passwordNew == confirmPassword:
            flash(f'Sikeres jelszó módosítás!', 'success')
            hashedPassword = bcrypt.generate_password_hash(passwordNew).decode('utf-8')
            user.password = hashedPassword
            db.session.commit()
            return redirect(url_for('account'))
        else:
            flash(f'Hibás aktuális jelszó!', 'danger')            
   
    data = {
        'activeLink' : 'account',
        'form' : form,
    }
    return render_template('User/changePassword.html', **data)

@app.route('/sendMessage', defaults = { 'targetUserId' : 0, 'subject': None }, methods=['POST', 'GET'])
@app.route('/sendMessage/<int:targetUserId>', defaults = { 'subject': None }, methods=['POST', 'GET'])
@app.route('/sendMessage/<int:targetUserId>/<string:subject>', methods=['POST', 'GET'])
@login_required
def sendMessage(targetUserId, subject):
    """ Üzenet küldés
    
    Arguments:
        targetUserId {[int]} -- Címzett felhasználó azonosító
        subject {[string]}   -- Tárgy
    
    Returns:
        [response]
    """ 
    form = SendMessageForm()    
    form.toUserId.query = User.query.filter(User.id!=current_user.id).order_by(User.fullName).all()    
    if form.validate_on_submit() and form.toUserId.data.id != current_user.id:       
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
        return redirect(url_for('sent'))
    else:
        if not form.is_submitted():
            form.toUserId.default = load_user(targetUserId)
            if subject is not None:
                form.subject.default = 'Re: ' + subject
            form.process()
        data = {
            'form' : form,
            'activeLink' : 'send',
        }
        return render_template('User/sendMessage.html', **data)

@app.route('/loadMessage/<int:messageId>', defaults = { 'fromPage' : None })
@app.route('/loadMessage/<int:messageId>/<string:fromPage>')
@login_required
def loadMessage(messageId, fromPage):
    """ Üzenet betöltés
    
    Arguments:
        messageId {[int]}   -- Üzenet azonosító
        fromPage {[string]} -- Inbox / Outbox -ból nyitottuk meg
    
    Returns:
        [response]
    """
    message = UserMessage.query.get_or_404(messageId)

    if message.readTime is None and message.toUserId == current_user.id:
        UserMessage.setRead(messageId)
        flash(f'Üzenet olvasottra állítva!', 'success')

    message.text = message.text.replace('\n', '<br />')
    return render_template('User/messageData.html', message=message, activeLink=fromPage)

@app.route('/inbox')
@login_required
def inbox():
    """ Bejővő Üzenetek
    
    Returns:
        [response]
    """
    messages = UserMessage.getRecievedMessages(current_user.id) 
    return render_template('User/inbox.html', messages=messages, activeLink='inbox')

@app.route('/sent')
@login_required
def sent():    
    """ Kimenő Üzenetek
    
    Returns:
        [response]
    """
    messages = UserMessage.getSentMessages(current_user.id) 
    return render_template('User/sent.html', messages=messages, activeLink='sent')

@app.route('/gantt')
def gantt():
    users = User.query.all()
    usersSelect =[u.serialize for u in users]


    return render_template('gantt.html', users=users)

