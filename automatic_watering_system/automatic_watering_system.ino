#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include "config.h"
#include "DFRobot_SHT20.h"

#define LED_PIN                     (14)  
#define SPRINKLER_RELAY_PIN         (12)
#define DRIP_RELAY_PIN              (15)
#define MOISTURE_SENSOR_PIN         (A0)

// Controll variable names
#define MIN_MOIST_VAR               "Minimum%20Moisture%"
#define MAX_MOIST_VAR               "Maximum%20Moisture%"
#define AUTOMATIC_VAR               "Automatic%20Mode"
#define SPRINKLER_VAR               "Sprinkler%20System"
#define DRIP_VAR                    "Drip%20System"

#define SENSOR_READ_TIMEOUT         (10)    

DFRobot_SHT20    sht20;     // Connect SCL to GPIO5 and SDA to GPIO4
ESP8266WiFiMulti WiFiMulti;

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
  String result = "";
  if ((WiFiMulti.run() == WL_CONNECTED)) {

    WiFiClient client;
    HTTPClient http;
    //http.setTimeout(10000);

    Serial.print("Trying url: ");
    Serial.print(url);
    Serial.print(". ");    

    if (http.begin(client, url)) { 
      // start connection and send HTTP header
      int httpCode = http.GET();

      // httpCode will be negative on error
      if (httpCode > 0) {
        // HTTP header has been send and Server response header has been handled
        Serial.printf("[HTTP] GET code: %d\n", httpCode);
        if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_MOVED_PERMANENTLY) {
          result = http.getString();
        }
      } else {
        result = "Error: [HTTP] GET failed: " + http.errorToString(httpCode);
      }

      http.end();
    } else {
      result = "Error: Unable to connect to " + url;
    }
  }else{
    result = "Error: No wifi connection.";
  }

return result;
}

/* Reads sensors and stores values in global variables to make them available in every function */
void read_sensors(){

  h = sht20.readHumidity();                  // Read Humidity
  t = sht20.readTemperature();               // Read Temperature

    Serial.print(" Temperature:");
    Serial.print(t, 1);
    Serial.print("C");
    Serial.print(" Humidity:");
    Serial.print(h, 1);
    Serial.print("%");
    Serial.println();

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
    url = baseSetUrl + "&G=Automatic%20Mode&N=" + String(MAX_MOIST_VAR) + "&V=" + String(maxPercentage);
    result = do_http_get_request(url);
    Serial.println(result);
  }else{
    maxPercentage = result.toFloat();
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
      digitalWrite(SPRINKLER_RELAY_PIN, LOW);
    }else if(percentage > maxPercentage){
      digitalWrite(SPRINKLER_RELAY_PIN, HIGH);
    }
  }else{
    if(sprinklerSystemOn){
      digitalWrite(SPRINKLER_RELAY_PIN, LOW);
    }else{
      digitalWrite(SPRINKLER_RELAY_PIN, HIGH);
    }
  }

  if(dripSystemOn){
    digitalWrite(DRIP_RELAY_PIN, HIGH);
  }else{
    digitalWrite(DRIP_RELAY_PIN, LOW);
  }
}

void setup()
{

  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(SPRINKLER_RELAY_PIN, OUTPUT);
  pinMode(DRIP_RELAY_PIN, OUTPUT);
  pinMode(MOISTURE_SENSOR_PIN, INPUT);

  // Set startup state
  digitalWrite(SPRINKLER_RELAY_PIN, HIGH);
  digitalWrite(DRIP_RELAY_PIN, LOW);

  sht20.initSHT20();                                  // Init SHT20 Sensor
  delay(100);
  sht20.checkSHT20();                                 // Check SHT20 Sensor
  
  WiFi.mode(WIFI_STA);
  WiFiMulti.addAP(SSID_1, PASS_1);
  WiFiMulti.addAP(SSID_2, PASS_2);
  
  Serial.print( "\n\nConnecting" );
  while ( WiFiMulti.run() != WL_CONNECTED ) {
    delay ( 500 );
    ESP.wdtFeed();
    Serial.print ( "." );
  }
  String IP =  WiFi.localIP().toString();
  String wifi_statusMessage = "\nConnected to: " + WiFi.SSID() + String(". IP address: ") + IP;   
  Serial.println(wifi_statusMessage);  
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
