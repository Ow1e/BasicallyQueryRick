from flask import Flask, redirect, url_for, session, render_template, request
from flask.templating import render_template_string
from flask_sqlalchemy import SQLAlchemy, _BoundDeclarativeMeta
from datetime import datetime
import qrcode.image.svg, os
import json

app = Flask(__name__)
app.secret_key = b'SECRET'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

URL = "https://basiclyqr.xyz"

db = SQLAlchemy(app)

class Places(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(50), nullable=False)
    place_group = db.Column(db.String(50), nullable=False)
    place_location = db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    # Function to create string
    def __repr__(self): 
        return f"Place('{self.place}', '{self.place_group}', '{self.place_location}', '{self.date_created}')"

class People(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.Integer, nullable=False, default=0)
    browser = db.Column(db.String(50), nullable=False)
    browser_version = db.Column(db.String(50), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return f"Person('{self.browser}', '{self.place}', '{self.browser_version}', '{self.platform}', '{self.date_created}')"

@app.route("/")
def index():
    # For debug and stats later print(f"{request.user_agent.browser} Version {request.user_agent.version} on {request.user_agent.platform}  /  {request.user_agent.string}")
    return render_template("index.html")

@app.route("/go/<place>/")
def apply(place):
    if session.get(place, False)!=True:
        session[place] = True
        if Places.query.get(place)!=None:
            new_person = People(browser=request.user_agent.browser, browser_version=request.user_agent.version, platform=request.user_agent.platform, place=place)
        else:
            new_person = People(browser=request.user_agent.browser, browser_version=request.user_agent.version, platform=request.user_agent.platform, place=0)
        try:
            db.session.add(new_person)
            db.session.commit()
        except:
            pass

        place_query = Places.query.get(place)
        if place_query==None:
            return render_template("redirect.html", redirect="/redirect", title="BasiclyQR")
        else:
            return render_template("redirect.html", redirect="/redirect", title=place_query.place)
    else:
        return redirect(url_for('.index'))

@app.route("/stats/<id>/", methods=['GET', 'POST'])
def stats(id = None):
    if id!=None:
        front = People.query.filter_by(place=id).order_by(People.id.desc()).limit(10).all()
        statistics = People.query.filter_by(place=id).all()
        url = URL+"/go/{}/".format(id)
        cqr = "/qrcode/{}.svg".format(id)
        cqr_desc = 'You can also create custom QR Codes!'
        return render_template("panel.html", data=front, rolls=len(statistics), url=url, cqr=cqr, cqr_desc=cqr_desc)
    else:
        return redirect(url_for("stats_alone"))

@app.route("/stats/", methods=['GET', 'POST'])
def stats_alone():
    front = People.query.order_by(People.id.desc()).limit(10).all()
    statistics = People.query.all()
    url = URL+"/create/"
    cqr = "/static/mainqr.svg"
    cqr_desc = "This QR Code is for creating a qr code and not a rickroll, we think"
    return render_template("panel.html", data=front, rolls=len(statistics), url=url, cqr=cqr, cqr_desc=cqr_desc)


@app.route("/stats/go/create/")
def stats_create(): # Redirects
    return redirect(url_for("create"))

@app.route("/stats/<nothing>/create/")
def stats_create_dynamic(nothing): # Redirects
    return redirect(url_for("create"))

@app.route("/create/", methods=['GET', 'POST'])
def create():
    return render_template("create.html")

@app.route("/createqr", methods=['GET', 'POST'])
def create_qr():
    if request.method == "POST":
        place_name = request.form['name']
        place_location = request.form['location']
        place_group = request.form['group']
        if place_group!=None:
            new_place = Places(place=place_name, place_location=place_location, place_group=place_group)
        else:
            new_place = Places(place=place_name, place_location=place_location, place_group="Default")
        try:
            db.session.add(new_place)
            db.session.commit()
            id = new_place.id
            return render_template("redirect.html", redirect=f"/stats/{id}/", title="BasiclyQueryRick")
        except Exception as e:
            print(e)
            return render_template("error.html", code="503 Tantrum", description="You made our SQLAlchemy Database go crazy! Try next time becuse its most likely your fault", icon="fa-layer-group"), 404
    else:
        return url_for("index")

@app.route("/redirect/")
def rick():
    return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

@app.route("/qrcode/<int:id>.svg")
def generate_code(id = 0):
    destination = f"static/qrcodes/{id}.svg"
    max =  len(Places.query.all())
    if max>=id:
        if not os.path.exists(destination):
            print("Creating QR Code for {}".format(id))
            url = URL+"/go/{}/".format(id)
            factory = qrcode.image.svg.SvgPathImage
            save_svg = qrcode.make(url, image_factory = factory)
            save_svg.save(destination)
        else:
            pass
        return redirect(url_for('static', filename=f'qrcodes/{id}.svg'))
    else:
        return render_template("error.html", code="403 We arent your mom!", description="Go create your own qr code dont use us!", icon="fa-bolt"), 403

@app.route("/redirecttest/")
def redirect_test():
    return render_template("redirect.html", redirect="#")

@app.route("/error/")
def error_test():
    return render_template("error.html", code="403 Forbidden", description="Sorry but your not in the cool kids club. This place is for developers only!", icon="fa-layer-group"), 403

@app.route("/orphan/")
def orphan():
    return render_template("error.html", code="Why", description="", icon="fa-question"), 404

@app.errorhandler(404)
def error_404(e):
    return render_template("error.html", code="404 Unknown", description="This sadly does not exist :(", icon="fa-question"), 404

@app.errorhandler(500)
def error_unknown(e):
     return render_template("error.html", code="500", description="Uhhhh wat", icon="fa-bomb"), 500

# API
@app.route("/api/")
def api_redirect():
    return redirect("https://github.com/thecodeavenger/BasiclyQueryRick/wiki/API")

@app.route("/api/user/query/all/")
def index_all_users():
    product = []
    for i in People.query.all():
        product.append({
            "id": i.id,
            "date": str(i.date_created),
            "place": i.place,
            "browser": {
                "name": i.browser,
                "version": i.browser_version,
                "platform": i.platform
            }
        })
    return json.dumps(product)

@app.route("/api/user/query/<id>/")
def index_specific_users(id):
    product = []
    for i in People.query.filter_by(place=id).all():
        product.append({
            "id": i.id,
            "date": str(i.date_created),
            "place": i.place,
            "browser": {
                "name": i.browser,
                "version": i.browser_version,
                "platform": i.platform
            }
        })
    return json.dumps(product)

@app.route("/api/user/query/group/<id>/")
def index_grouped_users(id):
    product = []
    for i in Places.query.all():
        if i.place_group == id:
            product.append(i.id)
    return json.dumps(product)

@app.route("/api/user/<id>/")
def index_specific_user(id):
    product = []
    for i in People.query.filter_by(id=id).all():
        product.append({
            "id": i.id,
            "date": str(i.date_created),
            "place": i.place,
            "browser": {
                "name": i.browser,
                "version": i.browser_version,
                "platform": i.platform
            }
        })
    return json.dumps(product)

@app.route("/api/location/query/all/")
def index_all_locations():
    product = []
    for i in Places.query.all():
        product.append({
            "id": i.id,
            "name": i.place,
            "group": i.place_group,
            "location": i.place_location,
            "date": str(i.date_created)
        })
    return json.dumps(product)

@app.route("/api/location/query/<id>/")
def index_specific_location(id):
    product = []
    for i in Places.query.filter_by(id=id).all():
        product.append({
            "id": i.id,
            "name": i.place,
            "group": i.place_group,
            "location": i.place_location,
            "date": str(i.date_created)
        })
    return json.dumps(product)

if __name__ == '__main__':
    app.run(host="0.0.0.0")