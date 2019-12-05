from flask import render_template, url_for, request, session, redirect, \
                  flash, Response, jsonify, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, and_, text
from projectmanage import app, db, bcrypt, loginManager
from projectmanage.models import User, UserMessage, Project, ProjectJob, ProjectJobLink, \
                                 ProjectJobWorktimeHistory, ProjectJobFile
from projectmanage.forms import RegisterForm, LoginForm, SendMessageForm, ModifyAccountBaseDataForm, \
                                ModifyAccountPasswordForm, AddAndModifyProjectForm, AddProjectWorker, AddProjectLeader, \
                                AddAndModifyProjectJobForm, AddAndModifyProjectJobSubJob, AddProjectWorkTimeForm
from projectmanage.functions import load_user, page_not_found, is_safe_url, my_utility_processor, \
                                    allowedFile, allowedFileSize, remove_tags
from projectmanage.api import userJobsAll, projectJobsAll, jobAddFromChart, jobManageFromChart, \
                              linkAddFromChart, linkManageFromChart
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from random import randint
import pprint, os

# ----
# Projektre / Projekt feladatra vonatkozó URL-k
# ----
@app.route('/')
@app.route('/home')
@login_required
def index():
    """ Dashboard megjelenítése
    
    Returns:
        response
    """
    jobs = User.getProjectJobListCategories(current_user.id)
    pendingJobs = []
    for job in jobs['pendingJobs']:
        job.hasSubJob = ProjectJob.hasSubJob(job)
        job.canCreateSubJob = ProjectJob.canCreateSubJob(job, current_user.id)
        pendingJobs.append(job)

    data = {
        'activeLink' : 'home',
        'activeJob' : jobs['activeJob'],
        'pendingJobs' : pendingJobs,
        'doneJobs' : jobs['doneJobs'],
        'form' : AddProjectWorkTimeForm(),
    }
    return render_template('Index/home.html', **data)

@app.route('/gantt')
@login_required
def userGantt():
    """ Felhasználó Gantt megjelenítése
    
    Returns:
        response
    """
    data = {
        'activeLink' : 'home',        
        'mode'       : 'user',
        'users'      : [{'id': current_user.id, 'name': current_user.fullName }],
    }
    return render_template('Gantt/gantt.html', **data)

@app.route("/projects")
@login_required
def projects():
    """ Projekt lista
    
    Returns:
        response
    """
    if current_user.admin == True:
        projects = Project.query.order_by(Project.name).all()
    else:
        projects = User.getUserVisibleProjects(current_user.id)    
    
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
        response
    """
    form = AddAndModifyProjectForm()
    if form.validate_on_submit() and form.dateStart.data <= form.dateEnd.data:
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
                'name' : remove_tags(form.name.data),
                'description' : remove_tags(form.description.data),
                'dateStart' : form.dateStart.data,
                'dateEnd' : form.dateEnd.data,
                'creatorUserId' : current_user.id,
            }
            project = Project(**projectData)              
            db.session.add(project)
            project.leaders.append(current_user)
            db.session.commit()
            flash(f'Sikeres projekt felvitel!', 'success')
            return redirect(url_for('projects'))
    else:
        if request.method == 'POST':
            flash('Kezdésnek ({}) korábban kell lennie mint a Végzésnek ({})!'.format(form.dateStart.data, form.dateEnd.data), 'danger')
        data = {
            'form' : form,
            'modify' : False,
            'activeLink' : 'addProject',
        }
        return render_template('Project/addProject.html', **data)

@app.route("/projectData/<int:projectId>")
@login_required
def projectData(projectId):
    """ Projekt adatai aloldal
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId)  
    project.isModifiable = Project.isModifiable(project, current_user.id)  
    if current_user.admin == False and project not in User.getUserVisibleProjects(current_user.id):
        return redirect(url_for('projects'))  
      
    worktimesAll = []
    for job in project.projectJobs:
        worktimes = ProjectJob.getJobWorktimes(job.id)
        for worktime in worktimes:
            user = User.query.get(worktime.createUserId)
            projectJob = ProjectJob.query.get(job.id)
            userName = user.fullName
            worktimesAll.append({
                'projectJobName' : projectJob.name, 
                'userName' :userName, 
                'date' : worktime.createTime, 
                'workTime' : worktime.workTime   
            })        
        job.isModifiable = ProjectJob.isModifiable(job, current_user.id)
    worktimesAllSorted = sorted(worktimesAll, key=lambda k: k['date']) 
    riport = Project.getRiportData(project)

    data = {
        'project' : project,
        'activeLink' : 'projects',
        'sumHours' : riport['booked'],
        'estimatedHours' : riport['estimated'],
        'riportPercent' : riport['percent'],
        'worktimesAll' : worktimesAllSorted,
    }
    return render_template('Project/projectData.html', **data)

