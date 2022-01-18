#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include "wifi_connection.h"

ESP8266WiFiMulti WiFiMulti;

void WIFIC_connect(){
  Serial.print( "\n\nConnecting" );
  WiFi.mode(WIFI_STA);
  WiFiMulti.addAP(SSID_1, PASS_1);
  WiFiMulti.addAP(SSID_2, PASS_2);
  
  while ( WiFiMulti.run() != WL_CONNECTED ) {
    delay ( 500 );
    ESP.wdtFeed();
    Serial.print ( "." );
  }
  String IP =  WiFi.localIP().toString();
  String wifi_statusMessage = "\nConnected to: " + WiFi.SSID() + String(". IP address: ") + IP;   
  Serial.println(wifi_statusMessage);  
}

bool WIFIC_connected(){
  return (WiFiMulti.run() == WL_CONNECTED);
}
