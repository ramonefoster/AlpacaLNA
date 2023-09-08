#include <Arduino.h>
#include <Stepper.h>  
#include <AccelStepper.h>

#define MotorInterfaceType 4

const int stepsPerRevolution = 500; 
String command;

AccelStepper myStepper(MotorInterfaceType, 8, 9, 10, 11);    

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