@app.route("/projectModify/<int:projectId>", methods=['GET', 'POST'])
@login_required
def projectModify(projectId):
    """ Projekt módosítás aloldal
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId)
    if current_user.id != project.creatorUserId:
        return redirect(url_for('index'))

    form = AddAndModifyProjectForm()
    if form.validate_on_submit() and form.dateStart.data <= form.dateEnd.data:
        oldProject = Project.query.filter_by(name=form.name.data).first()
        if oldProject is not None and oldProject.id != project.id:
            flash(f'{form.name.data} - Adott néven már van rögzített projekt!', 'danger')
            data = {
                'form' : form,
                'modify' : True,
                'activeLink' : 'projects',                
            }
            return render_template('Project/addProject.html', **data)
        else:             
            project.name = remove_tags(form.name.data)
            project.description = remove_tags(form.description.data)
            project.dateStart = form.dateStart.data
            project.dateEnd = form.dateEnd.data

            db.session.add(project)
            db.session.commit()

            flash(f'Sikeres projekt módosítás!', 'success')
            return redirect(url_for('projects'))
    else:
        if request.method == 'GET':
            form.name.data = project.name
            form.description.data = project.description
            form.dateStart.data = project.dateStart
            form.dateEnd.data = project.dateEnd
        elif request.method == 'POST':
            flash('Kezdésnek ({}) korábban kell lennie mint a Végzésnek ({})!'.format(form.dateStart.data, form.dateEnd.data), 'danger')

        data = {
            'form' : form,
            'modify' : True,
            'activeLink' : 'projects',
        }
        return render_template('Project/addProject.html', **data)

@app.route("/projectClose/<int:projectId>")
@login_required
def projectClose(projectId):
    """ Projekt lezárása
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get(projectId)
    if Project.isClosable(project, current_user.id):
        project.isDone = True
        project.doneTime = datetime.now()
        db.session.add(project)
        db.session.commit()
        flash(f'{project.name} nevű projekt sikeresen lezárva!', 'success')
    else:
        flash(f'{project.name} nevű projekt nem zárható le! Van nem elkészült feladat a projektben!', 'danger')
    return redirect(url_for('projects'))

@app.route("/projectArchive/<int:projectId>")
@login_required
def projectArchive(projectId):
    """ Projekt archiválása (törlés)
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get(projectId)
    if Project.isArchivable(project, current_user.id):
        project.deleted = True
        project.delTime = datetime.now()
        db.session.add(project)
        db.session.commit()
        flash(f'{project.name} nevű projekt sikeresen archiválva!', 'success')
    else:
        flash(f'{project.name} nevű projekt nem archiválható! Van aktív feladat a projektben!', 'danger')
    return redirect(url_for('projects'))

@app.route("/projectGantt/<int:projectId>")
@login_required
def projectGantt(projectId):
    """ Projekt Gantt oldal
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId) 
    if not project in User.getUserVisibleProjects(current_user.id) or not Project.isActive(project):
        return redirect(url_for('projectData', projectId=projectId))
 
    users = Project.getProjectUsers(project)
    
    data = {
        'activeLink' : 'projects',
        'mode'       : 'project',
        'project'    : project,
        'users'      : users,
        'canAdd'     : True if current_user in project.leaders else False,
    }
    return render_template('Gantt/gantt.html', **data)

