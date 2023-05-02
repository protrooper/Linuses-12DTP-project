from flask import Flask, render_template
import sqlite3


app = Flask(__name__)


@app.route('/')
def home():
    return render_template("home.html", title = "Home")


@app.route('/contact')
def contact():
    return render_template("contact.html", title = "contact")


@app.route('/about')
def about():
    return render_template("about.html", title = "about")


@app.route('/all_frogs')
def all_frogs():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM frogs')
    frogs = cur.fetchall()
    return render_template("all_frogs.html", frogs=frogs)

@app.route('/frog/<int:id>')
def frog(id):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM frogs WHERE id=?', (id,))
    frog = cur.fetchone()
    cur.execute('SELECT * FROM country WHERE id IN(SELECT cid FROM FrogCountry WHERE fid =?)', (id,))
    country = cur.fetchall()
    #cur.execute('SELECT * FROM country WHERE id =?', (countryid[1],))
    #country = cur.fetchall()
    return render_template("frog.html", frog = frog, country = country)
if __name__ == "__main__":  
    app.run(debug=True)