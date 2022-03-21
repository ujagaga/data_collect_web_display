#include "config.h"
#include "web_portal.h"
#include "wifi_connection.h"

#define SYNC_TIMEOUT          (5)   
#define UNLOCK_DURATION       (4) 

static uint32_t sync_timestamp = 0;
static uint32_t unlock_timestamp = 0;
static bool old_state = false;

void process_settings(){
  bool doorUnlock = WP_getState();
  
  if(doorUnlock){
    if(!old_state){
      // Just received ulock command
      unlock_timestamp = millis();
    }

    if((millis() - unlock_timestamp) < (UNLOCK_DURATION * 1000)){
      digitalWrite(RELAY_PIN, HIGH);
      digitalWrite(LED_PIN, LOW);
    }else{
      digitalWrite(RELAY_PIN, LOW);
      digitalWrite(LED_PIN, HIGH);
    }
  }else{
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_PIN, HIGH);
  }

  old_state = doorUnlock;
}

void setup()
{
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, LOW); 
  digitalWrite(LED_PIN, HIGH);  
  
  WIFIC_connect();
}

void loop() {    
  if((millis() - sync_timestamp) > (SYNC_TIMEOUT * 1000)){ 
    WP_readData();
    sync_timestamp = millis();
  }

  process_settings();
}
