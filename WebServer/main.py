#!/usr/bin/python3

from flask import Flask, request, render_template, Markup, send_from_directory, g, redirect, make_response, flash
import sys
import os
import sqlite3
import plotly
from plotly.graph_objs import Scatter, Layout
from datetime import datetime
import time
import hashlib
import secrets
from flask_mail import Mail, Message


application = Flask(__name__, static_url_path='/static', static_folder='static')
application.config.update(
    TESTING=False,
    SECRET_KEY="123DataCollectorSecretKey131313",
    SERVER_NAME="datacollect.ohanacode-dev.com",
    SESSION_COOKIE_DOMAIN="datacollect.ohanacode-dev.com",
    SESSION_TYPE="redis",
    MAIL_SERVER="mail.ohanacode-dev.com",
    MAIL_PORT=26,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=False,
    MAIL_USERNAME="rada.berar@ohanacode-dev.com",
    MAIL_PASSWORD="prokletamasina13",
    MAIL_DEFAULT_SENDER="rada.berar@ohanacode-dev.com"
)
mail = Mail(application)
db_path = "database.db"
WEB_PORT = 8000
ADMIN_USERNAME = "admin"
ADMIN_PASS = "admin123"
ADMIN_KEY = "AdminSecretKey123"     # An HTML safe string
COLORS = ["#000000", "#A52A2A", "#7FFFD4", "#8A2BE2", "#D2691E", "#2F4F4F", "#008000"]
color_id = 0
APP_URL = "ohanacodedata.com"


def pwd_encrypt(password):
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()


def generate_token():
    return secrets.token_urlsafe()


def send_email(to, message, title="Data collector service"):
    msg = Message(title,
                  recipients=[to],
                  html=message)

    mail.send(msg)


def init_database():
    if not os.path.isfile(db_path):
        # Database does not exist. Create one
        db = sqlite3.connect(db_path)

        sql = "create table data (timestamp TEXT, name TEXT, value TEXT, userid int)"
        db.execute(sql)
        db.commit()

        sql = "create table ctrl (name TEXT, value TEXT, groupby TEXT, type TEXT, userid int)"
        db.execute(sql)
        db.commit()

        sql = "create table units (name TEXT, unit TEXT)"
        db.execute(sql)
        db.commit()

        sql = "create table users (id int NOT NULL AUTO_INCREMENT, email TEXT, pass TEXT, apikey TEXT, resetcode TEXT)"
        db.execute(sql)
        db.commit()

        db.close()


def query_db(db, query, args=(), one=False):
    cur = db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def exec_db(query):
    g.db.execute(query)
    if not query.startswith('SELECT'):
        g.db.commit()


@application.before_request
def before_request():
    if not os.path.isfile(db_path):
        init_database()

    g.db = sqlite3.connect(db_path)


@application.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def get_user(email=None, apikey=None):
    data = None

    if email is not None:
        sql = "SELECT * FROM users WHERE email = '{}'".format(email)
    elif apikey is not None:
        sql = "SELECT * FROM users WHERE apikey = '{}'".format(apikey)
    else:
        print("ERROR finding user with email = {}, apikey = {}.".format(email, apikey))
        return None

    try:
        data = query_db(g.db, sql, one=True)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    return data


def set_user(email=None, apikey=None, password=None, resetcode=None):
    user = get_user(email=email, apikey=apikey)

    try:
        if user is not None:
            email = user["email"]
            if password is not None:
                sql = "UPDATE users SET password = '{}' WHERE email = '{}'".format(password, email)
            elif resetcode is not None:
                sql = "UPDATE users SET resetcode = '{}' WHERE email = '{}'".format(resetcode, email)
            else:
                print("ERROR: Nothing to do with user. No password or resetcode specified.")
                return
        else:
            if email is not None:
                # Adding a new user. Generate resetcode to enable password set.
                resetcode = generate_token()
                sql = "INSERT INTO users (email, resetcode) VALUES ('{}', '{}')".format(email, resetcode)
            else:
                print("ERROR adding user. No email specified.")
                return

        exec_db(sql)
        user = get_user(email=email)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    return user


def clear_variables():
    try:
        sql = "DELETE FROM ctrl"
        exec_db(sql)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def get_variable(name):
    data = None

    try:
        sql = "SELECT * FROM ctrl WHERE name = '{}'".format(name)
        data = query_db(g.db, sql, one=True)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    if data is not None:
        return data.get('value', '')

    return data


