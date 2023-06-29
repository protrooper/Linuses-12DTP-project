from flask import Flask, render_template, request
import sqlite3

import random




app = Flask(__name__)




def insertdata(name, countries, habitats, prey, predators):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    #--insert data

    results = cur.fetchall()
    conn.close()




#searches database for frogs which match the searched criteria
def search_frogs(country, location, prey, predator):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    cur.execute('''SELECT * FROM frogs WHERE id IN (SELECT fid FROM FrogCountry WHERE cid IN (SELECT id FROM country WHERE name LIKE ?))  
        AND id IN (SELECT fid FROM FrogHabitat WHERE hid IN (SELECT id FROM habitat WHERE name LIKE?))
        AND id IN (SELECT fid FROM FrogPrey WHERE pid IN (SELECT id FROM prey WHERE name LIKE?))
        AND id IN (SELECT fid FROM FrogPredator WHERE pid IN (SELECT id FROM predator WHERE name LIKE?))''',  ('%'+ country+'%', '%'+ location+'%', '%'+ prey+'%', '%'+ predator+'%'))
    results = cur.fetchall()
    conn.close()
    return results

@app.route('/')
def home():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    #select random frog to display
    cur.execute('SELECT id FROM frogs') #gets list of possible ids that can be used
    ids = cur.fetchall()
    randint = random.choices(ids, k=2) #selects random ids, k= number of ids selected
    id1 = randint[0]
    cur.execute('SELECT * FROM frogs WHERE id=?', id1) #select frog which matches the id
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
        sortedResults = sorted(results, key=lambda frog: frog[1]) #sorts results in alphabetical order, based on name

        return render_template("search.html", title = "search results", frogs=sortedResults)

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
        
        return render_template("explore.html", title="Explore", results=sortedResults, countries=countries, habitats = habitats, preys=preys, predators=predators)



@app.route('/all_frogs')
def all_frogs():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM frogs')
    frogs = cur.fetchall()

    sortedFrogs = sorted(frogs, key=lambda frog: frog[1]) #sort in alphabetical order
    print(sortedFrogs)

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

    return render_template("frog.html", frog = frog, country = country, prey = prey, predator = predator, habitat = habitat)

@app.route('/insert')
def insert():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    if request.method == "POST":
        data = dict(request.form)
        
        insertdata() #insert data
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
        
        return render_template("insert_data.html", title="insert_data", results=sortedResults, countries=countries, habitats = habitats, preys=preys, predators=predators)

if __name__ == "__main__": 
    app.run(debug=True)