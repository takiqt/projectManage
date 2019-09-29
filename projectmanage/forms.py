from flask_wtf import FlaskForm
from wtforms import Form, StringField, DateField, IntegerField, SelectField, TextAreaField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms.ext.sqlalchemy.fields import QuerySelectField

class RegisterFrom(FlaskForm):
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
    email    = StringField('E-mail',
                            validators=[
                                DataRequired(message="Megadása kötelező!"), 
                                Email(message="Érvényes e-mail címnek kell lennie!")
                            ])
    password = PasswordField('Jelszó', 
                            validators=[
                                DataRequired(message="Megadása kötelező!"), 
                                Length(min=6, max=12, message="Mező hosszának 6 és 12 karakter között kell lennie!")
                            ])
    confirmPassword = PasswordField('Jelszó megerősítése', 
                            validators=[
                                DataRequired(message="Megadása kötelező!"), 
                                Length(min=6, max=12, message="Mező hosszának 6 és 12 karakter között kell lennie!"), 
                                EqualTo('password', message="Jelszóval egyeznie kell!")
                            ]) 
    save = SubmitField('Felvitel')

class LoginForm(FlaskForm):
    userName = StringField('Felhasználó név', 
                            validators=[DataRequired()])    
    password = PasswordField('Jelszó', 
                            validators=[DataRequired()])
    remember = BooleanField('Bejelentkezve maradok')
    login = SubmitField('Bejelentkezés')

class AddProjectForm(FlaskForm):
    name = StringField('Projekt név', 
                validators=[
                    DataRequired(message="Megadása kötelező!"), 
                    Length(min=10, max=50, message="Mező hosszának 10 és 50 karakter között kell lennie!")
                ]) 
    description = TextAreaField('Leírás', validators=[DataRequired(message="Megadása kötelező!")])
    dateStart = DateField('Kezdő dátum', format='%Y-%m-%d', validators=[DataRequired(message="Megadása kötelező!")])
    dateEnd = DateField('Végző dátum', format='%Y-%m-%d', validators=[DataRequired(message="Megadása kötelező!")])    
    save = SubmitField('Felvitel')

class AddProjectWorker(FlaskForm):
    users = QuerySelectField('Felhasználó hozzáadása', allow_blank=False, get_label='fullName')
    save = SubmitField('Felvitel')

class AddProjectLeader(FlaskForm):
    users = QuerySelectField('Felhasználó hozzáadása', allow_blank=False, get_label='fullName')
    save = SubmitField('Felvitel')