def get_all_variables():
    data = None

    try:
        sql = "SELECT * FROM ctrl"
        data = query_db(g.db, sql)

        items = {}
        for item in data:
            group = item["groupby"]
            item_list = items.get(group, [])
            item_list.append(item)
            items[group] = item_list

        data = items

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    return data


def set_variable(name, value, groupby="", var_type=""):
    try:
        data = get_variable(name)

        if data is None:
            sql = "INSERT INTO ctrl (name, value, groupby, type) VALUES ('{}', '{}', '{}', '{}')" \
                  "".format(name, value, groupby, var_type)
        else:
            sql = "UPDATE ctrl SET value = '{}' WHERE name = '{}'".format(value, name)
        exec_db(sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def clear_data():
    try:
        sql = "DELETE FROM data"
        exec_db(sql)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def save_data(name, value):
    try:
        ts = time.time()

        sql = "INSERT INTO data (timestamp, name, value) VALUES ('{}', '{}', '{}')" \
              "".format(ts, name, value)
        exec_db(sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def get_data(name=None):
    data = None

    try:
        if name is not None:
            sql = "SELECT * FROM data WHERE name = '{}' ORDER BY timestamp DESC".format(name)
            data = query_db(g.db, sql, one=True)
        else:
            sql = "SELECT * FROM data ORDER BY timestamp"
            data = query_db(g.db, sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    return data


def set_unit(name, unit):
    try:
        sql = "DELETE FROM units WHERE name = '{}'".format(name)
        exec_db(sql)
        sql = "INSERT INTO units (name, unit) VALUES ('{}', '{}')".format(name, unit)
        exec_db(sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def get_units(name):
    unit = ""

    try:
        sql = "SELECT unit FROM units WHERE name = '{}'".format(name)
        data = query_db(g.db, sql, one=True)

        if data is None:
            # Override if none is set
            if "temperature" in name.lower():
                unit = "°C"
            elif "moisture" in name.lower():
                unit = "%"
            elif "humidity" in name.lower():
                unit = "%"
        else:
            unit = data["unit"]

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    return unit


def create_plot(plot_title, data):
    global color_id

    plot_color = COLORS[color_id]

    dataDictionary = {
        "X": [],
        "Y": []
    }

    for x in data:
        dataDictionary["X"].append(x[0])
        dataDictionary["Y"].append(x[1])

    plot = plotly.offline.plot({
        "data": [Scatter(x=dataDictionary["X"], y=dataDictionary["Y"], line=dict(color=plot_color, width=2))],
        "layout": Layout(title=plot_title, height=800, margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ))
    }, output_type='div'
    )

    # Prepare next color for next graph
    color_id += 1
    if color_id >= len(COLORS):
        color_id = 0

    return plot


def send_activation_email(user):
    return 'An activation email was sent to your address. Please follow the link provided to set your password.'


@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@application.route('/')
def home_page():
    access_key = request.cookies.get('token')
    if ADMIN_KEY != access_key:
        login_var = {"name": "Login", "url": "login", "icon": "fa-sign-in-alt"}
    else:
        login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}
    return render_template("home_page.html", dldid=int(time.time()), login=login_var, app_url=APP_URL)


@application.route('/graphs')
def graphs():
    global color_id

    color_id = 0
    access_key = request.cookies.get('token')
    if ADMIN_KEY != access_key:
        login_var = {"name": "Login", "url": "login", "icon": "fa-sign-in-alt"}
        authorized = False
    else:
        login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}
        authorized = True

    plot_list = []

    # get latest data
    data_list = get_data()
    if data_list is not None:
        data_dict = {}

        for data in data_list:
            timestamp = datetime.fromtimestamp(int(data["timestamp"].split('.')[0]))
            name = data["name"]
            value = float(data["value"])
            year = datetime.strftime(timestamp, '%Y')
            month = datetime.strftime(timestamp, '%B')
            day_time = datetime.strftime(timestamp, '%d, %H:%M:%S')

            name_data = data_dict.get(name, {})
            year_data = name_data.get(year, {})
            month_data = year_data.get(month, [])
            month_data.append([day_time, value])
            year_data[month] = month_data
            name_data[year] = year_data
            data_dict[name] = name_data

        for name in data_dict:
            name_data = data_dict[name]
            for year in name_data.keys():
                year_data = name_data[year]
                for month in year_data.keys():
                    month_data = year_data[month]
                    plot_title = "{} {}, {}".format(name, month, year)
                    plot = create_plot("", month_data)
                    plot_html = Markup(plot)
                    plot_data = {"date": year + "." + month, "plot": plot_html, "title": plot_title}
                    plot_list.append(plot_data)

    response = make_response(render_template("graphs.html", plots=plot_list, login=login_var, auth=authorized,
                                             dldid=int(time.time())))

    return response


@application.route('/datactrl')
def data_and_controls():
    global color_id

    color_id = 0
    access_key = request.cookies.get('token')

    if ADMIN_KEY != access_key:
        return redirect("/login")
    else:
        login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}
        data_list = get_data()

        if len(data_list) > 0:
            last_timestamp = int(float(data_list[-1]['timestamp']) * 1000)
        else:
            last_timestamp = "No data available"

        new_list = []
        if data_list is not None:
            data_dict = {}

            for data in data_list:
                name = data["name"]
                data_dict[name] = data["value"]

            for name in data_dict.keys():
                unit = get_units(name)

                new_list.append({"name": name, "val": data_dict[name], "unit": unit})
        vars = get_all_variables()

        response = make_response(render_template("datactrl.html", dldid=int(time.time()), vars=vars,
                                                 value_list=new_list, login=login_var, ts=last_timestamp))
        response.set_cookie('token', ADMIN_KEY, max_age=1200)

        return response


