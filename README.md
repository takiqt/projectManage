# Projekt Management Rendszer - projectManage

Takács Dániel

MSc Diplomamunka 

## Virtual Env
---

**Telepítés**

+ pip install virtualenv

**Létrehozás**

+ virtualenv --python=/usr/bin/python3 %name%

**Aktiválás**

**Linux**

+ source envs/pm/bin/activate

**Windows**

+ \path\to\env\Scripts\activate

**Telepített csomagok, modulok mentése**

+ pip freeze > requirements.txt

**Csomag függőségek telepítése**

+ pip install -r requirements.txt
+ python -m pip install -r requirements.txt


## Adatbázis migráció
---

**Ellenőrzés, változások lekövetése**

+ python run.py db migrate

**Adatbázis szerkezet frissítése**

+ python run.py db upgrade