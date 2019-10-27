from flask import request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, text
from projectmanage import app, db
from projectmanage.models import User, Project, ProjectJob, ProjectJobLink
from datetime import datetime

@app.route('/api/jobList', methods=['GET'])
def jobsAll():
    """ Feladatok, kapcsolatok lekérése a charthoz
    
    Returns:
        [json] -- Feladatok és linkek serializálva
    """ 
    jobs  = []
    links = []
    
    if current_user.is_authenticated:	 
        jobs  = ProjectJob.query.filter(ProjectJob.deleted==False).order_by(ProjectJob.dateStart)
        links = ProjectJobLink.query.all()
        users = User.query.all()

    return jsonify(data=[i.serialize for i in jobs], links=[j.serialize for j in links])

@app.route('/api/task', methods=['POST'])
@login_required
def jobAddFromChart():     
    """ Feladat felvitele charton keresztül
    
    Returns:
        [json] -- Feladat serializálva / Üres JSON
    """ 
    if request.method == 'POST':
        data = request.form.to_dict()
        projectJob = ProjectJob()
        projectJob.projectId = 1
        projectJob.dateStart = datetime.strptime(data['start_date'], '%d-%m-%Y %H:%M')
        projectJob.dateEnd   = datetime.strptime(data['end_date']  , '%d-%m-%Y %H:%M')
        projectJob.duration  = data['duration']
        projectJob.estimatedTime = data['duration']
        projectJob.name        = data['text']
        projectJob.description = data['desc']
        projectJob.creatorUserId = current_user.id
        projectJob.workerUserId = data['userId']    

        db.session.add(projectJob)
        db.session.commit()

        return jsonify(projectJob.serialize) 
    
    return jsonify(data=[])
    

@app.route('/api/task/<int:projectJobId>', methods=['PUT', 'DELETE'])
@login_required
def jobManageFromChart(projectJobId):
    """ Feladat módosítása és törlése charton keresztül
    
    Arguments:
        projectJobId {[int]} -- Feladat azonosító
    
    Returns:
        [json] -- Feladat serializálva / Üres JSON
    """   
    data = request.form.to_dict() 
    # Feladat frissítése
    if request.method == 'PUT': 
        projectJob = ProjectJob.query.get(projectJobId)
        projectJob.dateStart = datetime.strptime(data['start_date'], '%d-%m-%Y %H:%M')
        projectJob.dateEnd   = datetime.strptime(data['end_date']  , '%d-%m-%Y %H:%M')
        projectJob.duration  = data['duration']
        projectJob.name      = data['text']
        projectJob.description = data['desc']
        projectJob.workerUserId = data['userId'] 
 
        db.session.add(projectJob)
        db.session.commit()

        return jsonify(projectJob.serialize)        
        
    # Feladat törlése    
    elif request.method == 'DELETE':
        ProjectJob.setDeleted(projectJobId)        
    return jsonify([])     

@app.route('/api/link', methods=['POST'])
@login_required
def linkAddFromChart():
    """ Link felvitele charton keresztül
    
    Returns:
        [json] -- Link serializálva / Üres JSON
    """ 
    if request.method == 'POST':
        data = request.form.to_dict()
        projectJobLink = ProjectJobLink()
        projectJobLink.source = data['source']
        projectJobLink.target = data['target']
        projectJobLink.type   = data['type']

        db.session.add(projectJobLink)
        db.session.commit()

        return jsonify(projectJobLink.serialize)
    
    return jsonify(data=[])

@app.route('/api/link/<int:projectJobLinkId>', methods=['PUT', 'DELETE'])
@login_required
def linkManageFromChart(projectJobLinkId):
    """ Link módosítása és törlése charton keresztül
    
    Arguments:
        projectJobLinkId {[int]} -- Feladat link azonosító
    
    Returns:
        [json] -- Link serializálva / Üres JSON
    """
    data = request.form.to_dict()    
    # Link frissítése
    if request.method == 'PUT':
        projectJobLink = ProjectJobLink.query.get(projectJobLinkId)
        projectJobLink.source = data['source']
        projectJobLink.target = data['target']
        projectJobLink.type   = data['type']

        db.session.add(projectJobLink)
        db.session.commit()

        return (projectJobLink.serialize)

    # Link törlése
    elif request.method == 'DELETE':
        ProjectJobLink.query.filter_by(id=projectJobLinkId).delete()
        db.session.commit()
    return jsonify([])