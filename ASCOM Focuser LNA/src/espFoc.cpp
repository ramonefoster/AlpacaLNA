#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>

#include <AccelStepper.h>
#include <ArduinoJson.h>

//step-motor
#define MotorInterfaceType 4
#define IN1 5 //D1
#define IN2 4 //D2
#define IN3 14  //D5
#define IN4 12  //D6

const int stepsPerRevolution = 24; 
String command;

//photo-sensor
const int photsensor = 13; //D7

AccelStepper myStepper(MotorInterfaceType, IN1, IN3, IN2, IN4);  

const char* ssid = "LNA";
const char* password = "lab#astro";

ESP8266WebServer server(80);

void setup() {
  Serial.begin(9600);
  //motor
  myStepper.setMaxSpeed(200.0);
  myStepper.setAcceleration(50.0); 
  //sensor
  pinMode(photsensor, INPUT);
  //wifi
  WiFi.begin(ssid, password);
  IPAddress ip(192, 168, 11, 75); // Static IP
  IPAddress gateway(192, 168, 11, 1);
  IPAddress subnet(255, 255, 255, 0);
  WiFi.config(ip, gateway, subnet); 
  delay(500);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.println(WiFi.localIP());
  //routes
  server.on("/move", HTTP_GET, handleMove);
  server.on("/stop", HTTP_GET, handleStop);
  server.on("/position", HTTP_GET, handlePosition);
  server.on("/isrunning", HTTP_GET, handleRun);
  server.on("/", HTTP_GET, []() {
      server.send(200, F("text/html"),
          F("Welcome to the REST Web Server"));
  });
  server.begin();
}
void handleRun(){
  Serial.println("Running:"+String(myStepper.isRunning()));
  String response = handleResponse("success", String(myStepper.isRunning()));
  server.send(200, "application/json", response);
}
void handlePosition(){
  Serial.println("Position:"+String(myStepper.currentPosition()));
  String response = handleResponse("success", String(myStepper.currentPosition()));
  server.send(200, "application/json", response);
}
void handleStop(){
  myStepper.stop();
  String response = handleResponse("success", "Stopped");
  server.send(200, "application/json", response);
}
void handleMove(){
  String command = server.arg("steps");
  if (command.startsWith("M")) {
    command.remove(0, 1); // Remove the "M" character
    int targetPosition = command.toInt();
    myStepper.moveTo(targetPosition);
    myStepper.runToPosition();
    String response = handleResponse("success", "Moved to position: " + command);
    server.send(200, "application/json", response);
  } else {
    server.send(400, "text/plain", "Invalid command");
  }
}
String handleResponse(const char* status, const String& message) {
  // Create a JSON object and add data
  StaticJsonDocument<200> doc;
  doc["status"] = status;
  doc["message"] = message;

  // Serialize the JSON object to a string
  String jsonResponse;
  serializeJson(doc, jsonResponse);

  return jsonResponse;
}

void photoSensorRead(){  
    int sensorValue = digitalRead(photsensor);
    if (sensorValue == LOW) {
      Serial.println("Objeto detectado!"); // Se o sensor estiver bloqueado
    } else {
      Serial.println("Nenhum objeto detectado."); // Se o sensor estiver desobstruído
    }
}

void loop() {
  server.handleClient(); // Handle incoming HTTP requests
  myStepper.run(); // Run the stepper motor
}