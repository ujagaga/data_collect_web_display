#ifndef CONFIG_H_
#define CONFIG_H_

/* Define 2 WiFi AP to connect to in case one is not available. 
This is usefull when developing at home and then using elsewhere. */
#define SSID_1                        "WIFI_SSID_1"
#define PASS_1                        "PASS_1"

#define SSID_2                        "WIFI_SSID_2"
#define PASS_2                        "PASS_2"

#define WEB_SERVICE_ADDRESS         "http://datacollect.ohanacode-dev.com/"
#define ADMIN_KEY                   "YOUR_API_KEY"

#define RELAY_PIN                     (14) 
#define PUSHBTN_PIN                   (4) 
#define LED_PIN                       (2)    
#define TEMPERATURE_PROBE_PIN         (13)  
#define ADDITIONAL_GND                (12)       

#endif
