class Config(object):
    #  https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
    #  mysql://username:password@server/db
    SQLALCHEMY_DATABASE_URI = r'sqlite:///C:\path\to\project\projectManage\pmtest.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    FILE_UPLOADS = r'C:\path\to\project\projectmanage\static\files'
    FILE_UPLOAD_SIZE = 3145728 # 3 MB in bytes
    FILE_EXTENSIONS = [ 'TXT' , 'RTF', 'ODF', 'ODS', 'DOC', 'DOCX', 'XLS', 'XLSX', 'MD', 
                        'JPG' , 'JPEG', 'PNG', 'GIF', 'BMP', 'CSV', 'JSON', 'PDF' ]
    SECRET_KEY = 'whatever_123X4_'
    USE_SESSION_FOR_NEXT = True
    DEBUG = True
    TESTING = True    