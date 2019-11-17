from flask_wtf import FlaskForm
from wtforms import Form, StringField, FloatField, DateField, TimeField, IntegerField, \
                    SelectField, TextAreaField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField

class RegisterForm(FlaskForm):
    """ Felhasználó felvitel Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    userName = StringField('Felhasználó név', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=6, max=30, message="Mező hosszának 6 és 30 karakter között kell lennie!")
                ])
    fullName = StringField('Teljes név',
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=6, max=150, message="Mező hosszának 6 és 150 karakter között kell lennie!")
                ])
    email = StringField('E-mail',
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Email(message="Érvényes e-mail címnek kell lennie!")
                ])
    password = PasswordField('Jelszó', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=6, max=30, message="Mező hosszának 6 és 30 karakter között kell lennie!")
                ])
    confirmPassword = PasswordField('Jelszó megerősítése', 
                        validators=[
                            DataRequired(message="Megadása kötelező!"), 
                            Length(min=6, max=30, message="Mező hosszának 6 és 30 karakter között kell lennie!"), 
                            EqualTo('password', message="Jelszóval egyeznie kell!")
                        ]) 
    save = SubmitField('Felvitel')

class LoginForm(FlaskForm):
    """ Bejelentkezés Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    userName = StringField('Felhasználó név', 
                            validators=[DataRequired()])    
    password = PasswordField('Jelszó', 
                            validators=[DataRequired()])
    remember = BooleanField('Bejelentkezve maradok')
    login = SubmitField('Bejelentkezés')

class SendMessageForm(FlaskForm):
    """ Üzenet küldés Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    toUserId = QuerySelectField('Címzett', allow_blank=False, get_label='fullName')
    subject = StringField('Tárgy', validators=[
        DataRequired(message="Megadása kötelező!"),
        Length(min=5, max=50, message="Mező hosszának 5 és 50 karakter között kell lennie!")
    ])
    text = TextAreaField('Üzenet', validators=[DataRequired(message="Megadása kötelező!")])
    send = SubmitField('Küldés')

class ModifyAccountBaseDataForm(FlaskForm):
    """ Adataim módosítása Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    userName = StringField('Felhasználó név', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=6, max=30, message="Mező hosszának 6 és 30 karakter között kell lennie!")
                ])
    email = StringField('E-mail',
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Email(message="Érvényes e-mail címnek kell lennie!")
                ])    
    send = SubmitField('Módosítás')       

class ModifyAccountPasswordForm(FlaskForm):
    """ Jelszó módosítása Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    passwordOld = PasswordField('Aktuális Jelszó', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                ])
    passwordNew = PasswordField('Új Jelszó', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=6, max=30, message="Mező hosszának 6 és 30 karakter között kell lennie!")
                ])
    confirmPassword = PasswordField('Új Jelszó megerősítése', 
                        validators=[
                            DataRequired(message="Megadása kötelező!"), 
                            Length(min=6, max=30, message="Mező hosszának 6 és 30 karakter között kell lennie!"), 
                            EqualTo('passwordNew', message="Új Jelszóval egyeznie kell!")
                        ])
    send = SubmitField('Módosítás')                 

class AddAndModifyProjectForm(FlaskForm):
    """ Projekt felvitel Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    name = StringField('Projekt név', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=10, max=50, message="Mező hosszának 10 és 50 karakter között kell lennie!")
                ]) 
    description = TextAreaField('Leírás', validators=[DataRequired(message="Megadása kötelező!")])
    dateStart = DateField('Kezdő dátum', format='%Y-%m-%d', validators=[DataRequired(message="Megadása kötelező!")])
    dateEnd = DateField('Végző dátum', format='%Y-%m-%d', validators=[DataRequired(message="Megadása kötelező!")])    
    save = SubmitField('Felvitel')
    modify = SubmitField('Módosítás')
 
class AddProjectWorker(FlaskForm):
    """ Projekt munkatárs felvitel Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    users = QuerySelectField('Felhasználó hozzáadása', allow_blank=False, get_label='fullName')
    save = SubmitField('Felvitel')

class AddProjectLeader(FlaskForm):
    """ Projekt vezető felvitel Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    users = QuerySelectField('Felhasználó hozzáadása', allow_blank=False, get_label='fullName')
    save = SubmitField('Felvitel')

class AddAndModifyProjectJobForm(FlaskForm):
    """ Projekt feladat felvitel / módosítás Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    name = StringField('Feladat név', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=5, max=30, message="Mező hosszának 5 és 30 karakter között kell lennie!")
                ]) 
    description = TextAreaField('Leírás', validators=[DataRequired(message="Megadása kötelező!")])
    users = SelectField('Felhasználó', coerce=int)
    date = DateField('Dátum', format='%Y-%m-%d', validators=[DataRequired(message="Megadása kötelező!")])
    start = TimeField('Kezdés', validators=[DataRequired(message="Megadása kötelező!")])
    duration = IntegerField('Hossz', validators=[
        DataRequired(message="Megadása kötelező!"),
        NumberRange(min=1, message="Minimum 1-nek kell lennie!")
        ])
    estimatedTime = FloatField('Becsült idő', validators=[
        DataRequired(message="Megadása kötelező!"),
        NumberRange(min=1, message="Minimum 1-nek kell lennie!")
        ])    
    save = SubmitField('Felvitel')
    modify = SubmitField('Módosítás')

class AddAndModifyProjectJobSubJob(FlaskForm):
    """ Projekt alfeladat felvitel / módosítás Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    name = StringField('Feladat név', 
            validators=[
                DataRequired(message="Megadása kötelező!"), 
                Length(min=5, max=30, message="Mező hosszának 5 és 30 karakter között kell lennie!")
            ])    
    description = TextAreaField('Leírás', validators=[DataRequired(message="Megadása kötelező!")])
    date = DateField('Dátum', format='%Y-%m-%d', validators=[DataRequired(message="Megadása kötelező!")])
    start = TimeField('Kezdés', validators=[DataRequired(message="Megadása kötelező!")])
    duration = IntegerField('Hossz', validators=[
        DataRequired(message="Megadása kötelező!"),
        NumberRange(min=1, message="Minimum 1-nek kell lennie!")
        ])
    save = SubmitField('Felvitel')

class AddProjectWorkTimeForm(FlaskForm):
    """ Projekt feladat, munkaidő felvitel Form adatok
    
    Arguments:
        FlaskForm {Object} -- FlaskForm ősosztály
    """
    workTime = FloatField('Munkaidő (óra)', validators=[DataRequired(message="Megadása kötelező!")])
    comment = TextAreaField('Megjegyzés', validators=[DataRequired(message="Megadása kötelező!")])