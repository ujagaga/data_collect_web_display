#!/usr/bin/python3
import json

from flask import Flask, request, render_template, Markup, send_from_directory, g, redirect, make_response, url_for
import sys
import os
import plotly
from plotly.graph_objs import Scatter, Layout
from datetime import datetime
import time
import hashlib
import secrets
from flask_mail import Mail, Message
from app_cfg import AppConfig

if AppConfig.DB_TYPE == "mysql":
    import mysql.connector
else:
    import sqlite3

db_path = AppConfig.DB_NAME

application = Flask(__name__, static_url_path='/static', static_folder='static')
application.config.update(
    TESTING=False,
    SECRET_KEY="RandomlyGenerated_1234asdfhg3324r89u7dsfkjdsbvc",
    SERVER_NAME=AppConfig.APP_URL,
    SESSION_COOKIE_DOMAIN=AppConfig.APP_URL,
    SESSION_TYPE="redis",
    MAIL_SERVER=AppConfig.MAIL_SERVER,
    MAIL_PORT=AppConfig.MAIL_PORT,
    MAIL_USE_TLS=AppConfig.MAIL_USE_TLS,
    MAIL_USE_SSL=AppConfig.MAIL_USE_SSL,
    MAIL_USERNAME=AppConfig.MAIL_USERNAME,
    MAIL_PASSWORD=AppConfig.MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER=AppConfig.MAIL_DEFAULT_SENDER
)
mail = Mail(application)
WEB_PORT = AppConfig.WEB_PORT
COLORS = ["#000000", "#A52A2A", "#7FFFD4", "#8A2BE2", "#D2691E", "#2F4F4F", "#008000"]
color_id = 0
APP_URL = AppConfig.APP_URL


def pwd_encrypt(password):
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()


def generate_token():
    return secrets.token_urlsafe()


def query_db(db, query, args=(), one=False):
    if AppConfig.DB_TYPE == "mysql":
        cur = db
        cur.execute(query)
    else:
        cur = db.execute(query, args)

    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def exec_db(query):
    g.db.execute(query)
    if not query.startswith('SELECT'):
        if AppConfig.DB_TYPE == "mysql":
            g.connection.commit()
        else:
            g.db.commit()


@application.before_request
def before_request():
    if AppConfig.DB_TYPE == "mysql":
        g.connection = mysql.connector.connect(
            host="localhost",
            user=AppConfig.DB_USER,
            passwd=AppConfig.DB_PASS,
            database=AppConfig.DB_NAME
        )
        g.db = g.connection.cursor(buffered=True)
    else:
        if not os.path.isfile(db_path):
            # Database does not exist. Create one
            db = sqlite3.connect(db_path)

            sql = "create table data (timestamp TEXT, name TEXT, value TEXT, apikey TEXT)"
            db.execute(sql)
            db.commit()

            sql = "create table ctrl (name TEXT, value TEXT, groupby TEXT, type TEXT, apikey TEXT)"
            db.execute(sql)
            db.commit()

            sql = "create table units (name TEXT, unit TEXT, apikey TEXT)"
            db.execute(sql)
            db.commit()

            sql = "create table users (email  TEXT, pass TEXT, apikey TEXT, resetcode TEXT)"
            db.execute(sql)
            db.commit()

            db.close()

        else:
            g.db = sqlite3.connect(db_path)


@application.teardown_request
def teardown_request(exception):
    if AppConfig.DB_TYPE == "mysql":
        g.db.close()
        g.connection.close()
    else:
        if hasattr(g, 'db'):
            g.db.close()


def get_user(email=None, apikey=None):
    data = None

    if email is not None:
        sql = "SELECT * FROM users WHERE email = '{}'".format(email)
    elif apikey is not None:
        sql = "SELECT * FROM users WHERE apikey = '{}'".format(apikey)
    else:
        print("ERROR finding user with email = {}, apikey = {}.".format(email, apikey), flush=True)
        return None

    try:
        data = query_db(g.db, sql, one=True)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc), flush=True)

    return data


