from flask import render_template, url_for, request, session, redirect, flash
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from sqlalchemy import or_, and_
from projectmanage import app, db, bcrypt, loginManager
from projectmanage.models import User, Project
from projectmanage.forms import *

# Kezdőlap
@app.route('/')
@app.route('/home')
@login_required
def index():     
    app.logger.warning(current_user)
    return render_template('home.html')

@loginManager.user_loader
def load_user(userId):    
    return User.query.get(int(userId))

def is_safe_url(urlTarget):
    refUrl  = urlparse(request.host_url)
    testUrl = urlparse(urljoin(request.host_url, urlTarget))
    return testUrl.scheme in ('http', 'https') and \
            refUrl.netloc == testUrl.netloc


def isAdmin(userId):
    user = User.query.filter_by(admin=1, id=userId).first()
    if user is not None:
        return True
    else:
        return False

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
@login_required
def register():
    form = RegisterFrom()
    if form.validate_on_submit():
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
        }
        return render_template('register.html', **data)

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
            return render_template('home.html')
        data = {
            'form' : form,             
        }
        return render_template('login.html', **data)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/users")
@login_required
def users():
    users = User.query.order_by(User.fullName).all()
    data = {
        'users' : users
    }
    return render_template('User/users.html', **data)

@app.route("/projects")
@login_required
def projects():
    projects = Project.query.order_by(Project.name).all()
    data = {
        'projects' : projects
    }
    return render_template('Project/projects.html', **data)

@app.route("/addProject", methods=['GET', 'POST'])
@login_required
def addProject():
    form = AddProjectForm()
    if form.validate_on_submit():
        projectData = {
            'name' : form.name.data
        }
        project = Project(**projectData)
        db.session.add(project)
        db.session.commit()
        flash(f'Sikeres projekt felvitel', 'success')
        return redirect(url_for('projects'))
    else:
        data = {
            'form' : form                 
        }
        return render_template('Project/addProject.html', **data)


@app.route("/projectData/<int:projectId>")
@login_required
def projectData(projectId):
    project = Project.query.get_or_404(projectId)
    return render_template('Project/projectData.html', project=project, menuTitle='adatlap')
    

@app.route("/projectLeaders/<int:projectId>", methods=['POST', 'GET'])
@login_required
def projectLeaders(projectId):
    project = Project.query.get_or_404(projectId)
    form = AddProjectLeader()
    form.users.query = User.query.all()

    if form.validate_on_submit():
        userId = form.users.data.id        
        user = User.query.filter_by(id=userId).first()
        project.leaders.append(user)
        db.session.commit()    
        

    return render_template('Project/projectUsers.html', project=project, menuTitle='vezetők', form=form)


@app.route("/projectWorkers/<int:projectId>", methods=['POST', 'GET'])
@login_required
def projectWorkers(projectId):
    project = Project.query.get_or_404(projectId)
    return render_template('Project/projectUsers.html', project=project, menuTitle='munkatársak')



## Test chartok
@app.route('/test1')
@login_required
def test1():
    return render_template('test1.html')