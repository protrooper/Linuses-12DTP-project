from flask import Flask, render_template, request
import sqlite3
import random
import os
from werkzeug.utils import secure_filename
from PIL import Image
# where uploaded images go
UPLOAD_FOLDER = 'static/images'


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# executes a query/multiple queries
# parameters:
#       queries (list): a list of list/s containing the SQL queries and their parameters
#       fetchall (list): a list of bool values which determine whether the fetchall is used or not

def fetch_data(queries: list, fetchall: list):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()
    results = []

    for index, query in enumerate(queries):
        try:                                                 # checks if query[1] index exists, thefourtheye - https://stackoverflow.com/questions/29715501/how-can-i-check-if-a-list-index-exists
            cur.execute(query[0], query[1])
        except IndexError:
            cur.execute(query[0])

        if fetchall[index] is True:
            result = cur.fetchall()
        else:
            result = cur.fetchone()
        results.append(result)

    conn.close()
    return results


# inserts data into database, takes parameters from form
def insertdata(name, sci_name, min_size, max_size, status, image, description, countries, habitats, preys, predators):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    # insert data
    cur.execute('SELECT * FROM statuses WHERE name =?', (status,))
    if cur.fetchone() is None:
        cur.execute('INSERT INTO statuses (name) VALUES(?)', (status,))
        conn.commit()

    cur.execute('''INSERT INTO frogs (name, scientific_name, min_size, max_size, image, description, status)
                   VALUES (?, ?, ?, ?, ?, ?, (SELECT id FROM statuses WHERE name =?))''',
                (name, sci_name, min_size, max_size, image, description, status))
    conn.commit()

    insert_into(countries, name, 'country', 'FrogCountry', 'cid', cur)
    insert_into(habitats, name, 'habitat', 'FrogHabitat', 'hid', cur)
    insert_into(preys, name, 'prey', 'FrogPrey', 'pid', cur)
    insert_into(predators, name, 'predator', 'FrogPredator', 'pid', cur)

    conn.commit()
    conn.close()


# for inserting data into tables which contain foreign keys.
# parameters:
#       data(list): data to be inserted
#       frogName(str): name of frog
#       tableName(str): name of table new data is inserted into 
#       jointTable(str): table where id of frog is matched with id of data from tableName
#       id(str): name of column in joinTable which is to be matched with fid.
#       cur: cursor for executing queries

def insert_into(data, frogName, tableName, jointTable, id, cur):
    items = set(data)                      # make sure there is no duplicate data,  Denis Otkidach- https://stackoverflow.com/questions/1541797/how-do-i-check-if-there-are-duplicates-in-a-flat-list
    for item in items:
        # check if data exists in table
        cur.execute(f'SELECT * FROM {tableName} WHERE name =?', (item,))
        if cur.fetchone() is None:
            # if data doesn't exist, add data to table
            cur.execute(f'INSERT INTO {tableName} (name) VALUES (?)', (item,))
        cur.execute(f'INSERT INTO {jointTable} (fid, {id}) VALUES ((SELECT id FROM frogs WHERE name =?), (SELECT id FROM {tableName} WHERE name=?))', (frogName, item))


# searches database for frogs which match the searched criteria, takes parameters from form.
def search_frogs(country, location, prey, predator, status):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    cur.execute('''SELECT * FROM frogs WHERE id IN (SELECT fid FROM FrogCountry WHERE cid IN (SELECT id FROM country WHERE name LIKE ?))
        AND id IN (SELECT fid FROM FrogHabitat WHERE hid IN (SELECT id FROM habitat WHERE name LIKE?))
        AND id IN (SELECT fid FROM FrogPrey WHERE pid IN (SELECT id FROM prey WHERE name LIKE?))
        AND id IN (SELECT fid FROM FrogPredator WHERE pid IN (SELECT id FROM predator WHERE name LIKE?))
        AND id IN (SELECT id FROM frogs WHERE status IN(SELECT id FROM statuses WHERE name LIKE?))''',
        ('%'+ country+'%', '%'+ location+'%', '%'+ prey+'%', '%'+ predator+'%', '%'+status+'%'))

    results = cur.fetchall()
    conn.close()
    return results


@app.route('/')
def home():
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    # select random frog to display
    cur.execute('SELECT id FROM frogs')   # gets list of possible ids that can be used
    ids = cur.fetchall()
    randint = random.sample(ids, k=3)   # selects random ids, k= number of ids selected
    
    id1, id2, id3 = randint
    print(id1[0], id2[0], id3[0])
    cur.execute('SELECT * FROM frogs WHERE id=? OR id=? OR id=? ', (id1[0], id2[0], id3[0]))   # select frog which matches the id
    frogs = cur.fetchall()

    conn.close()

    return render_template("home.html", title="Home", frogs=frogs)