def set_user(email=None, apikey=None, password=None, resetcode=None):
    user = get_user(email=email, apikey=apikey)

    try:
        if user is not None:
            email = user["email"]
            if password is not None:
                sql = "UPDATE users SET pass = '{}' WHERE email = '{}'".format(password, email)
            elif resetcode is not None:
                sql = "UPDATE users SET resetcode = '{}' WHERE email = '{}'".format(resetcode, email)
            elif email is not None and apikey is not None:
                sql = "UPDATE users SET apikey = '{}' WHERE email = '{}'".format(apikey, email)
            else:
                print("ERROR: Nothing to do with user. No password or resetcode specified.", flush=True)
                return
        else:
            if email is not None:
                sql = "INSERT INTO users (email, resetcode) VALUES ('{}', '{}')".format(email, resetcode)
            else:
                print("ERROR adding user. No email specified.", flush=True)
                return

        exec_db(sql)
        user = get_user(email=email)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc), flush=True)

    return user


def clear_variables(apikey):
    try:
        sql = "DELETE FROM ctrl WHERE apikey = '{}'".format(apikey)
        exec_db(sql)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def get_variable(name, apikey):
    data = None

    try:
        sql = "SELECT * FROM ctrl WHERE name = '{}' AND apikey = '{}'".format(name, apikey)
        data = query_db(g.db, sql, one=True)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    if data is not None:
        return data.get('value', '')

    return data


def get_all_variables(access_key):
    data = None

    try:
        sql = "SELECT * FROM ctrl WHERE apikey = '{}'".format(access_key)
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