@app.route("/projectLeaders/<int:projectId>", methods=['POST', 'GET'])
@login_required
def projectLeaders(projectId):
    """ Vezető lista aloldal
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId)
    if current_user.id != project.creatorUserId or not Project.isModifiable(project, current_user.id):
        flash(f'Projekt nem módosítható', 'danger')
        return redirect(url_for('projectData', projectId=projectId))
    form = AddProjectLeader()
    form.users.query = User.query.filter(User.deleted == False).order_by(User.fullName).all()

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
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId)
    if current_user.id != project.creatorUserId or not Project.isModifiable(project, current_user.id):
        flash(f'Projekt nem módosítható', 'danger')
        return redirect(url_for('projectData', projectId=projectId))   

    form = AddProjectWorker()
    form.users.query = User.query.filter(User.deleted == False).order_by(User.fullName).all()
    
    if form.validate_on_submit():
        userId = form.users.data.id        
        sql = text('select COUNT(*) AS count from projectworkers WHERE userId = :userId AND projectId = :projectId')
        result = db.engine.execute(sql, { 'userId' : userId, 'projectId' : project.id })
        res = result.fetchone()
        if res['count'] == 0:
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
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId)    
    if current_user == project.creator and Project.isModifiable(project, current_user.id):
        userId = request.form.get('delUserId')
        user = User.query.filter_by(id=userId).first()
        if user is not None:
            if not User.hasProjectConnection(user, project):
                project.leaders.remove(user)
                db.session.commit() 
                flash(f'Vezető törölve!', 'success')
            else:
                flash(f'Vezető nem törölhető, van létrehozott vagy elvégzendő feladata!', 'danger')
    else:
        flash(f'Projekt nem módosítható', 'danger')
        return redirect(url_for('projectData', projectId=projectId))
        
    return redirect(url_for('projectLeaders', projectId=project.id))

@app.route('/projectWorkers/<int:projectId>/delete', methods=['POST'])
@login_required
def deleteProjectWorker(projectId):
    """ Munkatárs törlése a projektből
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId)
    if current_user == project.creator and Project.isModifiable(project, current_user.id):
        userId = request.form.get('delUserId')
        user = User.query.filter_by(id=userId).first()
        if user is not None:
            if not User.hasProjectConnection(user, project):
                project.workers.remove(user)
                db.session.commit() 
                flash(f'Munkatárs törölve!', 'success')
            else:
                flash(f'Munkatárs nem törölhető, van létrehozott vagy elvégzendő feladata!', 'danger')
    else:
        flash(f'Projekt nem módosítható', 'danger')
        return redirect(url_for('projectData', projectId=projectId))
        
    return redirect(url_for('projectWorkers', projectId=project.id))

