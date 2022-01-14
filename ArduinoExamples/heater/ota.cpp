#include <ArduinoOTA.h>
#include <ESP8266WebServer.h>
#include <pgmspace.h>
#include "ota.h"

static const char HTML_REDIRECT[] PROGMEM = R"(
<!DOCTYPE HTML>
<html>
  <head>    
    <meta http-equiv="refresh" content="1; URL=/status?dummy=%s" />
    <title>OTA update</title>    
  </head>
  <body> 
<h1>Requesting OTA Update</h1>
</body></html>
)";

static const char HTML_STATUS[] PROGMEM = R"(
<!DOCTYPE HTML>
<html>
  <head> 
    <title>OTA update</title>    
  </head>
  <body> 
  <h1>OTA update %s.</h1>
</body>
</html>
)";


static bool updateStartedFlag = false;
static uint32_t updateRequestTimestamp = 0; 

static ESP8266WebServer otaWebServer(OTA_PORT);

static void showUpdateStart() {
  updateRequestTimestamp = millis();

  String response = FPSTR(HTML_REDIRECT);
  response.replace("%s", String(millis()));     // Add timestamp to prevent browser caching
  otaWebServer.send(200, "text/html", response);
}

static void showStatus() {
  String response = FPSTR(HTML_STATUS);
  String updateStatus = "not requested";
  if(updateRequestTimestamp > 0){
    updateStatus = "initializing";
  }
  response.replace("%s", updateStatus);
  
  otaWebServer.send(200, "text/html", response);
}

static void showNotFound(void){
  otaWebServer.send(404, "text/plain", "Not found!");      
}

bool OTA_updateInProgress(){
  return updateStartedFlag;
}

static void startUpdate() {
  updateStartedFlag = true;
  
  // Port defaults to 8266
  // ArduinoOTA.setPort(8266);
  ArduinoOTA.setHostname(DEVICE_NAME);

  // No authentication by default
  //ArduinoOTA.setPassword((const char *)"pass123");
   
  ArduinoOTA.onStart([]() {});
  ArduinoOTA.onEnd([]() {
    updateStartedFlag = false;
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {});
  ArduinoOTA.onError([](ota_error_t error) { });
  ArduinoOTA.begin();
}

void OTA_process(void){
  if(updateStartedFlag){
    ArduinoOTA.handle();
  }else{
    otaWebServer.handleClient(); 
    if((updateRequestTimestamp > 0) && ((millis() - updateRequestTimestamp) >  2000)){
      updateRequestTimestamp = 0;
      startUpdate();
    }    
  }
}

void OTA_init(){
  updateStartedFlag = false;
  updateRequestTimestamp = 0;
  
  otaWebServer.on("/", showUpdateStart);  
  otaWebServer.on("/status", showStatus);
  otaWebServer.onNotFound(showNotFound);
  otaWebServer.begin();
}