def set_variable(name, apikey, value, groupby="", var_type=""):
    try:
        data = get_variable(name, apikey)

        if data is None:
            sql = "INSERT INTO ctrl (name, value, groupby, type, apikey) VALUES ('{}', '{}', '{}', '{}', '{}')" \
                  "".format(name, value, groupby, var_type, apikey)
        else:
            sql = "UPDATE ctrl SET value = '{}' WHERE name = '{}' AND apikey = '{}'".format(value, name, apikey)
        exec_db(sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def clear_data(apikey):
    try:
        sql = "DELETE FROM data WHERE apikey = '{}'".format(apikey)
        exec_db(sql)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def save_data(apikey, name, value):
    try:
        ts = time.time()

        sql = "INSERT INTO data (timestamp, name, value, apikey) VALUES ('{}', '{}', '{}', '{}')" \
              "".format(ts, name, value, apikey)
        exec_db(sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def get_data(apikey, name=None):
    data = None

    try:
        if name is not None:
            sql = "SELECT * FROM data WHERE name = '{}' AND apikey = '{}' ORDER BY timestamp DESC".format(name, apikey)
            data = query_db(g.db, sql, one=True)
        else:
            sql = "SELECT * FROM data WHERE apikey = '{}' ORDER BY timestamp".format(apikey)
            data = query_db(g.db, sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR reading data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    return data


def set_unit(apikey, name, unit):
    try:
        sql = "DELETE FROM units WHERE name = '{}' AND apikey = '{}'".format(name, apikey)
        exec_db(sql)
        sql = "INSERT INTO units (name, unit, apikey) VALUES ('{}', '{}', '{}')".format(name, unit, apikey)
        exec_db(sql)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("ERROR writing data to db on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))


def get_units(apikey, name):
    unit = ""

    try:
        sql = "SELECT unit FROM units WHERE name = '{}' AND apikey = '{}'".format(name, apikey)
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


def send_password_reset_email(user):
    resetcode = user['resetcode']
    title = "{} Activation".format(APP_URL)

    message = "<p>You requested a new account or password reset.</p>" \
              "<p>Please click <a href=https://{}/resetpass?resetcode={}&email={}>here</a> to set new password.</p>" \
              "".format(APP_URL, resetcode, user['email'])

    msg = Message(title,  recipients=[user['email']], html=message)
    try:
        mail.send(msg)
    except Exception as e:
        print("ERROR: email setup incorrect: {}, APP config: {}".format(e, application.config), flush=True)
        return 'An error occurred while trying to send the activation email. Please contact the administrator'

    return 'An activation email was sent to your address. Please follow the link provided to set your password.'


@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@application.route('/')
def home_page():
    access_key = request.cookies.get('token')
    user = None

    if access_key is not None:
        user = get_user(apikey=access_key)

    if user is None:
        login_var = {"name": "Login", "url": "login", "icon": "fa-sign-in-alt"}
        apikey_msg = ""
        access_key = "YOUR_API_KEY"
    else:
        login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}
        apikey_msg = "API key: {}".format(user["apikey"])

    message = request.args.get('message')
    return render_template("home_page.html", dldid=int(time.time()),
                           login=login_var,
                           app_url=APP_URL,
                           message=message,
                           apikey_msg=apikey_msg,
                           apikey=access_key,
                           admin_email=AppConfig.MAIL_DEFAULT_SENDER)


@application.route('/graphs')
def graphs():
    global color_id

    color_id = 0
    access_key = request.cookies.get('token')
    user = get_user(apikey=access_key)

    if user is None:
        return redirect(url_for('login'))
    else:
        login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}

    plot_list = []

    # get latest data
    data_list = get_data(apikey=access_key)
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

    response = make_response(render_template("graphs.html", plots=plot_list, login=login_var, dldid=int(time.time())))
    return response


@application.route('/datactrl')
def data_and_controls():
    global color_id

    color_id = 0
    access_key = request.cookies.get('token')
    user = get_user(apikey=access_key)

    if user is None:
        return redirect("/login")
    else:
        login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}
        data_list = get_data(apikey=access_key)

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
                unit = get_units(apikey=access_key, name=name)

                new_list.append({"name": name, "val": data_dict[name], "unit": unit})
        vars = get_all_variables(access_key)

        response = make_response(render_template("datactrl.html", dldid=int(time.time()), vars=vars,
                                                 value_list=new_list, login=login_var, ts=last_timestamp))
        response.set_cookie('token', access_key, max_age=86400)

        return response


@application.route('/download')
def download_csv():
    access_key = request.cookies.get('token')

    data_list = get_data(apikey=access_key)
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
def postdata():
    apikey = request.args.get('key')
    user = get_user(apikey=apikey)

    if user is None:
        return "Unauthorized"

    name = request.args.get('N', None)
    value = request.args.get('V', None)
    unit = request.args.get('U', None)

    if name is not None and value is not None:
        save_data(apikey=apikey, name=name, value=value)

        if unit is not None:
            set_unit(apikey=apikey, name=name, unit=unit)

    return 'ok'


@application.route('/getdata', methods=['GET'])
def getdata():
    apikey = request.args.get('key')
    user = get_user(apikey=apikey)

    if user is None:
        return "Unauthorized"

    name = request.args.get('N', None)

    if name is not None:
        data = get_data(apikey=apikey, name=name)
        if data is not None:
            return data.get("value", '0')

    return 'none'


@application.route('/setvar', methods=['GET'])
def setvar():
    apikey = request.args.get('key')
    user = get_user(apikey=apikey)

    if user is None:
        return "Unauthorized"

    name = request.args.get('N', None)
    value = request.args.get('V', None)
    groupby = request.args.get('G', "")
    var_type = request.args.get('T', "")

    if name is not None and value is not None:
        set_variable(apikey=apikey, name=name, value=value, groupby=groupby, var_type=var_type)

    return 'ok'


@application.route('/getvar', methods=['GET'])
def getvar():
    apikey = request.args.get('key')
    user = get_user(apikey=apikey)

    if user is None:
        return "Unauthorized"

    name = request.args.get('N', None)

    if name is not None:
        var = get_variable(name=name, apikey=apikey)
        if var is not None:
            return var

    return 'none'


@application.route('/json', methods=['GET'])
def get_json():
    access_key = request.args.get('apikey')

    vars = get_all_variables(access_key)

    # get latest data ordered by timestamp
    data_list = get_data(apikey=access_key)
    result_list = []
    if data_list is not None:
        data_dict = {}

        for data in data_list:
            name = data["name"]
            data_dict[name] = data

        for key in data_dict.keys():
            result_list.append(data_dict[key])

    result_dict = {"variables": vars, "data": result_list}
    return json.dumps(result_dict)


@application.route('/cleardata', methods=['GET'])
def cleardata():
    access_key = request.cookies.get('token')
    user = get_user(apikey=access_key)

    if user is not None:
        clear_data(access_key)

    return redirect(url_for("data_and_controls"))


@application.route('/clearvars', methods=['GET'])
def clearvars():
    access_key = request.cookies.get('token')
    user = get_user(apikey=access_key)

    if user is not None:
        clear_variables(access_key)

    return redirect(url_for("data_and_controls"))


@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", '')
        password = request.form.get("password", '')
        encrypted = pwd_encrypt(password)

        user = get_user(username)

        if user is not None and encrypted == user["pass"]:
            response = make_response(redirect("/"))
            response.set_cookie('token', user["apikey"], max_age=86400)
            return response
        else:
            message = "ERROR: Wrong e-mail or password"
    else:
        message = request.args.get("message", "")

    response = make_response(render_template('login.html', message=message))
    return response


@application.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get("email", '')
        request_type = request.form.get("type", 'register')
        if email != '':
            resetcode = generate_token()

            if request_type == 'register':
                user = set_user(email=email, resetcode=resetcode)
            else:
                # Reset requested. Check if the user exists
                user = get_user(email)
                if user is not None:
                    user = set_user(email=email, resetcode=resetcode)

            if user is not None:
                status_msg = send_password_reset_email(user)
            else:
                status_msg = "There was an error sending the email. The requested user was not found in our database."

            return redirect(url_for('home_page', message=status_msg))
    else:
        forgot_password = request.args.get('resetpass', 'no')

        if forgot_password == 'yes':
            title = "Reset Password"
            request_type = "reset"
            message = "Please provide your email address, so we can send you the reset link."
        else:
            title = "Register"
            request_type = "register"
            message = "Please provide your email address. It will be used only to send you the activation link " \
                      "or to reset password.<br>There will be no spam or news from this service."

        response = make_response(render_template('new_account.html',
                                                 message=message,
                                                 title=title,
                                                 request_type=request_type))
        return response


@application.route('/resetpass', methods=['GET'])
def resetpass():
    resetcode = request.args.get('resetcode', '')
    email = request.args.get('email', '')

    if email != "" and resetcode != "":
        user = get_user(email=email)
        if user is not None and user["resetcode"] == resetcode:
            apikey = user["apikey"]
            if apikey is None or len(apikey) < 16:
                apikey = generate_token()
                set_user(email, apikey)

            return redirect(url_for('activate', apikey=apikey))

    status_msg = "An error occurred while setting your password. Are you sure you followed the right link?"
    return redirect(url_for('home_page', message=status_msg))


@application.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect("/"))
    response.set_cookie('token', '', max_age=0)
    return response


@application.route('/activate', methods=['GET', 'POST'])
def activate():
    if request.method == 'POST':
        password = request.form.get("password1", '')
        apikey = request.form.get("apikey", '')

        user = get_user(apikey=apikey)
        if user is not None and len(password) > 5:
            encrypted = pwd_encrypt(password)
            set_user(apikey=apikey, password=encrypted)
            status_msg = "Password set successfully. You may now login with the new password."
        else:
            status_msg = "An error occurred while setting your password. {} | {} | {}".format(password, user, apikey)

        return redirect(url_for('home_page', message=status_msg))
    else:
        login_var = {"name": "Login", "url": "login", "icon": "fa-sign-in-alt"}
        apikey = request.args.get('apikey')
        response = make_response(render_template('activate_confirmation_page.html',
                                                 apikey=apikey,
                                                 login=login_var,
                                                 admin_email=AppConfig.MAIL_DEFAULT_SENDER))
        return response


if __name__ == '__main__':
    application.run(host="0.0.0.0", port=WEB_PORT, debug=True)