@app.route('/addProjectJob/<int:projectId>', methods=['POST', 'GET'])
@login_required
def addProjectJob(projectId):
    """ Projekt feladat felvitele
    
    Arguments:
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get_or_404(projectId)
    if current_user not in project.leaders:
        return redirect(url_for('projects'))
    form = AddAndModifyProjectJobForm()
    projectUsers = Project.getProjectUsers(project)
    projectUserChoices = []
    for u in projectUsers:
        uc = (u['id'], u['name'])
        projectUserChoices.append(uc)

    form.users.choices = projectUserChoices
    if form.validate_on_submit():
        date = form.date.data
        start = form.start.data
        duration = form.duration.data
        dateStart = datetime.combine(date, start)
        dateEnd = dateStart + timedelta(hours=duration)

        projectJobData = {
            'name' : remove_tags(form.name.data),
            'description' : remove_tags(form.description.data),            
            'dateStart' : dateStart,
            'dateEnd' : dateEnd,
            'estimatedTime' : form.estimatedTime.data,
            'duration' : duration,
            'creatorUserId' : current_user.id,
            'workerUserId' : form.users.data,
            'projectId' : projectId,            
        }
        projectJob = ProjectJob(**projectJobData)
        db.session.add(projectJob)
        db.session.commit()
        flash(f'Sikeres feladat felvitel!', 'success')
        return redirect(url_for('projectData', projectId=projectId))
    else:
        data = {
            'form' : form,
            'modify' : False,
            'activeLink' : 'projects',
            'projectId' : projectId,
        }
        return render_template('ProjectJob/addProjectJob.html', **data)

@app.route('/projectJobModify/<int:projectJobId>', methods=['GET', 'POST'])
@login_required
def projectJobModify(projectJobId):
    """ Projekt feladat módosítás
    
    Arguments:
        projectJobId {int} -- Projekt feladat azonosító
    
    Returns:
        response
    """
    projectJob = ProjectJob.query.get_or_404(projectJobId)
    project    = Project.query.get_or_404(projectJob.projectId)
    form = AddAndModifyProjectJobForm()
    projectUsers = Project.getProjectUsers(project)
    projectUserChoices = []
    for u in projectUsers:
        uc = (u['id'], u['name'])
        projectUserChoices.append(uc)

    form.users.choices = projectUserChoices

    if not ProjectJob.isModifiable(projectJob, current_user.id):
        flash(f'Projekt feladat nem módosítható!', 'danger')
        return redirect(url_for('index'))
    if form.validate_on_submit():        
        date = form.date.data
        start = form.start.data
        duration = form.duration.data
        dateStart = datetime.combine(date, start)
        dateEnd = dateStart + timedelta(hours=duration)
        originalWorkerUserId = projectJob.workerUserId
        projectJob.name = remove_tags(form.name.data)
        projectJob.description = remove_tags(form.description.data)
        projectJob.dateStart = dateStart
        projectJob.dateEnd = dateEnd
        projectJob.estimatedTime = form.estimatedTime.data
        projectJob.duration = duration
        projectJob.workerUserId =  form.users.data

        db.session.add(projectJob)
        db.session.commit()

        subJobsText = ''
        if ProjectJob.hasSubJob(projectJob) and projectJob.workerUserId != originalWorkerUserId:
            for job in ProjectJob.getSubJobs(projectJob):
                job.workerUserId = form.users.data
                db.session.add(job)
                db.session.commit()
            subJobsText = ' Projekt alfeladatainak felhasználója is módosítva!'

        flash(f'Sikeres projekt feladat módosítás!' + subJobsText, 'success')
        return redirect(url_for('projectData', projectId=projectJob.projectId))
    else:
        form.name.data = projectJob.name
        form.description.data = projectJob.description
        form.users.data = User.query.get(projectJob.workerUserId)
        form.estimatedTime.data = projectJob.estimatedTime
        form.duration.data = projectJob.duration
        start = date = projectJob.dateStart     
        form.start.data = start
        form.date.data = date       

        data = {
            'form' : form,
            'modify' : True,
            'hasSubJob' : ProjectJob.hasSubJob(projectJob),
            'activeLink' : 'projects',
            'projectId' : projectJob.projectId,
        }
        return render_template('ProjectJob/addProjectJob.html', **data)

@app.route('/projectJobData/<int:projectJobId>')
@login_required
def projectJobData(projectJobId):
    """ Projekt feladat adatlap
    
    Arguments:
        projectJobId {int} -- Projekt feladat azonosító
    
    Returns:
        response
    """    
    projectJob = ProjectJob.query.get_or_404(projectJobId)
    project = Project.query.get_or_404(projectJob.projectId)
    if project not in User.getUserVisibleProjects(current_user.id):
        return redirect(url_for('projects'))

    projectJob.hasSubJob = ProjectJob.hasSubJob(projectJob)   
    
    if ProjectJob.hasSubJob(projectJob) :
        worktimesAll = [] 
        worktimesSorted = [] # Nincs feladat munkaidő        
        for job in ProjectJob.getSubJobs(projectJob):
            worktimes = ProjectJob.getJobWorktimes(job.id)
            for worktime in worktimes:
                user = User.query.get(worktime.createUserId)
                projectSubJob = ProjectJob.query.get(job.id)
                userName = user.fullName
                worktimesAll.append({
                    'projectJobName' : projectSubJob.name, 
                    'userName' :userName, 
                    'date' : worktime.createTime, 
                    'workTime' : worktime.workTime,
                    'comment' : worktime.comment
                })        
        worktimesSubJob = sorted(worktimesAll, key=lambda k:  k['date'])
    else:
        projectJob.workTimes = ProjectJob.getJobWorktimes(projectJobId)
        worktimes = []
        worktimesSubJob = [] # Nincs alfeladat munkaidő
        for worktime in projectJob.workTimes:
            user = User.query.get(worktime.createUserId)
            worktimes.append({
                'userName' : user.fullName, 
                'date' : worktime.createTime, 
                'workTime' : worktime.workTime,
                'comment' : worktime.comment
            })
        worktimesSorted = sorted(worktimes, key=lambda k:  k['date'])

    data = {
        'projectJob' : projectJob,
        'project'    : project,
        'worktimes'  : worktimesSorted,
        'worktimesSubJob'  : worktimesSubJob,
        'sumHours'   : ProjectJob.getJobWorktimesAll(projectJob.id),        
        'activeLink' : 'projects', 
    }
    return render_template('ProjectJob/projectJobData.html', **data)

@app.route('/uploadFileToJob/<int:projectJobId>', methods=['GET', 'POST'])
@login_required
def uploadFileToJob(projectJobId):
    """ Projekt feladathoz file feltöltése
    
    Arguments:
        projectJobId {int} -- Projekt feladat azonosító
    
    Returns:
        response
    """
    projectJob = ProjectJob.query.get_or_404(projectJobId)
    project = Project.query.get_or_404(projectJob.projectId)
    if project not in User.getUserVisibleProjects(current_user.id):
        return redirect(url_for('projects'))
    
    data = {
        'projectJob' : projectJob,
        'allowed'    : str(app.config['FILE_EXTENSIONS']).strip('[]').lower(),
        'maxSize'    : str(app.config['FILE_UPLOAD_SIZE'] / pow(1024, 2)) + ' MB',
        'activeLink' : 'projects', 
    }
    
    if request.method == 'POST':        
        if request.files:            
            file = request.files['file']
            fileName = file.filename
            # Név, kiterjesztés ellenőrzés
            if fileName == '' or not allowedFile(fileName):
                flash(f'Nem megengedett kiterjesztés!', 'danger')
                return render_template('ProjectJob/upload.html', **data)
            # Méret ellenőrzés
            if not allowedFileSize(request.cookies.get("fileSize")):
                flash(f'Fájl mérete meghaladja a megengedett méretet!', 'danger')
                return render_template('ProjectJob/upload.html', **data)
            # Biztonságos egyedi filename 
            secureFileName = str(projectJobId) + '_' + str(randint(1, 1000)) + '_' + secure_filename(fileName)            
            savePath = os.path.join(app.config['FILE_UPLOADS'], secureFileName)
            # Mentés       
            file.save(savePath)                        
            # Ha kijátsza a cookie-t akkor mentés után újra ellenőrzés
            if not allowedFileSize(os.path.getsize(savePath)) and os.path.exists(savePath):
                os.remove(savePath)
                flash(f'Fájl mérete meghaladja a megengedett méretet!', 'danger')
                return render_template('ProjectJob/upload.html', **data)
            else:
                # Kapcsolat a Projekt feladattal
                fileData = {
                    'projectJobId'  : projectJobId,
                    'fileName'      : secureFileName,
                    'createTime'    : datetime.now(),
                    'creatorUserId' : current_user.id,
                }
                projectJobFile = ProjectJobFile(**fileData)
                db.session.add(projectJobFile)
                db.session.commit()
                flash(f'Sikeres fájl feltöltés! {secureFileName}', 'success')    

    return render_template('ProjectJob/upload.html', **data)

@app.route('/downloadFile/<int:fileId>')
@login_required
def downloadFile(fileId):
    """ Projekt feladat file letöltése
    
    Arguments:
        fileId {int} -- Projekt feladat file azonosító
    
    Returns:
        response
    """
    projectJobFile = ProjectJobFile.query.get_or_404(fileId)
    if projectJobFile.projectJob.project in User.getUserVisibleProjects(current_user.id):
        try:
            return send_from_directory(app.config['FILE_UPLOADS'], filename=projectJobFile.fileName, as_attachment=True)
        except FileNotFoundError:
            abort(404)

@app.route('/removeFile/<int:fileId>')
@login_required
def removeFile(fileId):
    """ Projekt feladat file törlése, és átmozgatása 
        a törölt könyvtárba
    
    Arguments:
        fileId {int} -- Projekt feladat file azonosító
    
    Returns:
        response
    """
    projectJobFile = ProjectJobFile.query.get_or_404(fileId)
    if projectJobFile.projectJob.project in User.getUserVisibleProjects(current_user.id) and projectJobFile.creatorUserId == current_user.id:
        if ProjectJobFile.deleteFile(projectJobFile):
            flash(f'Fájl törölve!', 'success')
        else:
            flash(f'Fájl nem törölhető!', 'danger')

    return redirect(url_for('projectJobData', projectJobId=projectJobFile.projectJobId))

@app.route('/startJob/<int:projectJobId>')
@login_required
def startJob(projectJobId):    
    """ Projekt feladat levétele
    
    Arguments:
        projectJobId {int} -- Projekt feladat azonosító
    
    Returns:
        response
    """
    projectJob = ProjectJob.query.get_or_404(projectJobId)
    if ProjectJob.isManagable(projectJob, current_user.id):
        current_user.activeJobId = projectJobId
        db.session.commit()
    else:
        flash(f'Feladat nem vehető le!', 'danger')

    return redirect(url_for('index'))

@app.route('/manageJob/<int:projectJobId>', methods=['POST', 'GET'])
@login_required
def manageJob(projectJobId):
    """ Projekt feladat állapot változatás
    
    Arguments:
        projectJobId {int} -- Projekt feladat azonosító
    
    Returns:
        response
    """
    projectJob = ProjectJob.query.get_or_404(projectJobId)
    if not ProjectJob.isManagable(projectJob, current_user.id) or request.method == 'GET':
        flash(f'Feladat nem módosítható!', 'danger')
        return redirect(url_for('index'))
    comment = remove_tags(request.form.get('comment'))
    workTimeString = request.form.get('workTime')
    workTime = float(workTimeString.replace(',', '.'))
    done = request.form.get('done')
    pending = request.form.get('pending')

    if comment.strip() != '' and workTime > 0:
        workTimeHistoryData = {
            'comment' : comment,
            'workTime' : workTime,
            'projectJobId' : projectJobId,
            'createUserId' : current_user.id,
        }
        projectJobWorktimeHistory = ProjectJobWorktimeHistory(**workTimeHistoryData)
        db.session.add(projectJobWorktimeHistory)
        current_user.activeJobId = 0
        if done is not None:
            projectJob = ProjectJob.query.get_or_404(projectJobId)            
            ProjectJob.setDone(projectJob.id)
            flash(f'Feladat elkészült!', 'success')
        elif pending is not None:
            flash(f'Feladat várakozó állapotra állítva!', 'success')
        
        db.session.commit()
    else: 
        flash(f'Hibás munkaidő adatok!', 'danger')

    return redirect(url_for('index'))

@app.route('/projectJobCheckDone/<int:projectJobId>/<int:projectId>')
@login_required
def projectJobCheckDone(projectJobId, projectId):
    """ Elkészült Projekt feladat ellenőrzése
    
    Arguments:
        projectJobId {int} -- Projekt feladat azonosító
        projectId {int} -- Projekt azonosító
    
    Returns:
        response
    """
    project = Project.query.get(projectId)
    projectJob = ProjectJob.query.get(projectJobId)
    if project.creator == current_user and projectJob.isDone == True and projectJob.seen == False:
        projectJob.seen = True
        projectJob.seenTime = datetime.now()
        db.session.add(projectJob)
        db.session.commit()
        flash(f'Sikeres ellenőrzés!', 'success')
    else:
        flash(f'Sikertelen ellenőrzés!', 'danger')
    return redirect(url_for('projectData', projectId=projectId))

@app.route('/createSubJob/<int:parentJobId>', methods=['POST', 'GET'])
@login_required
def projectJobCreateSubJob(parentJobId):
    """ Várakozó elvégzendő feladathoz alfeladat felvitele
    
    Arguments:
        parentJobId {int} -- Szülő Projekt feladat azonosító
    
    Returns:
        response
    """
    form = AddAndModifyProjectJobSubJob()
    parentJob = ProjectJob.query.get_or_404(parentJobId)
    if not ProjectJob.canCreateSubJob(parentJob, current_user.id):
        flash(f'Feladathoz nem lehet alfeladatot rögzíteni!', 'danger')
        return redirect(url_for('index'))
    project   = Project.query.get_or_404(parentJob.projectId)

    if project not in User.getUserVisibleProjects(current_user.id):
        flash(f'Feladathoz nem lehet alfeladatot rögzíteni!', 'danger')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        date = form.date.data
        start = form.start.data
        duration = form.duration.data
        dateStart = datetime.combine(date, start)
        dateEnd = dateStart + timedelta(hours=duration)
        
        projectJobData = {
            'name' : remove_tags(form.name.data),
            'description' : remove_tags(form.description.data),            
            'dateStart' : dateStart,
            'dateEnd' : dateEnd,
            'estimatedTime' : 0,
            'duration' : duration,
            'creatorUserId' : current_user.id,
            'workerUserId' : current_user.id,
            'projectId' : project.id,            
            'parentJobId' : parentJob.id,            
        }
        projectJob = ProjectJob(**projectJobData)

        db.session.add(projectJob)
        db.session.commit()

        jobLinkData = {
            'source' : projectJob.id,
            'target' : parentJob.id,
            'type'   : '2', # finish_to_finish
        }
        link = ProjectJobLink(**jobLinkData)
        
        db.session.add(link)
        db.session.commit()

        flash(f'Sikeres alfeladat felvitel!', 'success')
        return redirect(url_for('index'))
    else:
        data = {
            'form' : form,
            'parentJob' : str(parentJob),
            'activeLink' : 'projects',
        }
        return render_template('ProjectJob/addProjectJobSubJob.html', **data)

# ----
# Felhasználókra vonatkozó URL-k
# ----
@app.route("/register", methods=['GET', 'POST'])
@login_required
def register():
    """ Felhasználó felvitele
    
    Returns:
        response
    """
    if current_user.admin != True:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        oldUser = User.query.filter(or_(User.userName == form.userName.data, User.email == form.email.data)).first()
        if oldUser is not None:
            flash(f'Adott felhasználónév vagy email foglalt!', 'danger')
            data = {
                'form' : form,
                'activeLink' : 'users',  
            }              
            return render_template('User/register.html', **data)
        else:
            hashedPassword = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            userData = {
                'userName' : remove_tags(form.userName.data),
                'fullName' : remove_tags(form.fullName.data),
                'password' : hashedPassword,
                'email'    : form.email.data
            }
            user = User(**userData)
            db.session.add(user)
            db.session.commit()
            flash(f'Felhasználó regisztrálva {form.userName.data}', 'success')        
            return redirect(url_for('users'))
    else:
        data = {
            'form' : form,    
            'activeLink' : 'users',
        }
        return render_template('User/register.html', **data)

@app.route('/passiveUser/<int:userId>')
@login_required
def passiveUser(userId):
    """ Felhasználó passziválása
    
    Arguments:
        userId {int} -- Felhasználó azonosító
    
    Returns:
        response
    """
    if current_user.admin != True:
        return redirect(url_for('index'))

    user = User.query.get(userId)
    if User.isPassivable(user, current_user):
        user.deleted = True
        user.delTime = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash(f'Sikeres felhasználó passziválás!', 'success')
    else:
        flash(f'Sikertelen felhasználó passziválás!', 'danger')
    return redirect(url_for('users'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    """ Bejelentkezés 

    Returns:
        response
    """
    form = LoginForm()
    if form.validate_on_submit():
        userName = form.userName.data
        password = form.password.data
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter(and_(
            User.userName == userName,
            User.deleted == False
        )).first()

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
        return render_template('Index/login.html', **data)

@app.route("/logout")
@login_required
def logout():
    """ Kijelentkezés 
    
    Returns:
        response
    """
    logout_user()
    return redirect(url_for('index'))

@app.route("/users")
@login_required
def users():
    """ Felhasználó lista oldal
    
    Returns:
        response
    """
    users = User.query.filter(User.deleted == False).order_by(User.fullName).all()
    if current_user.admin == True:
        passiveUsers = User.query.filter(User.deleted == True).order_by(User.fullName).all()
    else:
        passiveUsers = None
    data = {
        'users' : users,
        'passiveUsers' : passiveUsers,
        'activeLink' : 'users',
    }
    return render_template('User/users.html', **data)

@app.route('/userData/<int:userId>')
@login_required
def userData(userId):
    """ Felhasználó adatlap megtekintése
    
    Arguments:
        userId {int} -- Felhasználó azonosító
    
    Returns:
        response
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

