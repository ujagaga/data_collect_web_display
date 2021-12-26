#include <ESP8266WiFi.h>
#include <DHT.h>    // Install DHT11 Library and Adafruit Unified Sensor Library
#include <ESP8266HTTPClient.h>
#include "config.h"

#define DHTPIN                      (2)    
#define LED_PIN                     (14)  
#define SPRINKLER_RELAY_PIN         (12)
#define DRIP_RELAY_PIN              (15)
#define MOISTURE_SENSOR_PIN         (A0)

// Controll variable names
#define MIN_MOIST_VAR               "Minimum%20Moisture"
#define MAX_MOIST_VAR               "Maximum%20Moisture"
#define AUTOMATIC_VAR               "Automatic%20Mode"
#define SPRINKLER_VAR               "Sprinkler%20System"
#define DRIP_VAR                    "Drip%20System"

#define SENSOR_READ_TIMEOUT         (5)     // Read sensors every 5 seconds

#define DHTTYPE    DHT11

DHT dht(DHTPIN, DHTTYPE);
HTTPClient http;
float minPercentage = 20; // Adjust for minimum percentage under which the relay is activated
float maxPercentage = 90;

// Variables to store sensor values
float h = 0;
float t = 0;
float f = 0;
float percentage = 0;

unsigned long cycle_timestamp = 0;
bool relayAutomaticMode = false;
bool sprinklerSystemOn = false;
bool dripSystemOn = false;


String do_http_get_request(String url){
  String result = "Error: No wifi connection.";
  
  if (WiFi.status() == WL_CONNECTED) { //Check WiFi connection status 
    HTTPClient http;  //Declare an object of class HTTPClient   
    
    http.begin(url); 
    int httpCode = http.GET();  
 
    if (httpCode > 0) { //Check the returning code
      String result = http.getString();
    }
 
    http.end();   //Close connection  
  }
}

/* Reads sensors and stores values in global variables to make them available in every function */
void read_sensors(){
  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  t = dht.readTemperature();
  // Read temperature as Fahrenheit (isFahrenheit = true)
  f = dht.readTemperature(true);

  int moi = 1024-analogRead(MOISTURE_SENSOR_PIN); 
  percentage = map(moi,0,1023,0,100);
}


void send_data(){
  String url = "";
  String result = "";
  String baseSetUrl = String(WEB_SERVICE_ADDRESS) + "postdata?key=" + String(ADMIN_KEY);

  // Set temperature
  url = baseSetUrl + "&N=Temperature&V=" + String(t);
  Serial.print("Setting temperature: ");  
  result = do_http_get_request(url);
  Serial.println(result);
  
  // Set humidity
  url = baseSetUrl + "&N=Humidity&V=" + String(h);
  Serial.print("Setting humidity: ");  
  result = do_http_get_request(url);
  Serial.println(result);

  // Set moisture
  url = baseSetUrl + "&N=Moisture&V=" + String(percentage);
  Serial.print("Setting moisture: ");  
  result = do_http_get_request(url);
  Serial.println(result);
}


void read_data(){
  String url = "";
  String result = "";
  String baseGetUrl = String(WEB_SERVICE_ADDRESS) + "getvar?key=" + String(ADMIN_KEY) + "&N=";
  String baseSetUrl = String(WEB_SERVICE_ADDRESS) + "setvar?key=" + String(ADMIN_KEY);

  // get minimum moisture and set it if unset
  url = baseGetUrl + String(MIN_MOIST_VAR);
  Serial.print("Fetching minimum moisture level: ");  
  result = do_http_get_request(url);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Minimum moisture percentage not set. Setting initial value:");
    url = baseSetUrl + "&G=Automatic%20Mode&N=" + String(MIN_MOIST_VAR) + "&V=" + String(minPercentage);
    result = do_http_get_request(url);
    Serial.println(result);
  }else{
    minPercentage = result.toFloat();
  }  
  
  // get maximum moisture and set it if unset
  url = baseGetUrl + String(MAX_MOIST_VAR);
  Serial.print("Fetching maximum moisture level: ");  
  result = do_http_get_request(url);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Maximum moisture percentage not set. Setting initial value:");
    url = baseSetUrl + "&G=Automatic%20Mode&" + String(MAX_MOIST_VAR) + "&V=" + String(maxPercentage);
    result = do_http_get_request(url);
    Serial.println(result);
  }else{
    maxPercentage = result.toFloat();
  }  
  
  // get automatic mode and set it if unset
  url = baseGetUrl + String(AUTOMATIC_VAR);
  Serial.print("Fetching automatic mode setting: ");  
  result = do_http_get_request(url);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Automatic mode not set. Setting initial value:");
    url = baseSetUrl + "&G=Automatic%20Mode&T=toggle&N=" + String(AUTOMATIC_VAR) + "&V=" + String(int(relayAutomaticMode));
    result = do_http_get_request(url);
    Serial.println(result);
  }else{
    relayAutomaticMode = bool(result.toInt());
  } 
  
  // get sprinkler system and set it if unset 
  url = baseGetUrl + String(SPRINKLER_VAR);
  Serial.print("Fetching sprinkler system setting: ");  
  result = do_http_get_request(url);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Sprinkler system value not set. Setting initial value:");
    url = baseSetUrl + "&G=Manual%20Mode&T=toggle&N=" + String(SPRINKLER_VAR) + "&V=" + String(int(sprinklerSystemOn));
    result = do_http_get_request(url);
    Serial.println(result);
  }else{
    sprinklerSystemOn = bool(result.toInt());
  } 
  
  // get drip system and set it if unset 
  url = baseGetUrl + String(DRIP_VAR);
  Serial.print("Fetching sprinkler system setting: ");  
  result = do_http_get_request(url);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Sprinkler system value not set. Setting initial value:");
    url = baseSetUrl + "&G=Manual%20Mode&T=toggle&N=" + String(DRIP_VAR) + "&V=" + String(int(dripSystemOn));
    result = do_http_get_request(url);
    Serial.println(result);
  }else{
    dripSystemOn = bool(result.toInt());
  } 
}


void process_settings(){
  if(relayAutomaticMode){
    if(percentage < minPercentage){
      digitalWrite(SPRINKLER_RELAY_PIN, HIGH);
      digitalWrite(DRIP_RELAY_PIN, HIGH);
    }else if(percentage > maxPercentage){
      digitalWrite(SPRINKLER_RELAY_PIN, LOW);
      digitalWrite(DRIP_RELAY_PIN, LOW);
    }
  }else{
    if(sprinklerSystemOn){
      digitalWrite(SPRINKLER_RELAY_PIN, HIGH);
    }else{
      digitalWrite(SPRINKLER_RELAY_PIN, LOW);
    }

    if(dripSystemOn){
      digitalWrite(DRIP_RELAY_PIN, HIGH);
    }else{
      digitalWrite(DRIP_RELAY_PIN, LOW);
    }
  }
}


void setup()
{

  Serial.begin(9600);

  dht.begin();
  pinMode(LED_PIN, OUTPUT);
  pinMode(SPRINKLER_RELAY_PIN, OUTPUT);
  pinMode(DRIP_RELAY_PIN, OUTPUT);
  pinMode(MOISTURE_SENSOR_PIN, INPUT);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(300);
  }
  Serial.println();
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());
  Serial.println();
}

void loop() {

  if((millis() - cycle_timestamp) > (SENSOR_READ_TIMEOUT * 1000)){
    read_sensors();
    send_data();
    read_data();
    process_settings();
    cycle_timestamp = millis();
  }
}
