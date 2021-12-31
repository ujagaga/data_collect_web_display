# Data collector web UI #

Python Flask simple data collector service. Initially intended for uploading data from embedded projects like Arduino boards, ESP8266, ESP32,... 
Normally you can have sensor data like Temperature, Humidity, Moisture,... These will be displayed as graphic functions.
The other type of data are controll variables used to switch relays ON/OFF, so they are displayed as buttons.

## How to start ##
Istall Flask and plotly


    pip install Flask, plotly


Deploy it anywhere and go to url or IP address like 


    http://localhost:8000


Check the "templates" folder and adjust the html for your pages.
The page "Data & Controlls" is protected by login credentials which can be changed at the top of the "main.py" file, just look for "ADMIN_USERNAME" and "ADMIN_PASS". 
To post new data, you will need the administration key. Find it next to login credentials as "ADMIN_KEY", then go to:


     http://localhost:8000/postdata?key=AdminSecretKey123&N=data_name&V=data_value&U=data_unit

     e.g. http://localhost:8000/postdata?key=AdminSecretKey123&N=Temperature&V=25.4&U=°C
          http://localhost:8000/postdata?key=AdminSecretKey123&N=Humidity&V=30&U=%


You can use any HTML safe data_name and value. The timestamp will be automatically updated according to current time.
After posting few samples, you will be able to view a graphical display on the "Graphs" page.

To set a control variable go to "/setvar" page. Also make sure you have the correct access key like:


    http://localhost:8000/setvar?key=AdminSecretKey123&N=var_name&V=var_value&G=my_group&T=var_type


As you can see from above example, a control variable can have the following attributes:
    N ... name
    V ... value
    G ... group to use to group multiple variables
    T ... type of the variable. The only supported type is "toggle". 
            If toggle type is set, the variable will be displayed with a toggle button. If omitted, it will be displayed with a value.
            
To retrieve a control variable value, go to "/getvar" page like:


    http://localhost:8000/getvar?key=AdminSecretKey123&N=var_name


## Sample urls

    http://localhost:8000/postdata?key=AdminSecretKey123&N=Temperature&V=24&U=°C
    http://localhost:8000/postdata?key=AdminSecretKey123&N=Temperature&V=25
    http://localhost:8000/postdata?key=AdminSecretKey123&N=Temperature&V=26
    
    http://localhost:8000/setvar?key=AdminSecretKey123&N=Automatic mode activate&V=1&G=Automatic Mode&T=toggle
    http://localhost:8000/setvar?key=AdminSecretKey123&N=Minimum moisture&V=30&G=Automatic Mode
    http://localhost:8000/setvar?key=AdminSecretKey123&N=Maximum moisture&V=30&G=Automatic Mode
    http://localhost:8000/setvar?key=AdminSecretKey123&N=Water ON&V=30&G=Manual Mode&T=toggle
    http://localhost:8000/setvar?key=AdminSecretKey123&N=Drip System&V=30&G=Manual Mode&T=toggle
    http://localhost:8000/setvar?key=AdminSecretKey123&N=Sprinkler System&V=30&G=Manual Mode&T=toggle


    To use these links on an application deployed to a hosting service, just replace "http://localhost:8000" with your website url.


## Heroku Deployment ##

To deploy this app on Heroku, create an account and follow their python deployment tutorial or steps outlined below.

1. Install git and prepare your git repository.
2. Install Heroku CLI 
        - For windows download from: https://devcenter.heroku.com/articles/heroku-cli
        - on Ubuntu: sudo snap install heroku --classic).
3. Open a console window.
4. Clone your git repository: 

        git clone git@github.com:ujagaga/data_collect_web_display.git

Alternatively navigate to already cloned repository.

5. Login to Heroku by running:

        heroku login

6. Create your app:

        heroku create <my_app_name>

7. Push your app from custom branch to Heroku main branch

        git push heroku <git_branch_name>:main

8. Open your app via url: 

        https://<my_app_name>.herokuapp.com

   or via CLI: 

        heroku open


## Additional Heroku CLI quick reference ##

To list available apps:

        heroku apps:list

To delete an app:

        heroku apps:destroy <app_name>


## Contact ##

* web: http://www.radinaradionica.com
* email: ujagaga@gmail.com

