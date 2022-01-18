#include <OneWire.h>
#include <DallasTemperature.h>
#include "DS18B20.h"
#include "config.h"

#define ONE_WIRE_BUS              TEMPERATURE_PROBE_PIN

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensor(&oneWire);
// arrays to hold device address
DeviceAddress insideThermometer;  

float DS_read(){
  sensor.requestTemperatures();
  float tempC = sensor.getTempC(insideThermometer); 
  return tempC;
}

void DS_init(){ 
  // Additional GND
  pinMode(ADDITIONAL_GND, OUTPUT);
  digitalWrite(ADDITIONAL_GND, LOW); 
  
  sensor.begin();

  // Prepare the sensor
  int deviceCount = sensor.getDeviceCount();
  
  Serial.print("Found ");
  Serial.print(deviceCount, DEC);
  Serial.println(" DS18B20 devices.");  

  if(deviceCount > 0){
    if (!sensor.getAddress(insideThermometer, 0)) {
      Serial.println("Unable to find address for Device 0");
    }
  }
}
