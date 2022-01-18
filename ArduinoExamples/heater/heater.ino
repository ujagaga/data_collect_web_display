#include <DHT.h>    // Install DHT11 Library and Adafruit Unified Sensor Library
#include "config.h"
#include "DS18B20.h"
#include "web_portal.h"
#include "wifi_connection.h"
#include "ota.h"

#define SENSOR_READ_TIMEOUT         (60)    

static float t = 0;
static uint32_t cycle_timestamp = 0;
static uint32_t btnProcessTimestamp = 0;
static bool oldBtnPressedState = false;
static bool automaticModeOn = false;

void process_settings(){
  automaticModeOn = WP_getAutoMode();
  float targetTemp = WP_getTargetTemp();
  
  if(automaticModeOn){
    if(t < targetTemp){
      digitalWrite(RELAY_PIN, HIGH);
    }else{
      digitalWrite(RELAY_PIN, LOW);
    }
  }else{
    digitalWrite(RELAY_PIN, HIGH);
  }
}

static void processPushButton(){ 
  // Software debounce
  if((millis() - btnProcessTimestamp) > 100){
    btnProcessTimestamp = millis();
    
    bool btnPressed = digitalRead(PUSHBTN_PIN) == 0;
  
    if(btnPressed){
      if(!oldBtnPressedState){
        // Button was just pressed. Toggle automatic mode;
        automaticModeOn = !automaticModeOn;
        WP_setAutoMode(automaticModeOn);
      }
    }
  
    oldBtnPressedState = btnPressed;
  }

  if(automaticModeOn){
    // Blink the LED;
    int cycle = millis() % 2000;

    if(cycle < 1000){
      digitalWrite(LED_PIN, HIGH);
    }else{
      digitalWrite(LED_PIN, LOW);
    }
  }else{
    digitalWrite(LED_PIN, HIGH);
  }
}

void setup()
{
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(PUSHBTN_PIN, INPUT_PULLUP);

  digitalWrite(RELAY_PIN, HIGH); 
  digitalWrite(LED_PIN, HIGH);  
  
  WIFIC_connect();
  DS_init();
  automaticModeOn = WP_getAutoMode();
  OTA_init();
}

void loop() {
  OTA_process();
  
  if(!OTA_updateInProgress()){    
    processPushButton();
    
    if((millis() - cycle_timestamp) > (SENSOR_READ_TIMEOUT * 1000)){    
      t = DS_read();
      
      WP_setCurrentTemperature(t);    
      WP_sendData();
      WP_readData();
      
      process_settings();
      cycle_timestamp = millis();
    }
  }
}
