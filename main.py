import time, random, threading
from flask import Flask, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from SQLAlchemy import select
from flask_bcrypt import Bcrypt
from turbo_flask import Turbo
from forms import RegistrationForm, EmailForm
from audio import printWAV

app = Flask(__name__)
app.config['SECRET_KEY'] = '37be8d614b721cbab4a9c00ca3717ddf'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

interval=10
FILE_NAME = "mcl1.wav"
turbo = Turbo(app)

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(60), nullable=False)

  def __repr__(self):
    return f"User('{self.username}', '{self.email}')"

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', subtitle='Home Page', 
                           text='This is the home page')

@app.route("/captions")
def captions():
    TITLE = "doug demuro mclaren"
    return render_template('captions.html', songName=TITLE, file=FILE_NAME)
  
@app.before_first_request
def before_first_request():
    #resetting time stamp file to 0
    file = open("pos.txt","w") 
    file.write(str(0))
    file.close()

    #starting thread that will time updates
    threading.Thread(target=update_captions).start()

@app.context_processor
def inject_load():
    # getting previous time stamp
    file = open("pos.txt","r")
    pos = int(file.read())
    file.close()

    # writing next time stamp
    file = open("pos.txt","w")
    file.write(str(pos+interval))
    file.close()

    #returning captions
    return {'caption':printWAV(FILE_NAME, pos=pos, clip=interval)}

def update_captions():
    with app.app_context():
        while True:
            # timing thread waiting for the interval
            time.sleep(interval)

            # forcefully updating captionsPane with caption
            turbo.push(turbo.replace(render_template('captionsPane.html'), 'load'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit(): # checks if entries are valid
        user = User(username=form.username.data, email=form.email.data, 
                    password=bcrypt.generate_password_hash(form.password.data).decode('utf-8'))
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('register.html', title='Register', form=form)

@app.route("/find_email")
def find_email():
    form = EmailForm()
    if form.validate_on_submit():
        stmt = select(db).where(db.username == form.username.data)
        result = session.execute(stmt)
        for user_obj in result.scalars():
            if(bcrypt.check_password_hash(user_obj.password, form.password.data)):
                flash(f'The email associated with this account is {user_obj.email}', 'success')
                return redirect(url_for('home'))
            else:
                flash('Incorrect password', 'error')
                return redirect(url_for('home'))
    return render_template('find_email.html', title='Find Email', form=form)
  
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")