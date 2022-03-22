#!/usr/bin/python3

from flask import Flask, request, render_template, Markup, send_from_directory, g, redirect, make_response
import sys
import os
import sqlite3
import plotly
from plotly.graph_objs import Scatter, Layout
from datetime import datetime, timedelta
import time
import json

application = Flask(__name__, static_url_path='/static', static_folder='static')
application.secret_key = "<g\x93E\xf3\xc6\xb8\xc4\x87\xff\xf6\x0fxD\x91\x13\x9e\xfe1+%\xa3"
db_path = "database.db"
WEB_PORT = 8000
ADMIN_USERNAME = "smart"
ADMIN_PASS = "smart123"
ADMIN_KEY = "SmartHorti123"     # An HTML safe string
COLORS = ["#000000", "#A52A2A", "#7FFFD4", "#8A2BE2", "#D2691E", "#2F4F4F", "#008000"]
color_id = 0


def init_database():
    if not os.path.isfile(db_path):
        # Database does not exist. Create one
        db = sqlite3.connect(db_path)

        sql = "create table data (timestamp TEXT, name TEXT, value TEXT)"
        db.execute(sql)
        db.commit()

        sql = "create table ctrl (name TEXT, value TEXT, groupby TEXT, type TEXT, " \
              "scheduletime TEXT, hour TEXT, duration TEXT, repeat TEXT, active TEXT, tz TEXT)"
        db.execute(sql)
        db.commit()

        sql = "create table units (name TEXT, unit TEXT)"
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
        var_type = data["type"]
        sch_time = data["scheduletime"]
        if (var_type == "toggle") and (sch_time is not None) and (int(data["active"]) > 0):
            sch_timestamp = int(sch_time)
            current_timestamp = int(time.time())
            duration = int(data["duration"]) * 60
            data["value"] = '0'

            if current_timestamp > sch_timestamp:
                time_diff = current_timestamp - sch_timestamp
                repeat = int(data["repeat"])

                if repeat > 0:
                    time_diff = time_diff % (24 * 60 * 60)

                if time_diff < duration:
                    data["value"] = '1'

        return data.get('value', '')

    return data


def get_all_variables():
    data = None

    try:
        sql = "SELECT * FROM ctrl"
        data = query_db(g.db, sql)

        items = {}
        for item in data:
            var_type = item["type"]
            sch_time = item["scheduletime"]
            if (var_type == "toggle") and (sch_time is not None) and (int(item["active"]) > 0):
                sch_timestamp = int(sch_time)
                current_timestamp = int(time.time())
                duration = int(item["duration"]) * 60
                item["value"] = '0'

                if current_timestamp > sch_timestamp:
                    time_diff = current_timestamp - sch_timestamp
                    repeat = int(item["repeat"])

                    if repeat > 0:
                        time_diff = time_diff % (24 * 60 * 60)

                    if time_diff < duration:
                        item["value"] = '1'

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


def set_schedule(name, hour, duration, repeat, activate_time, active, tz_delta):
    try:
        sql = "UPDATE ctrl SET scheduletime = '{}', hour = '{}', duration = '{}', repeat = '{}', active = '{}', " \
              "tz_delta = '{}' WHERE name = '{}'".format(activate_time, hour, duration, repeat, active, tz_delta, name)
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
    return render_template("home_page.html", dldid=int(time.time()), login=login_var)


@application.route('/about')
def about_page():
    access_key = request.cookies.get('token')
    if ADMIN_KEY != access_key:
        login_var = {"name": "Login", "url": "login", "icon": "fa-sign-in-alt"}
    else:
        login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}

    return render_template("about.html", dldid=int(time.time()), login=login_var)


@application.route('/graphs')
def graphs():
    global color_id

    color_id = 0
    access_key = request.cookies.get('token')
    if ADMIN_KEY != access_key:
        return redirect("/login")
    
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
    
    login_var = {"name": "Logout", "url": "logout", "icon": "fa-sign-out-alt"}
    data_list = get_data()

    if len(data_list) > 0:
        last_timestamp = int(float(data_list[-1]['timestamp']))
        if time.time() - last_timestamp > 25:
            status = "Disconnected"
        else:
            status = "Connected"
    else:
        last_timestamp = "No data available"
        status = "Disconnected"

    new_list = []
    if data_list is not None:
        data_dict = {}

        for data in data_list:
            name = data["name"]
            
            if status == "Disconnected":
                data_dict[name] = "unknown"
            else:
                data_dict[name] = data["value"]

        for name in data_dict.keys():
            if status == "Disconnected":
                unit = ""
            else:
                unit = get_units(name)

            new_list.append({"name": name, "val": data_dict[name], "unit": unit})
    vars = get_all_variables()

    response = make_response(render_template("datactrl.html", dldid=int(time.time()), vars=vars,
                                             value_list=new_list, login=login_var, ts=last_timestamp, status=status))
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


@application.route('/setvarschedule', methods=['GET'])
def set_var_schedule():
    access_key = request.args.get('key', ' ')

    if ADMIN_KEY != access_key:
        return redirect("/login")

    value = request.args.get('V', None)
    if value is not None:
        try:
            data = json.loads(value)

            local_time = data.get("t", "").split(":")
            local_h = int(local_time[0])
            local_m = int(local_time[1])

            server_time = datetime.now()
            server_h = server_time.hour
            server_m = server_time.minute
            activate_date = datetime.now().replace(hour=local_h, minute=local_m)
            tz_delta = ((local_h - server_h) * 60 + (local_m - server_m)) * 60

            h = int(data.get("h", local_h))
            if h < local_h:
                # Add 24h to set for tomorrow
                activate_date = activate_date + timedelta(hours=24)
                activate_date = activate_date.replace(hour=h)

            activate_timestamp = int(datetime.timestamp(activate_date)) - tz_delta

            active = int(data.get("a", "0"))
            if h < 0:
                active = 0

            duration = int(data.get("d", "-1"))
            if int(data.get("r", "0")) == 0:
                repeat = 0
            else:
                repeat = 1
            name = data.get("n", "")
            set_schedule(name=name, hour=h, duration=duration, repeat=repeat, activate_time=activate_timestamp,
                         active=active, tz_delta=tz_delta)

        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("ERROR using data on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

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


@application.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect("/"))
    response.set_cookie('token', '', max_age=0)
    return response


if __name__ == '__main__':
    application.run(host="0.0.0.0", port=WEB_PORT, debug=True)
