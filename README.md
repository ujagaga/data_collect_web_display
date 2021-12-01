# Data collector web UI #

Python Flask simple data collector service. Deploy it anywhere and go to url or IP address like 


    http://localhost:8000?key=AdminSecretKey123


The key can be changed at the top of the "main.py" file, just look for "ADMIN_KEY". 
To post new data go to:


     http://localhost:8000/postdata?key=AdminSecretKey123&N=data_name&V=data_value

     e.g. http://localhost:8000/postdata?key=AdminSecretKey123&N=Temperature&V=25.4
          http://localhost:8000/postdata?key=AdminSecretKey123&N=Humidity&V=30


You can use any HTML safe data_name and value. The timestamp will be automatically updated according to current time.
After posting few samples, you will be able to view a graphical display on the front page.


## TODO ##

1. Add data that can be used to controll devices (not timestamped and only one instance of each data name).
2. Add delete button so a data set can be cleared.

## Contact ##

* web: http://www.radinaradionica.com
* email: ujagaga@gmail.com

