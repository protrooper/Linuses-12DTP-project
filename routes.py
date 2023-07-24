from flask import Flask, render_template, request
import sqlite3

import random

app = Flask(__name__)


#inserts data into database, takes parameters from form
def insertdata(name, image, description, countries, habitats, preys, predators):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    picture = ''.join(["/static/images/", image])
    #--insert data
    cur.execute('INSERT INTO frogs (name, image, description) VALUES (?, ?, ?)', (name, picture, description,))
    conn.commit()
    for country in countries:
        cur.execute('INSERT INTO FrogCountry (fid, cid) VALUES ((SELECT id FROM frogs WHERE name =?), (SELECT id FROM country WHERE name=?))', (name, country))
    for habitat in habitats:
        cur.execute('INSERT INTO FrogHabitat (fid, hid) VALUES ((SELECT id FROM frogs WHERE name =?), (SELECT id FROM habitat WHERE name=?))', (name, habitat))
    for prey in preys:
        cur.execute('INSERT INTO FrogPrey (fid, pid) VALUES ((SELECT id FROM frogs WHERE name =?), (SELECT id FROM prey WHERE name=?))', (name, prey))
    for predator in predators:
        cur.execute('INSERT INTO FrogPredator (fid, pid) VALUES ((SELECT id FROM frogs WHERE name =?), (SELECT id FROM predator WHERE name=?))', (name, predator))
    conn.commit()
    conn.close()


#searches database for frogs which match the searched criteria, takes parameters from form.
def search_frogs(country, location, prey, predator):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    cur.execute('''SELECT * FROM frogs WHERE id IN (SELECT fid FROM FrogCountry WHERE cid IN (SELECT id FROM country WHERE name LIKE ?))  
        AND id IN (SELECT fid FROM FrogHabitat WHERE hid IN (SELECT id FROM habitat WHERE name LIKE?))
        AND id IN (SELECT fid FROM FrogPrey WHERE pid IN (SELECT id FROM prey WHERE name LIKE?))
        AND id IN (SELECT fid FROM FrogPredator WHERE pid IN (SELECT id FROM predator WHERE name LIKE?))''',  
        ('%'+ country+'%', '%'+ location+'%', '%'+ prey+'%', '%'+ predator+'%'))

    results = cur.fetchall()
    conn.close()
    return results


@app.route('/')
def home():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    #select random frog to display
    cur.execute('SELECT id FROM frogs')   #gets list of possible ids that can be used
    ids = cur.fetchall()
    randint = random.choices(ids, k=2)   #selects random ids, k= number of ids selected
    id1 = randint[0]
    cur.execute('SELECT * FROM frogs WHERE id=?', id1)   #select frog which matches the id
    frog1 = cur.fetchone()

    conn.close()

    return render_template("home.html", title = "Home", frog=frog1)
    

@app.route('/contact')
def contact():
    return render_template("contact.html", title = "contact")


@app.route('/about')
def about():
    return render_template("about.html", title = "about")


@app.route('/explore', methods=['GET', 'POST'])
def explore():
    if request.method == "POST":
        data = dict(request.form)
        
        results = search_frogs(data['search'], data['habitat'], data['prey'], data['predator'])
        sortedResults = sorted(results, key=lambda frog: frog[1])  #sorts results in alphabetical order, based on name

        return render_template("search.html", title="search results", frogs=sortedResults)

    else:
        sortedResults = []
        conn = sqlite3.connect('frog.db')
        cur = conn.cursor()

        cur.execute('SELECT * FROM country')
        countries = cur.fetchall()

        cur.execute('SELECT * FROM habitat')
        habitats = cur.fetchall()

        cur.execute('SELECT * FROM prey')
        preys = cur.fetchall()

        cur.execute('SELECT * FROM predator')
        predators = cur.fetchall()

        conn.close()
        
        return render_template("explore.html", title="Explore", results=sortedResults, countries=countries, habitats=habitats, preys=preys, predators=predators)


@app.route('/all_frogs')
def all_frogs():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM frogs')
    frogs = cur.fetchall()

    sortedFrogs = sorted(frogs, key=lambda frog: frog[1])  #sort in alphabetical order

    conn.close()

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

    conn.close()

    return render_template("frog.html", frog=frog, country=country, prey=prey, predator=predator, habitat=habitat)


@app.route('/insert', methods=['GET', 'POST'])
def insert():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM frogs')
    frogs = cur.fetchall()

    cur.execute('SELECT * FROM country')
    countries = cur.fetchall()

    cur.execute('SELECT * FROM habitat')
    habitats = cur.fetchall()

    cur.execute('SELECT * FROM prey')
    preys = cur.fetchall()

    cur.execute('SELECT * FROM predator')
    predators = cur.fetchall()

    conn.close() 

    if request.method == "POST":
        print(request.form.get('name'), request.form.get('description'), request.form.getlist('country'), 
        request.form.getlist('habitat'), request.form.getlist('prey'), request.form.getlist('predator'))

        insertdata(request.form.get('name'), request.form.get('image'), request.form.get('description'), request.form.getlist('country'), request.form.getlist('habitat'), request.form.getlist('prey'), request.form.getlist('predator'))

    return render_template("insert_data.html", title="insert_data", frogs=frogs, countries=countries, habitats=habitats, preys=preys, predators=predators)


if __name__ == "__main__": 
    app.run(debug=True)