#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <Servo.h>
#include "DHT.h"


#define DHTPIN D2
#define WATER_EARTH A0
#define FOTORES D0
#define WATERLEVEL D3

const int VENTILATION = D5;
const int WATER = D6;
const int LIGHT = D7;
const int TERM = D8;

const char* ssid ="3153";       // SSID вашей Wi-Fi сети
const char* password = "";  // Пароль от Wi-Fi сети
const char* raspberry_ip = "192.168.0.10";  // IP-адрес Raspberry Pi
const int raspberry_port = 5000;             // Порт Raspberry Pi
int key = 0;

WiFiClient client;
DynamicJsonDocument doc(1024);
Servo myServo;
DHT dht(DHTPIN, DHT11);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Подключение к Wi-Fi...");
  }

  Serial.println("Подключено к Wi-Fi");
   Serial.println(WiFi.localIP());
  dht.begin();
  myServo.attach(VENTILATION);
  pinMode (WATER, OUTPUT);
  pinMode (LIGHT, OUTPUT);
  pinMode (TERM, OUTPUT);

  pinMode (DHTPIN, INPUT);
  pinMode (WATER_EARTH, INPUT);
  pinMode (FOTORES, INPUT);
  pinMode (WATERLEVEL, INPUT);

  myServo.write(0); // Rotate servo back to 0 degrees

  HTTPClient http;
  String url = "http://" + String(raspberry_ip) + ":" + String(raspberry_port) + "/auth";
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  String mac = WiFi.macAddress();
  String postData = "{\"key\":" + String(key) + ",\"mac\":\"" + mac + "\"}";
  int httpCode = http.POST(postData);
  String response = "";

    while (httpCode < 1) {
      Serial.printf("[HTTP] Ошибка при получении ключа\n");
        String postData = "{\"key\":" + String(key) + ",\"mac\":\"" + mac + "\"}";
        int httpCode = http.POST(postData);
    }
    Serial.printf("[HTTP] POST успешно выполнен, код: %d\n", httpCode);

    key = response.toInt();
    Serial.println();
    Serial.println(key);
    http.end();
}

void loop() {
    HTTPClient http;
    // Ваши датчиковые данные
    // Формируем URL и данные для отправки
    String url = "http://" + String(raspberry_ip) + ":" + String(raspberry_port) + "/update_data";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    int light;                     // Создаем переменные
    light = digitalRead (FOTORES);        // считываем значение с порта pinD0
    Serial.println(light);

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (isnan(h) || isnan(t)) {
        Serial.println("Ошибка считывания");
        return;
    }
    Serial.println(h);
    Serial.println(t);

  int moisturePercentage = (100.00 - ( (analogRead(WATER_EARTH) / 1023.00) * 100.00 ) );
  Serial.print("Soil Moisture is  = ");
  Serial.print(moisturePercentage);
  Serial.println("%");

    // Формируем JSON-данные для отправки
    String postData = "{\"key\":" + String(key) + ",\"humidity\":" + String(h) + ",\"temperature\":" + String(t) + ",\"humidity_earth\":" + String(moisturePercentage) + "}";
    int httpCode = http.POST(postData);
    String response = "";

    if (httpCode > 0) {
        Serial.printf("[HTTP] POST успешно выполнен, код: %d\n", httpCode);
        response = ""+http.getString();
        Serial.println();
        Serial.println(response);
    } else {

        Serial.printf("[HTTP] Ошибка при выполнении POST запроса\n");
    }
    http.end();

    Serial.println("Отправка данных на Raspberry Pi...");
    
    DeserializationError error =  deserializeJson(doc, response);

    int ventilation = doc["ventilation"];
    int water = doc["water"];
    int term = doc["term"];
    for (auto kvp : doc.as<JsonObject>()) {
  Serial.print(kvp.key().c_str()); // Ключ
  Serial.print(": ");

  // Проверяем тип значения и выводим его
  JsonVariant value = kvp.value();

  if (value.is<bool>()) {
    Serial.println(value.as<bool>());
  }
  else if (value.is<int>()) {
    Serial.println(value.as<int>());
  }
  else if (value.is<float>()) {
    Serial.println(value.as<float>());
  }
  else {
    // Если значение само является JSON-объектом, используйте
    // рекурсию или отдельную функцию для его вывода
    Serial.println("Nested JSON Object");
  }
  // Добавьте другие типы проверок по мере необходимости
}


    // Check the value of the 'light' key in the JSON and turn on the LED accordingly
    if (ventilation == 1) {
          myServo.write(45); // Rotate servo to 90 degrees
    } else {
          myServo.write(0); // Rotate servo back to 0 degrees
    }
    if (water == 1) {
        digitalWrite(WATER, HIGH);
    } else {
        digitalWrite(WATER, LOW);
    }
    if (light == 1) {
        digitalWrite(LIGHT, HIGH);
    } else {
        digitalWrite(LIGHT, LOW);
    }
    if (term == 1) {
        digitalWrite(TERM, HIGH);
    } else {
        digitalWrite(TERM, LOW);
    }

    delay(10000); // Пауза между отправками данных
}