@app.route('/contact')
def contact():
    return render_template("contact.html", title="contact")


@app.route('/about')
def about():
    return render_template("about.html", title="about")


@app.route('/explore', methods=['GET', 'POST'])
def explore():
    if request.method == "POST":
        data = dict(request.form)

        results = search_frogs(data['country'], data['habitat'], data['prey'], data['predator'], data['statuses'])
        sortedResults = sorted(results, key=lambda frog: frog[1])  # sorts results in alphabetical order, based on name

        return render_template("search.html", title="search results", frogs=sortedResults)

    else:
        sortedResults = []
        queries = [['SELECT * FROM country'],
                   ['SELECT * FROM habitat'],
                   ['SELECT * FROM prey'],
                   ['SELECT * FROM predator'],
                   ['SELECT * FROM statuses']]
        fetchall = [True, True, True, True, True]
        countries, habitats, preys, predators, statuses = fetch_data(queries, fetchall)

        return render_template("explore.html", title="Explore", results=sortedResults, countries=countries, habitats=habitats, preys=preys, predators=predators, statuses=statuses)


@app.route('/all_frogs')
def all_frogs():
    queries = [['SELECT * FROM frogs ORDER BY name']]
    frogs = fetch_data(queries, [True])
    return render_template("all_frogs.html", frogs=frogs[0])


@app.route('/frog/<int:id>')
def frog(id):
    queries = [['SELECT * FROM frogs WHERE id=?', (id,)],
               ['SELECT * FROM statuses WHERE id IN(SELECT status FROM frogs WHERE id =?)', (id,)],
               ['SELECT * FROM country WHERE id IN(SELECT cid FROM FrogCountry WHERE fid =?)', (id,)],
               ['SELECT * FROM prey WHERE id IN(SELECT pid FROM FrogPrey WHERE fid =?)', (id,)],
               ['SELECT * FROM predator WHERE id IN(SELECT pid FROM FrogPredator WHERE fid =?)', (id,)],
               ['SELECT * FROM habitat WHERE id IN(SELECT hid FROM FrogHabitat WHERE fid =?)', (id,)]]
    fetchall = [False, False, True, True, True, True, True]
    frog, status, country, prey, predator, habitat = fetch_data(queries, fetchall)

    return render_template("frog.html", frog=frog, status=status, country=country, prey=prey, predator=predator, habitat=habitat)


@app.route('/insert', methods=['GET', 'POST'])
def insert():
    queries = [['SELECT * FROM frogs'],
               ['SELECT * FROM statuses'],
               ['SELECT * FROM country'],
               ['SELECT * FROM habitat'],
               ['SELECT * FROM prey'],
               ['SELECT * FROM predator']]
    fetchall = [True, True, True, True, True, True]
    frogs, statuses, countries, habitats, preys, predators = fetch_data(queries, fetchall)

    if request.method == "POST":

        # save image to file
        image = request.files['image']
        filename = secure_filename(image.filename)     # makes sure filename can be safely stored, and doesn't break the system.
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(path)

        status = ""
        reason = ""

        # validates image file, https://stackoverflow.com/questions/889333/how-to-check-if-a-file-is-a-valid-image-file
        try:
            queries = [['SELECT * FROM frogs WHERE name =?', (request.form.get('name'),)],
                       ['SELECT * FROM frogs WHERE scientific_name =?', (request.form.get('scientificName'),)]]
            fetchall = [False, False]
            name, scientificName = fetch_data(queries, fetchall)

            im = Image.open(path)

            if name is None and scientificName is None:
                # insert data into database
                insertdata(request.form.get('name'),
                           request.form.get('scientificName'),
                           request.form.get('min_size'),
                           request.form.get('max_size'),
                           request.form.get('status'),
                           path,
                           request.form.get('description'),
                           request.form.getlist('country'),
                           request.form.getlist('habitat'),
                           request.form.getlist('prey'),
                           request.form.getlist('predator'))
                status = "success"
                im.close()
            else:
                status = "fail"
                reason = "Name or Scientific Name already exists!"
                print("name or scientific name already exists")
            
        except IOError:
            # image is invalid
            status = "fail"
            reason = "Invalid Image"
            print("invalid image")

        if status == "fail":
            im.close()
            os.remove(path)


        return render_template("success.html", title=status, status=status, reason=reason)

    else:
        return render_template("insert_data.html", title="insert_data", frogs=frogs, statuses=statuses, countries=countries, habitats=habitats, preys=preys, predators=predators)


if __name__ == "__main__":
    app.run(debug=True)
