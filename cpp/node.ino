#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <Servo.h>
#include "DHT.h"


#define DHTPIN D2
#define WATER_EARTH A0
#define FOTORES D0
#define WATERLEVEL D3

int on_TEMPERATURE = 0;
int on_HUMIDITY = 0;
int on_WATER_EARTH = 0;
int on_FOTORES = 0;
int on_WATERLEVEL = 0;

const int VENTILATION = D5;
const int WATER = D6;
const int LIGHT = D7;
const int TERM = D8;
const int VIBR = 3;

int on_VENTILATION = 0;
int on_WATER = 0;
int on_LIGHT = 0;
int on_TERM = 0;
int on_VIBR = 0;

const char* ssid = "1811wifi-1";              // SSID вашей Wi-Fi сети
const char* password = "1811pass1811";        // Пароль от Wi-Fi сети
const char* raspberry_ip = "172.19.104.151";  // IP-адрес Raspberry Pi
const int raspberry_port = 5000;              // Порт Raspberry Pi
int key = 0;
unsigned long lastTime = 0;  // сохраните это значение в начале программы


WiFiClient client;
DynamicJsonDocument doc(1024);
Servo myServo;
DHT dht(DHTPIN, DHT11);

void setup() {
  Serial.begin(115200);

  dht.begin();
  myServo.attach(VENTILATION);
  pinMode(WATER, OUTPUT);
  pinMode(LIGHT, OUTPUT);
  pinMode(TERM, OUTPUT);

  pinMode(DHTPIN, INPUT);
  pinMode(WATER_EARTH, INPUT);
  pinMode(FOTORES, INPUT);
  pinMode(WATERLEVEL, INPUT);

  myServo.write(0);  // Rotate servo back to 0 degrees
  wifi_start();
  Serial.println(1);
}

void loop() {

  unsigned long currentTime = millis();
  if (currentTime - lastTime > 3600000) {  //проверяем, прошел ли час (3600000 миллисекунд = 1 час)
    wifi_start();                          // выполняем нужную функцию
    lastTime = currentTime;                // обновляем время последнего выполнения функции
  } else {
    int light = -1;  // Создаем переменные
    if (on_FOTORES) {
      light = digitalRead(FOTORES);  // считываем значение с порта pinD0
      Serial.println(light);
    }

    float h = -50;
    float t = -50;
    if (on_HUMIDITY) {
      h = dht.readHumidity();
    }
    if (on_TEMPERATURE) {
      t = dht.readTemperature();
    }


    Serial.println(h);
    Serial.println(t);

  int moisturePercentage = -1;
  if (on_WATER_EARTH) {
    moisturePercentage = (100.00 - ((analogRead(WATER_EARTH) / 1023.00) * 100.00));
    Serial.print("Soil Moisture is  = ");
    Serial.print(moisturePercentage);
    Serial.println("%");
  }

  String postData = "{\"key\":" + String(key) + ",\"humidity\":" + String(h) + ",\"temperature\":" + String(t) + ",\"humidity_earth\":" + String(moisturePercentage) + ",\"light\":" + String(light) + "}";
  Serial.println(postData);
  String response = wifi_post(postData);


  DeserializationError error = deserializeJson(doc, response);

  int ventilation = doc["ventilation"];
  int water = doc["water"];
  int term = doc["term"];
  light = doc["light"];


  // Check the value of the 'light' key in the JSON and turn on the LED accordingly
  if (on_VENTILATION) {
    if (ventilation > 0) {
      myServo.write(ventilation);  // Rotate servo to 90 degrees
    } else {
      myServo.write(0);  // Rotate servo back to 0 degrees
    }
  }

  if (on_WATER) {
    if (water == 1) {
      digitalWrite(WATER, HIGH);
    } else {
      digitalWrite(WATER, LOW);
    }
  }
  if (on_LIGHT) {
    digitalWrite(LIGHT, HIGH);
  } else {
    digitalWrite(LIGHT, LOW);
  }
  if (on_TERM) {
    if (term == 1) {
      digitalWrite(TERM, HIGH);
    } else {
      digitalWrite(TERM, LOW);
    }
  }

  delay(6000);  // Пауза между отправками данных
}}

void wifi_start() {
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Подключение к Wi-Fi...");
  }

  Serial.println("Подключено к Wi-Fi");
  HTTPClient http;
  String url = "http://" + String(raspberry_ip) + ":" + String(raspberry_port) + "/auth";
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  key = 0;
  String mac = WiFi.macAddress();
  String postData = "{\"key\":" + String(key) + ",\"mac\":\"" + mac + "\"}";
  int httpCode = http.POST(postData);
  String response = "";

  while (httpCode < 1) {
    Serial.printf("[HTTP] Ошибка при получении ключа\n");
    String postData = "{\"key\":" + String(key) + ",\"mac\":\"" + mac + "\"}";
    int httpCode = http.POST(postData);
  }
  Serial.printf("[HTTP] POST auth успешно выполнен, код: %d\n", httpCode);
  response = "" + http.getString();


  DeserializationError error = deserializeJson(doc, response);

  key = doc["key"];
  on_TEMPERATURE = doc["on_TEMPERATURE"];
  on_HUMIDITY = doc["on_HUMIDITY"];
  on_WATER_EARTH = doc["on_WATER_EARTH"];
  on_FOTORES = doc["on_FOTORES"];
  on_WATERLEVEL = doc["on_WATERLEVEL"];
  on_VENTILATION = doc["on_VENTILATION"];
  on_WATER = doc["on_WATER"];
  on_LIGHT = doc["on_LIGHT"];
  on_TERM = doc["on_TERM"];
  on_VIBR = doc["on_VIBR"];
  Serial.println();
  Serial.println(key);
  Serial.println(on_TEMPERATURE);
  Serial.println(on_HUMIDITY);
  Serial.println(on_WATER_EARTH);
  Serial.println(on_FOTORES);
  Serial.println(on_WATERLEVEL);
  Serial.println(on_VENTILATION);
  Serial.println("this :" +on_WATER);
  Serial.println(on_LIGHT);
  Serial.println(on_TERM);
  Serial.println(on_VIBR);
  http.end();

  WiFi.mode(WIFI_OFF);
}

String wifi_post(String postData) {
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Подключение к Wi-Fi...");
  }

  Serial.println("Подключено к Wi-Fi");
  HTTPClient http;
  // Ваши датчиковые данные
  // Формируем URL и данные для отправки
  String url = "http://" + String(raspberry_ip) + ":" + String(raspberry_port) + "/update_data";
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");

  // Формируем JSON-данные для отправки
  int httpCode = http.POST(postData);
  String response = "";

  if (httpCode > 0) {
    Serial.printf("[HTTP] POST update_data успешно выполнен, код: %d\n", httpCode);
    response = "" + http.getString();
    Serial.println();
    Serial.println(response);
  } else {

    Serial.printf("[HTTP] Ошибка при выполнении POST запроса\n");
  }

  http.end();

  WiFi.mode(WIFI_OFF);

  Serial.println("Отправка данных на Raspberry Pi...");
  return response;
}

void light_sleep() {
  uint32_t sleep_time_in_ms = 600000;  // sleep time ms
  wifi_set_opmode(NULL_MODE);
  wifi_fpm_set_sleep_type(LIGHT_SLEEP_T);
  wifi_fpm_open();
  wifi_fpm_do_sleep(sleep_time_in_ms * 1000);
  delay(sleep_time_in_ms + 1);
}