@app.route('/userRiport/<int:userId>')
@login_required
def userRiport(userId):
    """ Felhasználó riport megtekintése
    
    Arguments:
        userId {int} -- Felhasználó azonosító
    
    Returns:
        response
    """    
    user = User.query.get_or_404(userId)    
    creatorRiport = User.getJobCreatorRiportData(user)
    workerRiport  = User.getJobWorkerRiportData(user)
    data = {
        'user' : user,
        'createdCount' : creatorRiport['jobCount'],        
        'creatorRiportEstimated': creatorRiport['estimated'],
        'creatorRiportBooked': creatorRiport['booked'],
        'creatorRiportPercent': creatorRiport['percent'],
        'workerCount'  : workerRiport['jobCount'],
        'workerRiportEstimated': workerRiport['estimated'],
        'workerRiportBooked': workerRiport['booked'],
        'workerRiportPercent': workerRiport['percent'],
        'activeLink' : 'users',
    }
    return render_template('User/userRiport.html', **data)

@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    """ Adataim menüpont
    
    Returns:
        response
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
        userName =  remove_tags(form.userName.data)
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
        response
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
        targetUserId {int} -- Címzett felhasználó azonosító
        subject {string}   -- Tárgy
    
    Returns:
        response
    """ 
    form = SendMessageForm()    
    form.toUserId.query = User.query.filter(and_(
        User.id != current_user.id,
        User.deleted == False
    )).order_by(User.fullName).all()    
    if form.validate_on_submit() and form.toUserId.data.id != current_user.id:       
        messageData = {
            'text' : remove_tags(form.text.data),
            'subject' : remove_tags(form.subject.data),
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

@app.route('/loadMessage/<int:messageId>', defaults = { 'fromPage' : 'index' })
@app.route('/loadMessage/<int:messageId>/<string:fromPage>')
@login_required
def loadMessage(messageId, fromPage):
    """ Üzenet betöltés
    
    Arguments:
        messageId {int}   -- Üzenet azonosító
        fromPage {string} -- Inbox / Outbox / Default index -ból nyitottuk meg
    
    Returns:
        response
    """
    message = UserMessage.query.get_or_404(messageId)
    if not UserMessage.isVisibleByUser(message, current_user.id):
        return redirect(url_for('index'))

    if message.readTime is None and message.toUserId == current_user.id:
        UserMessage.setRead(messageId)
        flash(f'Üzenet olvasottra állítva!', 'success')

    data = {
        'message'    : message,
        'activeLink' : fromPage,
    }
    return render_template('User/messageData.html', **data)

@app.route('/inbox')
@login_required
def inbox():
    """ Bejővő Üzenetek
    
    Returns:
        response
    """
    messages = UserMessage.getRecievedMessages(current_user.id)
    data = {
        'messages' : messages,
        'activeLink' : 'inbox',
    } 
    return render_template('User/inbox.html', **data)

@app.route('/sent')
@login_required
def sent():    
    """ Kimenő Üzenetek
    
    Returns:
        response
    """
    messages = UserMessage.getSentMessages(current_user.id) 
    data = {
        'messages' : messages,
        'activeLink' : 'sent',
    }  
    return render_template('User/sent.html', **data)