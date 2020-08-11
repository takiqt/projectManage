# Projekt Management Rendszer - projectManage

# **Takács Dániel - MSc Diplomamunka - 2019**

## **1. Virtual Env**
---

**Telepítés**

    pip install virtualenv

**Létrehozás**
    
Projekt mappájába belépni.

+ **Linux**

    + virtualenv --python=/usr/bin/python3 projectEnv

+ **Windows**
    + virtaulenv projectEnv

**Aktiválás**

+ **Linux**

    + source envs/projectEnv/bin/activate

+ **Windows**

    + projectEnv\Scripts\activate


**Csomag függőségek telepítése**

    pip install -r requirements.txt
    python -m pip install -r requirements.txt
    pip install flask-login

## **2. Adatbázis beállítás**

A `config.py`-ban beállítani az adatbázis elérést, illetve a projekt mappa elérését, a fájfeltöltéshez.


**2.1. SQLite tesztadatbázis config.**

```python
class Config(object):    
    SQLALCHEMY_DATABASE_URI = r'sqlite:///F:\projectManage\pmtest.db'
    FILE_UPLOADS = r'F:\projectManage\projectmanage\static\files'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    FILE_UPLOAD_SIZE = 3145728 # 3 MB in bytes
    FILE_EXTENSIONS = [ 'TXT' , 'RTF', 'ODF', 'ODS', 'DOC', 'DOCX', 'XLS', 'XLSX', 'MD', 
                        'JPG' , 'JPEG', 'PNG', 'GIF', 'BMP', 'CSV', 'JSON', 'PDF' ]
    SECRET_KEY = 'whatever_123X4_'
    USE_SESSION_FOR_NEXT = True
    DEBUG = True
    TESTING = True    
```

**2.2. MySQL config.**
```python
class Config(object):    
    #  https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
    SQLALCHEMY_DATABASE_URI = r'mysql://username:password@server/db'
    # ...
    # ...
```



## **3.1. Teszt adatbázis - SQLite3**

A **pmtest.db** fileban található egy előre feltöltött teszt adatbázis.

Teszt adatbázis felhasználók:
+ tesztuser - 123456 - Admin
+ teszt1 - 123456
+ teszt2 - 123456
+ teszt3 - 123456 - Passzivált

Továbbá találhatók teszt projektek és feladatok.


## **3.2. Adatbázis migráció - MySQL**
---
A `projectManage\migrations` mappa törlése ha létezik.

**Inicalizálás**
    
    python run.py db migrate

**Ellenőrzés, változások lekövetése**

    python run.py db migrate

**Adatbázis szerkezet frissítése**

    python run.py db upgrade

**Admin teszt felhasználó létrehozása**

    python run.py createAdmin --userName="tesztuser" --password="123456 --email="test@abc.hu" --fullName="Tesztelő Felhasználó"
    
## **4. Szerver indítása**
---
    python run.py runserver --host=127.0.0.2 --port 8000 --threaded

    http://127.0.0.2:8000