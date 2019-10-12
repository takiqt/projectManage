
from projectmanage import app, db, bcrypt, loginManager
from urllib.parse import urlparse, urljoin
from projectmanage.models import User, Project, ProjectJob, ProjectJobWorktimeHistory, UserMessage
from flask import url_for, request, redirect

@loginManager.user_loader
def load_user(userId):    
    """ Felhasználó beléptetés segédfunkciója
    
    Arguments:
        userId {[int]} -- [Felhasználó azonosító]
    
    Returns:
        [Object] -- [User]
    """    
    return User.query.get(int(userId))

def is_safe_url(urlTarget):
    """ Valós url vizsgálat
    
    Arguments:
        urlTarget {[string]} -- [Hívott URL]
    
    Returns:
        [bool] -- [True ha létezik, különben False]
    """
    refUrl  = urlparse(request.host_url)
    testUrl = urlparse(urljoin(request.host_url, urlTarget))
    return testUrl.scheme in ('http', 'https') and \
            refUrl.netloc == testUrl.netloc

@app.errorhandler(404)
def page_not_found(e):
    """ Error handler oldal
    
    Arguments:
        e {[error]}
    
    Returns:
        [response]
    """
    return redirect(url_for('login'))

@app.context_processor
def my_utility_processor():
    """ Template segédfüggvények

    Returns:
        [dict]
    """
    def getProjectName(projectId):
        """ Projekt név lekérés
        Arguments:
            projectId {[int]} -- [Projekt azonosító]

        Returns:
            [string] -- [Név]
        """
        project = Project.query.get_or_404(projectId)
        return project.name
    def getProjectJobName(projectJobId):
        """ Projekt feladat név lekérés
        Arguments:
            projectJobId {[int]} -- [Projekt feladat azonosító]

        Returns:
            [string] -- [Név]
        """
        if projectJobId == 0:
            return 'Nincs aktív feladat kiválasztva'
        else:
            projectJob = ProjectJob.query.get_or_404(projectJobId)
            return projectJob.name
    def getUserName(userId):
        """ Felhasználó név lekérés

        Arguments:
            userId {[int]} -- [Felhasználó azonosító]

        Returns:
            [string] -- [Név]
        """
        user = User.query.get_or_404(userId)
        return user.fullName
    def getUnreadCount(userId):
        """ Felhasználó olvasatlan üzenetek lekérés

        Arguments:
            userId {[int]} -- [Felhasználó azonosító]
        
        Returns:
            [int] -- [Darabszám]
        """
        return UserMessage.getUnreadCount(userId)
    return dict(
        getProjectName=getProjectName, 
        getUserName=getUserName, 
        getUnreadCount=getUnreadCount,
        getProjectJobName=getProjectJobName,
    )
