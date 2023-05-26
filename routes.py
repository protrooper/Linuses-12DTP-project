from flask import Flask, render_template, request
import sqlite3

import random




app = Flask(__name__)





#searches database for frogs which match the searched country
def getcountries(search):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM frogs WHERE id IN (SELECT fid FROM FrogCountry WHERE cid IN (SELECT id FROM country WHERE name LIKE ?))', ('%'+ search+'%',))
    results = cur.fetchall()
    conn.close()
    return results



@app.route('/')
def home():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(id) FROM frogs')
    count = cur.fetchone()
    randomId = random.randint(1, count[0])
    cur.execute('SELECT * FROM frogs WHERE id=?', (randomId,))
    frog = cur.fetchone()
    return render_template("home.html", title = "Home", frog=frog)
    

@app.route('/contact')
def contact():
    return render_template("contact.html", title = "contact")


@app.route('/about')
def about():
    return render_template("about.html", title = "about")



@app.route('/locations', methods=['GET', 'POST'])
def locations():
    if request.method == "POST":
        data = dict(request.form)
        print(data['search'])
        results = getcountries(data['search'])
        sortedResults = sorted(results, key=lambda frog: frog[1]) 
        return render_template("search.html", title = "search results", frogs=sortedResults)
    else:
        sortedResults = []
        conn = sqlite3.connect('frog.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM country')
        countries = cur.fetchall()
        return render_template("locations.html", title = "Location", results = sortedResults, countries=countries)

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