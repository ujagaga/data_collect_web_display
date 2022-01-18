#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include "config.h"
#include "web_portal.h"
#include "wifi_connection.h"

static float targetTemp = 27;
static bool automaticModeOn = true;
static float temperature = 0;

static String doHttpGetRequest(String url){
  String result = "";
  if (WIFIC_connected()) {

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

void WP_setAutoMode(bool autoModeOn){
  automaticModeOn = autoModeOn;

  // Adjust in web service too
  Serial.println("Automatic mode changed. Updating web service.");
  String url = String(WEB_SERVICE_ADDRESS) + "setvar?key=" + String(ADMIN_KEY) + 
              "&T=toggle&N=" + String(AUTO_MODE_VAR) + 
              "&V=" + String(int(automaticModeOn));
  String result = doHttpGetRequest(url);
  Serial.println(result);
}

bool WP_getAutoMode(){
  return automaticModeOn;
}

float WP_getTargetTemp(){
  return targetTemp;
}

void WP_setCurrentTemperature(float curTemp){
  temperature = curTemp;
}

void WP_sendData(){
  String url = "";
  String result = "";
  String baseSetUrl = String(WEB_SERVICE_ADDRESS) + "postdata?key=" + String(ADMIN_KEY);

  // Set temperature
  url = baseSetUrl + "&N=Temperatura&V=" + String(temperature);
  Serial.print("Setting temperature: ");  
  result = doHttpGetRequest(url);
  Serial.println(result); 
}

void WP_readData(){
  String url = "";
  String result = "";
  String baseGetUrl = String(WEB_SERVICE_ADDRESS) + "getvar?key=" + String(ADMIN_KEY) + "&N=";
  String baseSetUrl = String(WEB_SERVICE_ADDRESS) + "setvar?key=" + String(ADMIN_KEY);
 
  // get automatic mode setting and set it if unset
  url = baseGetUrl + String(AUTO_MODE_VAR);
  Serial.print("Fetching automatic mode setting: ");  
  result = doHttpGetRequest(url);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Automatic mode not set. Setting initial value:");
    url = baseSetUrl + "&T=toggle&N=" + String(AUTO_MODE_VAR) + "&V=" + String(int(automaticModeOn)) + "&G=" + String(GROUP_VAR);
    result = doHttpGetRequest(url);
    Serial.println(result);
  }else{
    automaticModeOn = bool(result.toInt());
  } 
      
  // get target temperature and set it if unset 
  url = baseGetUrl + String(TARGET_TEMP_VAR);
  Serial.print("Fetching target temperature: ");  
  result = doHttpGetRequest(url);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Target temperature value not set. Setting initial value:");
    url = baseSetUrl + "&N=" + String(TARGET_TEMP_VAR) + "&V=" + String(targetTemp) + "&G=" + String(GROUP_VAR);
    result = doHttpGetRequest(url);
    Serial.println(result);
  }else{
    targetTemp = result.toFloat();
  } 
}
