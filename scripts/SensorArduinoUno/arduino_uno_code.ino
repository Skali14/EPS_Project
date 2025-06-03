/*
Code by K12206357

Everything that is commented out is for testing
*/

// please install these libraries first 
#include <Wire.h>
#include "Adafruit_VL6180X.h"
#include "DHT.h"

Adafruit_VL6180X vl = Adafruit_VL6180X();

#define DHTPIN 2        // connect DATA pin of DHT11 to digital pin 2
#define DHTTYPE DHT11   // DHT11 sensor

DHT dht(DHTPIN, DHTTYPE);

const int AnalogPhoto = A0;

const int redLED = 9;

int photoIn = 0;
int tempIn = 0;

void setup() {

  Serial.begin(9600);
  dht.begin();
  
  // wait for serial port to open on native usb devices
  while (!Serial) {
    delay(1);
  }
  
  //Serial.println("Adafruit VL6180x test!");
  if (! vl.begin()) {
    //Serial.println("Failed to find sensor");
    while (1);
  }
  //Serial.println("Sensor found!");
}

void loop() {
  // Temp & Humid
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Check if any reads failed
  if (isnan(humidity) || isnan(temperature)) {
    //Serial.println("Failed to read from DHT sensor!");
    return;
  }

  Serial.print("sens_humid=");
  Serial.println(humidity);
  //Serial.print(" %\t"); // not included for communication
  Serial.print("sens_temp=");
  Serial.println(temperature);
  //Serial.println(" °C"); // not included for communication

  // Distance
  float lux = vl.readLux(VL6180X_ALS_GAIN_5);

  Serial.print("sens_lux="); 
  Serial.println(lux);
  
  uint8_t range = vl.readRange();
  uint8_t status = vl.readRangeStatus();

  if (status == VL6180X_ERROR_NONE) {
    Serial.print("sens_range="); 
    Serial.println(range);
  } else {
    Serial.println("sens_range=-1"); // if the range is greater than the max -> return -1
    //Serial.println(status);
  }



  // photo-sensor activates redLED
  photoIn = analogRead(AnalogPhoto);
  if(photoIn < 320) {
    analogWrite(redLED, 255);
    Serial.println("led_red=true");
  } else {
    analogWrite(redLED, 0);
    Serial.println("led_red=false");
  }
  Serial.print("sens_photo=");
  Serial.println(photoIn);

  //delay
  delay(1000);
}