@application.route('/download')
def download_csv():
    data_list = get_data()
    if data_list is not None:
        data_dict = {}
        for data in data_list:
            timestamp = datetime.fromtimestamp(int(data["timestamp"].split('.')[0]))
            name = data["name"]
            value = float(data["value"])
            date = datetime.strftime(timestamp, '%Y/%b/%d %H:%M:%S')
            name_data = data_dict.get(name, [])
            name_data.append([date, value])
            data_dict[name] = name_data

        f = open("/tmp/data.csv", 'w')
        for name in data_dict.keys():
            f.write("{} date, value\n".format(name))
            value = data_dict[name]
            for data in value:
                f.write("{}, {}\n".format(data[0], data[1]))
            f.write("\n\n")

        f.close()

    return send_from_directory('/tmp', 'data.csv')


@application.route('/postdata', methods=['GET'])
def post_data():
    access_key = request.args.get('key', ' ')

    if ADMIN_KEY != access_key:
        return "Unauthorized"

    name = request.args.get('N', None)
    value = request.args.get('V', None)
    unit = request.args.get('U', None)

    if name is not None and value is not None:
        save_data(name, value)

        if unit is not None:
            set_unit(name, unit)

    return 'ok'


@application.route('/setvar', methods=['GET'])
def set_var():
    access_key = request.args.get('key', ' ')

    if ADMIN_KEY != access_key:
        return redirect("/login")

    name = request.args.get('N', None)
    value = request.args.get('V', None)
    groupby = request.args.get('G', "")
    var_type = request.args.get('T', "")

    if name is not None and value is not None:
        set_variable(name, value, groupby, var_type)

    return 'ok'


@application.route('/getvar', methods=['GET'])
def get_var():
    access_key = request.args.get('key', ' ')

    if ADMIN_KEY != access_key:
        return redirect("/login")

    name = request.args.get('N', None)

    if name is not None:
        var = get_variable(name)
        if var is not None:
            return var

    return 'none'


@application.route('/cleardata', methods=['GET'])
def cleardata():
    access_key = request.cookies.get('token')

    if ADMIN_KEY == access_key:
        clear_data()

    return redirect("/")


@application.route('/clearvars', methods=['GET'])
def clearvars():
    access_key = request.cookies.get('token')

    if ADMIN_KEY == access_key:
        clear_variables()

    return redirect("/")


@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", '')
        password = request.form.get("password", '')
        if password == ADMIN_PASS and username == ADMIN_USERNAME:
            response = make_response(redirect("/"))
            response.set_cookie('token', ADMIN_KEY, max_age=1200)
            return response
        else:
            message = "Login or password incorrect"
    else:
        message = request.args.get("message")

    response = make_response(render_template('login.html', message=message))
    return response


@application.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get("email", '')
        if email != '':
            user = set_user(email=email)
            if user is not None:
                status_msg = send_activation_email(user)
                flash(status_msg)
            response = make_response(redirect("/"))
            return response

    response = make_response(render_template('new_account.html'))
    return response


@application.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect("/"))
    response.set_cookie('token', '', max_age=0)
    return response


if __name__ == '__main__':
    application.run(host="0.0.0.0", port=WEB_PORT, debug=True)
