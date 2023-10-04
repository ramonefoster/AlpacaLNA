#include <Arduino.h>
#include <Stepper.h>  
#include <AccelStepper.h>

#define MotorInterfaceType 1
#define dirPin 8
#define stepPin 9

const int stepsPerRevolution = 200; 
String command;

AccelStepper myStepper(MotorInterfaceType, stepPin, dirPin);    

void setup() {
  Serial.begin(9600);
  myStepper.setMaxSpeed(1000.0);
  myStepper.setAcceleration(100.0); 
}

void loop() {

  myStepper.run();

  if (Serial.available() > 0) {
    
    myStepper.run();
    command = Serial.readStringUntil('\n'); 
    myStepper.run();
    
    if (command.startsWith("M")) {
      command.remove(0, 1); // "M1000"
      int targetPosition = command.toInt();
      myStepper.moveTo(targetPosition);
      Serial.println(1);
    }

    else if (command.equals("P")) {       
      Serial.println(myStepper.currentPosition());
    } 

    else if (command.equals("R")) { 
      Serial.println(myStepper.isRunning());
    } 

    else if (command.equals("S")) { 
      myStepper.stop();
      Serial.println(1);
    } 

  }
  myStepper.run();
}
