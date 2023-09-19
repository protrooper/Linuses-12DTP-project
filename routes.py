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
        # checks if query[1] index exists,
        #  -thefourtheye https://stackoverflow.com/questions/29715501/how-can-i-check-if-a-list-index-exists
        try:
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
def insertdata(name, sci_name, min_size, max_size, status, image,
               description, countries, habitats, preys, predators):

    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    # insert data
    cur.execute('SELECT * FROM statuses WHERE name =?', (status,))
    if cur.fetchone() is None:
        cur.execute('INSERT INTO statuses (name) VALUES(?)', (status,))
        conn.commit()

    cur.execute('''
                INSERT INTO frogs (name, scientific_name, min_size, max_size, image, description, status)
                VALUES (?, ?, ?, ?, ?, ?, (SELECT id FROM statuses WHERE name =?))
                ''',
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
    # make sure there is no duplicate data,
    #   Denis Otkidach- https://stackoverflow.com/questions/1541797/how-do-i-check-if-there-are-duplicates-in-a-flat-list
    items = set(data)
    for item in items:
        # check if data exists in table
        cur.execute(f'SELECT * FROM {tableName} WHERE name =?', (item,))
        if cur.fetchone() is None:
            # if data doesn't exist, add data to table
            cur.execute(f'INSERT INTO {tableName} (name) VALUES (?)', (item,))

        cur.execute(f'INSERT INTO {jointTable} (fid, {id}) VALUES ((SELECT id FROM frogs WHERE name =?), \
                    (SELECT id FROM {tableName} WHERE name=?))', (frogName, item))


# searches database for frogs which match the searched criteria, takes parameters from form.
def search_frogs(country, location, prey, predator, status):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    cur.execute('''
                SELECT * FROM frogs WHERE id IN
                (SELECT fid FROM FrogCountry WHERE cid IN (SELECT id FROM country WHERE name LIKE ?))
                AND id IN (SELECT fid FROM FrogHabitat WHERE hid IN (SELECT id FROM habitat WHERE name LIKE?))
                AND id IN (SELECT fid FROM FrogPrey WHERE pid IN (SELECT id FROM prey WHERE name LIKE?))
                AND id IN (SELECT fid FROM FrogPredator WHERE pid IN (SELECT id FROM predator WHERE name LIKE?))
                AND id IN (SELECT id FROM frogs WHERE status IN(SELECT id FROM statuses WHERE name LIKE?))
                ''',
                ('%'+country+'%', '%'+location+'%', '%'+prey+'%', '%'+predator+'%', '%'+status+'%'))

    results = cur.fetchall()
    conn.close()
    return results


# gets any number of random frogs(depending on parameter)
def get_random_frog(number: int):
    conn = sqlite3.connect('frog.db')
    cur = conn.cursor()

    # Select random frog IDs to display
    cur.execute('SELECT id FROM frogs')   # gets list of possible ids that can be used
    ids = cur.fetchall()
    random_ids = random.sample(ids, k=number)   # selects random ids, k= number of ids selected

    # make string that goes into sql query, number of parameters = length of random_ids
    parameters = ', '.join(['?'] * len(random_ids))

    cur.execute(f'SELECT * FROM frogs WHERE id IN ({parameters})', [id[0] for id in random_ids])
    frogs = cur.fetchall()

    conn.close()
    return frogs


# makes a unqiue filename incase there are images have the same name
# https://stackoverflow.com/questions/52497605/how-do-i-rename-a-file-if-it-already-exists-in-python
def make_unique_filename(filename):
    # splits filename into base and extension
    base, filext = os.path.splitext(filename)
    counter = 1
    
    while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        filename = f"{base}_{counter}{filext}"
        counter += 1

    return filename


# home page
@app.route('/')
def home():
    frog_count = fetch_data([['SELECT COUNT(*) FROM frogs']], [True])
    return render_template("home.html", title="Home", frog_count=frog_count[0][0][0])


# contact page, displays contact information
@app.route('/contact')
def contact():
    return render_template("contact.html", title="contact")


# about page
@app.route('/about')
def about():
    return render_template("about.html", title="about")


# allows user to search for frogs which match a specific criteria
@app.route('/explore', methods=['GET', 'POST'])
def explore():
    if request.method == "POST":
        data = dict(request.form)

        frogs = search_frogs(data['country'], data['habitat'], data['prey'], data['predator'], data['statuses'])
        sort_key = request.form.get('sort_key')

        return render_template("search.html", title="search results",
                               frogs=frogs, sort_key=sort_key, formData=data)

    else:
        frogs = get_random_frog(3)
        sortedResults = []
        queries = [['SELECT * FROM country'],
                   ['SELECT * FROM habitat'],
                   ['SELECT * FROM prey'],
                   ['SELECT * FROM predator'],
                   ['SELECT * FROM statuses']]
        fetchall = [True, True, True, True, True]
        countries, habitats, preys, predators, statuses = fetch_data(queries, fetchall)

        return render_template("explore.html",
                               title="Explore", frogs=frogs,
                               results=sortedResults, countries=countries,
                               habitats=habitats, preys=preys,
                               predators=predators, statuses=statuses)


# displays all the frogs in a 3x3 grid, sorted by name, scientific name or size via sort_key
@app.route('/all_frogs', methods=['GET', 'POST'])
def all_frogs():
    if request.method == "POST":
        sort_key = request.form.get('sort_key')
    else:
        sort_key = '1'   # default sort_key
    queries = [['SELECT * FROM frogs']]
    frogs = fetch_data(queries, [True])
    return render_template("all_frogs.html", frogs=frogs[0], sort_key=sort_key)


# displays information for one specific frog
@app.route('/frog/<int:id>')
def frog(id):
    try:
        queries = [['SELECT * FROM frogs WHERE id=?', (id,)],
                   ['SELECT * FROM statuses WHERE id IN(SELECT status FROM frogs WHERE id =?)', (id,)],
                   ['SELECT * FROM country WHERE id IN(SELECT cid FROM FrogCountry WHERE fid =?)', (id,)],
                   ['SELECT * FROM prey WHERE id IN(SELECT pid FROM FrogPrey WHERE fid =?)', (id,)],
                   ['SELECT * FROM predator WHERE id IN(SELECT pid FROM FrogPredator WHERE fid =?)', (id,)],
                   ['SELECT * FROM habitat WHERE id IN(SELECT hid FROM FrogHabitat WHERE fid =?)', (id,)]]
        fetchall = [False, False, True, True, True, True, True]
        frog, status, country, prey, predator, habitat = fetch_data(queries, fetchall)
        if frog is None:    # page doesn't exist!
            return render_template("success.html", title="404", status="404", reason="Page not found")
        else:
            return render_template("frog.html",
                                   frog=frog, status=status,
                                   country=country, prey=prey,
                                   predator=predator, habitat=habitat)
    except OverflowError:
        return render_template("success.html", title="404", status="404", reason="Page not found")


# allows user to insert data into database
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
        image = request.files['image']
        # make sure filename can be safely stored, and doesn't break the system.
        filename = secure_filename(image.filename)
        unique_filename = make_unique_filename(filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        # save image to file
        image.save(path)

        status = ""
        reason = ""

        # validates image file,
        # https://stackoverflow.com/questions/889333/how-to-check-if-a-file-is-a-valid-image-file
        try:
            queries = [['SELECT * FROM frogs WHERE name =?', (request.form.get('name'),)],
                       ['SELECT * FROM frogs WHERE scientific_name =?', (request.form.get('scientificName'),)]]
            fetchall = [False, False]
            name, scientificName = fetch_data(queries, fetchall)

            # resizes image, solution by tomvon
            # https://stackoverflow.com/questions/273946/how-do-i-resize-an-image-using-pil-and-maintain-its-aspect-ratio
            basewidth = 500
            im = Image.open(path)
            wpercent = (basewidth/float(im.size[0]))
            hsize = int((float(im.size[1])*float(wpercent)))
            im = im.resize((basewidth, hsize), resample=Image.BICUBIC)
            im.save(path)

            if name is None and scientificName is None:
                # frog does not exist currently, insert data into database
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
                status = "Fail"
                reason = "Name or Scientific Name already exists!"
                print("name or scientific name already exists")

        except IOError:
            # image is invalid
            status = "Fail"
            reason = "Invalid Image"
            print("invalid image")

        if status == "Fail":
            im.close()
            os.remove(path)

        return render_template("success.html", title=status, status=status, reason=reason)

    else:
        return render_template("insert_data.html", title="insert_data",
                               frogs=frogs, statuses=statuses,
                               countries=countries, habitats=habitats,
                               preys=preys, predators=predators)


# 404 page, user is redirected to this page when URL does not exist
@app.errorhandler(404)
def page_not_found(e):
    return render_template("success.html", title="404", status="404", reason="Page not found")


if __name__ == "__main__":
    app.run(debug=True)
