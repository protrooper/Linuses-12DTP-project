from flask import Flask, render_template
import sqlite3

#import stuff for flask forms
from flask_bootstrap import Bootstrap5

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length




app = Flask(__name__)



import secrets
foo = secrets.token_urlsafe

app.secret_key = foo

bootstrap = Bootstrap5(app)

crsf = CSRFProtect(app)

#we will use this form to search for a name
class NameForm(FlaskForm):
    name = StringField('what country?', validators=[DataRequired(), Length(10, 40)])
    submit = SubmitField('Submit')

@app.route('/')
def home():
    return render_template("home.html", title = "Home")


@app.route('/contact')
def contact():
    return render_template("contact.html", title = "contact")


@app.route('/about')
def about():
    return render_template("about.html", title = "about")



@app.route('/locations', methods=['GET', 'POST'])
def locations():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    cur.execute('SELECT name FROM country')
    name = cur.fetchall()
    form = NameForm()

    return render_template("locations.html", title = "Location", form=form)

@app.route('/all_frogs')
def all_frogs():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM frogs')
    frogs = cur.fetchall()

    sortedFrogs = sorted(frogs, key=lambda frog: frog[1]) 
    print(sortedFrogs)
    return render_template("all_frogs.html", frogs=sortedFrogs)

@app.route('/frog/<int:id>')
def frog(id):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM frogs WHERE id=?', (id,))
    frog = cur.fetchone()

    cur.execute('SELECT * FROM country WHERE id IN(SELECT cid FROM FrogCountry WHERE fid =?)', (id,))
    country = cur.fetchall()

    cur.execute('SELECT * FROM prey WHERE id IN(SELECT pid FROM FrogPrey WHERE fid =?)', (id,))
    prey = cur.fetchall()

    cur.execute('SELECT * FROM predator WHERE id IN(SELECT pid FROM FrogPredator WHERE fid =?)', (id,))
    predator = cur.fetchall()

    cur.execute('SELECT * FROM habitat WHERE id IN(SELECT hid FROM FrogHabitat WHERE fid =?)', (id,))
    habitat = cur.fetchall()

    return render_template("frog.html", frog = frog, country = country, prey = prey, predator = predator, habitat = habitat)

if __name__ == "__main__": 
    app.run(debug=True)