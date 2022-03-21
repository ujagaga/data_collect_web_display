#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include "config.h"
#include "web_portal.h"
#include "wifi_connection.h"

static bool doorOpenFlag = false;

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

bool WP_getState(){
  return doorOpenFlag;
}

void WP_readData(){
  String result = "";
  String getUrl = String(WEB_SERVICE_ADDRESS) + "getvar?key=" + String(ADMIN_KEY) + "&N=" + String(DOOR_VAR);
  String setUrl = String(WEB_SERVICE_ADDRESS) + "setvar?key=" + String(ADMIN_KEY) + "&T=onetime&V=0&N=" + String(DOOR_VAR);
 
  // get automatic mode setting and set it if unset
  Serial.print("Fetching door state: ");  
  result = doHttpGetRequest(getUrl);
  Serial.println(result);
  
  if(result.startsWith("none")){
    Serial.println("Door state not set. Setting initial value:");
    result = doHttpGetRequest(setUrl);
    Serial.println(result);
  }else{
    doorOpenFlag = bool(result.toInt());
  } 
}
