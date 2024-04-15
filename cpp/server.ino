// Импортируем необходимые библиотеки:
#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <BH1750.h>
#include <DHT.h>
#include <OneWire.h>

//Датчик DTH22
#define DHTPIN 13                       //Указываем номер цифрового pin для чтения данных
#define DHTTYPE DHT22                   //Указываем тип датчика
DHT dht(DHTPIN, DHTTYPE);

//Датчик BH1750
BH1750 lightMeter;

//Датчик BME280
Adafruit_BME280 bme;                    // Подключаем датчик в режиме I2C

//Датчик DS18B20
OneWire ds(14); // Создаем объект OneWire для шины 1-Wire, с помощью которого будет осуществляться работа с датчиком

//Датчик Soil_Moisture_Sensor (влажность почвы)
int moisture_pin = 36;                 // Указываем номер аналогового пина
int output_value ;

// Задаем сетевые настройки
const char* ssid     = "ssid";
const char* password = "my_password";
IPAddress local_IP(192, 168, 1, 68);  // Задаем статический IP-адрес:
IPAddress gateway(192, 168, 1, 102);  // Задаем IP-адрес сетевого шлюза:
IPAddress subnet(255, 255, 255, 0);    // Задаем маску сети:
IPAddress primaryDNS(8, 8, 8, 8);      // Основной ДНС (опционально)
IPAddress secondaryDNS(8, 8, 4, 4);    // Резервный ДНС (опционально)
WiFiServer server(80);                 // Назначаем web серверу 80 порт
String header;                         // Переменная для хранения HTTP-запроса

// для хранения текущего состояния выходных контактов:
String output32State = "off";
String output33State = "off";
String output25State = "off";
String output14State = "off";

//========================= Однократная загрузка ============================
    void setup() {

Serial.begin(115200); // инициализируем монитор порта
delay(1500);           // запас времени на открытие монитора порта — 0,5 секунды

//DTH22
Serial.println(F("запуск датчика DHT22..."));
dht.begin();

// Датчик BH1750
Wire.begin();
lightMeter.begin();
Serial.println(F("запуск датчика BH1750..."));

// Датчик BME280
Serial.println(F("запуск датчика BME280..."));
if (!bme.begin(0x76)) {
Serial.println("Не обнаружен датчик BME280, проверьте соеденение!");
while (1);
}

//Датчик Soil_Moisture_Sensor
Serial.println("запуск датчика влажности почвы... ");

// Объявляем пины для подключения блока реле
pinMode(32, OUTPUT);       // Объявляем выходной пин BME280 (верхние форточки)
digitalWrite(32, LOW);     // присваиваем 'этому пину значение «LOW»
pinMode(33, OUTPUT);       // Объявляем выходной пин BME280 (нижние форточки)
digitalWrite(33, LOW);     // присваиваем 'этому пину значение «LOW»
pinMode(25, OUTPUT);       // Объявляем выходной пин Soil_Moisture_Sensor (полив-1)
digitalWrite(25, LOW);     // присваиваем 'этому пину значение «LOW»
//pinMode(26, OUTPUT);     // Объявляем выходной пин Soil_Moisture_Sensor (полив-2)
//digitalWrite(26, LOW);   // присваиваем 'этому пину значение «LOW»
//pinMode(27, OUTPUT);     // Объявляем выходной пин Soil_Moisture_Sensor (полив-3)
//digitalWrite(27, LOW);   // присваиваем 'этому пину значение «LOW»
pinMode(14, OUTPUT);       // Объявляем выходной пин BH1750 (освещение)
digitalWrite(14, LOW);     // присваиваем 'этому пину значение «LOW»

// Настраиваем статический IP-адрес:
if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
Serial.println("Режим клиента не удалось настроить");
}

// Подключаемся к WiFi:
WiFi.begin(ssid, password);
while (WiFi.status() != WL_CONNECTED) {
delay(1000);
Serial.println("Подключаемся к WiFi...");
}

// Отображаем локальный IP-адрес и запускаем веб-сервер:
Serial.println("");
Serial.println("WiFi подключен.");
Serial.println("IP адрес: ");
Serial.println(WiFi.localIP());
server.begin();
Serial.println("Web сервер запущен.");
}
//============================= Циклическая загрузка ================================
    void loop(){

// DTH22 Датчик температуры и влажности
float IN2 = dht.readHumidity();                         // Считывание влажности и создание переменной с именем IN2
float IN1 = dht.readTemperature();                      // Считывание температуры и создание переменной с именем IN1
// Проверяем, не удалось ли выполнить какое-либо чтение, после чего выходим раньше (чтобы повторить попытку).
if (isnan(IN2) || isnan(IN1)) {
Serial.println(F("Ошибка чтения с DHT датчика!"));
return;
}
Serial.print(F("DTH22- Влажность: "));                  // Вывод текста в монитор порта
Serial.print(IN2);                                      // Вывод влажности в последовательный монитор
Serial.print(F(" %   Температура: "));                  // Вывод текста в монитор порта
Serial.print(IN1);                                      // Вывод температуры в последовательный монитор
Serial.println(F(" °C "));                              // Вывод текста в монитор порта
delay(1000);                                            // Пауза 1 сек.

//Датчик BH1750
float IN3 = lightMeter.readLightLevel();                // Считывание данных и создание переменной с именем IN3
Serial.print("Освещенность: ");                         // Вывод текста в монитор порта
Serial.print(IN3);                                      // Вывод показаний в последовательный монитор порта
Serial.println(" люкс");                                // Вывод текста в монитор порта
//if (IN3>=500) digitalWrite(32, HIGH);                   // При достижении освещенности 2000 люкс и выше, подать 1 на 32 пин.
//else digitalWrite(32, LOW);                             // Сброс реле в исходное состояние
delay(1000);

// Универсальный датчик MBE280
float IN4 = (bme.readTemperature()-1.04);               // Считывание температуры и создание переменной с именем IN4, поправочный коэффициент -1.04 гр.
Serial.print("BME280- Температура: ");                  // Вывод текста в монитор порта
Serial.print(IN4);                                      // Вывод показаний в последовательный монитор порта
Serial.print(F(" °C "));                                // Вывод текста в монитор порта
// По заданной температуре открываем (закрываем) форточки.
//if (IN4>=24) digitalWrite(25, HIGH);                    // При достижении температуры 24 гр. и выше, подать 1 на 25 пин.
//if (IN4<=20) digitalWrite(25, LOW);                     // При понижении температуры до 20 гр. и ниже, подать 0 на 25 пин.
//if (IN4>=26) digitalWrite(26, HIGH);                    // При достижении температуры 26 гр. и выше, подать 1 на 26 пин.
//else digitalWrite(26, LOW);                             // Сброс реле в исходное состояние

float IN5 = (bme.readPressure()/133.3);                 // Считывание давление и создаем переменную с именем IN5
Serial.print(" Давление: ");                            // Вывод текста в монитор порта
Serial.print(IN5);                                      // Вывод показаний в последовательный монитор порта
Serial.print(" мм.рт.ст ");                             // Вывод текста в монитор порта

float IN6 = (bme.readHumidity());                       // Считывание влажности воздуха и создание переменной с именем IN6
Serial.print(" Влажность: ");                           // Вывод текста в монитор порта
Serial.print(IN6);                                      // Вывод показаний в последовательный монитор порта
Serial.println(" %");                                   // Вывод текста в монитор порта
delay(1000);                                            // Пауза 1 сек.

//Датчик DS18B20
byte data[2];     // Место для значения температуры
ds.reset();       // Начинаем взаимодействие со сброса всех предыдущих команд и параметров
ds.write(0xCC);   // Даем датчику DS18b20 команду пропустить поиск по адресу. В нашем случае только одно устрйоство
ds.write(0x44);   // Даем датчику DS18b20 команду измерить температуру. Само значение температуры мы еще не получаем - датчик его положит во внутреннюю память
delay(1000);      // Микросхема измеряет температуру, а мы ждем.
ds.reset();       // Теперь готовимся получить значение измеренной температуры
ds.write(0xCC);
ds.write(0xBE);   // Просим передать нам значение регистров со значением температуры

// Получаем и считываем ответ
data[0] = ds.read();   // Читаем младший байт значения температуры
data[1] = ds.read();   // А теперь старший

// Формируем итоговое значение:
// - сперва "склеиваем" значение,
// - затем умножаем его на коэффициент, соответсвующий разрешающей способности (для 12 бит по умолчанию - это 0,0625)
float temperature =  ((data[1] << 8) | data[0]) * 0.0625;

float IN7 = ((temperature)+2.3);                        // Считывание данных и создание переменной с именем IN7, поправочный коэффициент +2,3 гр.
Serial.print("DS18B20- Температура почвы: ");           // Вывод текста в монитор порта
Serial.print(IN7);                                      // Вывод показаний в последовательный монитор порта
Serial.println(" °C");                                  // Вывод текста в монитор порта

//Датчик Soil Moisture Sensor (Датчик влажности почвы)
output_value = analogRead(moisture_pin);
output_value = map(output_value, 4090, 2900, 0, 100);  // Настроить, где: 4090=0% влажности, 2900=100% влажности.
float IN8 = (output_value);                            // Считывание данных и создание переменной с именем IN8
Serial.print("Влажность почвы: ");
Serial.print(IN8);                                     // Вывод показаний в последовательный монитор порта
Serial.println("%");
Serial.println();
//if (IN8>=50) digitalWrite(33, HIGH);                  // При понижении влажности до 50% и менее, подать 1 на 33 пин.
//else digitalWrite(33, LOW);                           // Сброс реле в исходное состояние
delay(1000);

//========================================== Настройка вэб сервера ===================================================
WiFiClient client = server.available();                // начинаем прослушивать входящих клиентов:
      if (client) {                                    // если подключился новый клиент,
        Serial.println("Клиент подключился...");       // выводим сообщение «Новый клиент» в мониторе порта
        String currentLine = "";                       // создаем строку для хранения входящих данных от клиента
        while (client.connected()) {                   // цикл while() будет работать все то время, пока клиент будет подключен к серверу;
          if (client.available()) {                    // если у клиента есть данные, которые можно прочесть,
            char c = client.read();                    // считываем байт, а затем
            Serial.write(c);                           // выводим его в мониторе порта
            header += c;
            if (c == '\n') {                           // если этим байтом является символ новой строки
// если текущая строка пуста, у вас есть два символа новой строки подряд
// это конец клиентского HTTP-запроса, поэтому отпраляем ответ:
              if (currentLine.length() == 0) {
// HTTP-заголовки всегда начинаются с кода ответа (например, «HTTP/1.1 200 OK»)
// и информации о типе контента(чтобы клиент понимал, что получает) в конце пишем пустую строчку:
client.println("HTTP/1.1 200 OK");
client.println("Content-type:text/html");
client.println("Подключение: закрыто"); //  "Соединение: отключено"
client.println();

                // с помощью этого кода включаем и выключаем GPIO-контакты:
                if (header.indexOf("GET /32/on") >= 0) {
                   Serial.println("GPIO 32 включен");        // "GPIO32 включен"
                   output32State = "on";
                   digitalWrite(32, HIGH);
                } else if (header.indexOf("GET /32/off") >= 0) {
                Serial.println("GPIO 32 выключен");          // "GPIO32 выключен"
                output32State = "off";
                digitalWrite(32, LOW);
                }

                if (header.indexOf("GET /33/on") >= 0) {
                   Serial.println("GPIO 33 включен");        // "GPIO33 включен"
                   output33State = "on";
                   digitalWrite(33, HIGH);
                } else if (header.indexOf("GET /33/off") >= 0) {
                Serial.println("GPIO 33 выключен");          // "GPIO33 выключен"
                output33State = "off";
                digitalWrite(33, LOW);
                }

				if (header.indexOf("GET /25/on") >= 0) {
                   Serial.println("GPIO 25 включен");       // "GPIO25 включен"
                   output25State = "on";
                   digitalWrite(25, HIGH);
                } else if (header.indexOf("GET /25/off") >= 0) {
                Serial.println("GPIO 25 выключен");         // "GPIO25 выключен"
                output25State = "off";
                digitalWrite(25, LOW);
                }

				if (header.indexOf("GET /14/on") >= 0) {
                   Serial.println("GPIO 14 включен");       // "GPIO14 включен"
                   output14State = "on";
                   digitalWrite(14, HIGH);
                } else if (header.indexOf("GET /14/off") >= 0) {
                Serial.println("GPIO 14 выключен");        // "GPIO14 выключен"
                output14State = "off";
                digitalWrite(14, LOW);
                }
// Отправляем HTML страницу клиенту.
client.println("<!DOCTYPE html>");
client.println("<html>");
client.println("<head>");
client.println("<meta charset=utf-8 http-equiv=refresh content=10>");
client.println("<link href=<a href="http://a.radikal.ru/a02/2103/16/d2882b4d2489.jpg" rel="nofollow">http://a.radikal.ru/a02/2103/16/d2882b4d2489.jpg</a> rel=shortcut icon type=/x-icon>");
client.println("<title>Моя тепличка</title>");
//client.println("<link rel=StyleSheet type=text/css>");
// ============== CSS стиль таблицы ================
client.println("<style>");
// Фоновый градиент
client.println("#gradient {");
client.println("-ms-filter: progid:DXImageTransform.Microsoft.gradient (GradientType=0, startColorstr=#589afc, endColorstr=#f0f5fc);");
client.println("background: -webkit-linear-gradient(to bottom, #589afc, #f0f5fc);");
client.println("background: -moz-linear-gradient(to bottom, #589afc, #f0f5fc);");
client.println("background: -o-linear-gradient(to bottom, #589afc, #f0f5fc);");
client.println("background: linear-gradient(to bottom, #589afc, #f0f5fc);");
client.println("}");
// Позиционирование картинки и наложение на нее данных
client.println(".wrapper{min-height: 87vh; display: flex; flex-direction: column;}");
client.println(".title{text-align: center;}");
client.println(".content{flex-grow: 1; display: flex; justify-content: center; align-items: center;}");
client.println(".img-block{max-width: 900px; position: relative;}");
client.println(".img-block img{max-width: 100%;} ");
client.println(".txt-top, .txt-bottom{position: absolute;}");
client.println(".txt-top {top: font-size:1.3em; color:red}");
// стиль кнопок «ON» и «OFF»;
client.println("html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}");
client.println(".button { background-color: #1d32f0; border: none; color: white; padding: 3px 41px;");
client.println("text-decoration: none; font-size: 20px; margin: 2px; cursor: pointer;}");
client.println(".button2 {background-color: #878686;}");
client.println("</style>");
// Заголовок веб страницы
client.println("</head>");
client.println("<body id=gradient onload=startTime()>");
client.println("<center>");
client.println("<p><img alt=домик height=70 width=72 src=<a href="http://b.radikal.ru/b24/2103/fe/fc244b9baa45.png" rel="nofollow">http://b.radikal.ru/b24/2103/fe/fc244b9baa45.png</a>><font size=7 color=#FFFFFF> &nbsp;&nbsp; Контрольная панель - Умная теплица</font></p>");
client.println("</center>");
client.println("<div class=wrapper>");
client.println("<div class=title>");
client.println("<hr noshade size=3px>");
client.println("</div>");
client.println("<div class=content>");
client.println("<div class=img-block><img src=<a href="http://c.radikal.ru/c11/2103/8a/a37215234ef6.png" rel="nofollow">http://c.radikal.ru/c11/2103/8a/a37215234ef6.png</a> alt=картинка>");
client.println("<div class=txt-top style='top:17px; left:700px;'><img src=<a href="http://a.radikal.ru/a23/2103/45/eebdf37707a9.gif" rel="nofollow">http://a.radikal.ru/a23/2103/45/eebdf37707a9.gif</a> height=142 width=172></div>");
// Отображаем в браузере иконки и показания датчиков
client.print("<div class=txt-top style='top:20px; left:65px;'><img src=<a href="http://b.radikal.ru/b07/2103/c5/2f3c2bd305b7.png" rel="nofollow">http://b.radikal.ru/b07/2103/c5/2f3c2bd305b7.png</a>>");
client.print("&nbsp;&nbsp; Температура:&nbsp;&nbsp;");
client.print("<b>");
client.print(IN1);
client.print("</b>");
client.print(" &nbsp;°C");
client.println("</div>");

client.print("<div class=txt-top style='top:50px; left:65px;'><img src=<a href="http://c.radikal.ru/c11/2103/69/c266ed71cfda.png" rel="nofollow">http://c.radikal.ru/c11/2103/69/c266ed71cfda.png</a>>");
client.print("&nbsp;&nbsp; Влажность:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
client.print("<b>");
client.print(IN2);
client.print("</b>");
client.print(" &nbsp;%");
client.println("</div>");

client.print("<div class=txt-top style='top:260px; left:540px;'><img src=<a href="http://b.radikal.ru/b05/2103/b4/fbce1a092bdb.png" rel="nofollow">http://b.radikal.ru/b05/2103/b4/fbce1a092bdb.png</a>>");
client.print(" Освещенность:&nbsp;&nbsp;");
client.print("<b>");
client.print(IN3);
client.print("</b>");
client.print(" &nbsp;люкс");
client.println("</div>");

client.print("<div class=txt-top style='top:290px; left:540px;'><img src=<a href="http://b.radikal.ru/b07/2103/c5/2f3c2bd305b7.png" rel="nofollow">http://b.radikal.ru/b07/2103/c5/2f3c2bd305b7.png</a>>");
client.print("&nbsp; Температура:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
client.print("<b>");
client.print (IN4);
client.print("</b>");
client.print(" °C");
client.println("</div>");

client.print("<div class=txt-top style='top:320px; left:540px;'><img src=<a href="http://a.radikal.ru/a27/2103/0a/df3356c53b7b.png" rel="nofollow">http://a.radikal.ru/a27/2103/0a/df3356c53b7b.png</a>>");
client.print("&nbsp; Давление: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
client.print("<b>");
client.print(IN5);
client.print("</b>");
client.print(" &nbsp;мм.рт.ст");
client.println("</div>");

client.print("<div class=txt-top style='top:350px; left:540px;'><img src=<a href="http://c.radikal.ru/c11/2103/69/c266ed71cfda.png" rel="nofollow">http://c.radikal.ru/c11/2103/69/c266ed71cfda.png</a>>");
client.print("&nbsp; Влажность:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
client.print("<b>");
client.print(IN6);
client.print("</b>");
client.print(" &nbsp;%");
client.println("</div>");

client.println("<div class=txt-top style='top:485px; left:239px;'><img src=<a href="http://b.radikal.ru/b07/2103/c5/2f3c2bd305b7.png" rel="nofollow">http://b.radikal.ru/b07/2103/c5/2f3c2bd305b7.png</a>>");
client.print("<b>&nbsp;");
client.print(IN7);
client.print("</b>");
client.print(" &nbsp;°C");
client.println("</div>");

client.println("<div class=txt-top style='top:515px; left:239px;'><img src=<a href="http://c.radikal.ru/c11/2103/69/c266ed71cfda.png" rel="nofollow">http://c.radikal.ru/c11/2103/69/c266ed71cfda.png</a>>");
client.print("<b>&nbsp;");
client.print(IN8);
client.print("</b>");
client.print(" &nbsp;%");
client.print("</div>");

// Отображаем в браузере кнопки
client.println("<div class=txt-top style='top:235px; right:-170px;'>");
client.println("<p>форточки " + output32State + "</p>");
if (output32State=="off") {
client.println("<p><a href=\"/32/on\"><button class=\"button\">ОТКРЫТЬ</button></a></p>");
} else {
client.println("<p><a href=\"/32/off\"><button class=\"button button2\">ЗАКРЫТЬ</button></a></p>"); }
client.println("</div>");

client.println("<div class=txt-top style='top:315px; right:-170px;'>");
client.println("<p>форточки " + output33State + "</p>");
if (output33State=="off") {
client.println("<p><a href=\"/33/on\"><button class=\"button\">ОТКРЫТЬ</button></a></p>");
} else {
client.println("<p><a href=\"/33/off\"><button class=\"button button2\">ЗАКРЫТЬ</button></a></p>"); }
client.println("</div>");

client.println("<div class=txt-top style='top:395px; right:-170px;'>");
client.println("<p>Полив11 " + output25State + "</p>");
if (output25State=="off") {
client.println("<p><a href=\"/25/on\"><button class=\"button\">ОТКРЫТЬ</button></a></p>");
} else {
client.println("<p><a href=\"/25/off\"><button class=\"button button2\">ЗАКРЫТЬ</button></a></p>"); }
client.println("</div>");

client.println("<div class=txt-top style='top:475px; right:-170px;'>");
client.println("<p>Полив-1 " + output14State + "</p>");
if (output14State=="off") {
client.println("<p><a href=\"/14/on\"><button class=\"button\">ОТКРЫТЬ</button></a></p>");
} else {
client.println("<p><a href=\"/14/off\"><button class=\"button button2\">ЗАКРЫТЬ</button></a></p>"); }
client.println("</div>");

client.println("</div>");
client.println("</div>");
client.println("</div>");
client.println("</body>");
client.println("</html>");
client.println();    // конец HTTP-ответа задается с помощью дополнительной пустой строки

                break;                      // выходим из цикла while
              } else {                      // если получили символ новой строки,
                currentLine = "";           // очищаем текущую строку «currentLine»:
              }
            } else if (c != '\r') {         // если получили любые данные, кроме символа возврата каретки,
              currentLine += c;             // добавляем эти данные в конец строки «currentLine»
            }
          }
		}
        header = "";                        // очищаем переменную «header»
        client.stop();                      // закрываем соединение
        Serial.println("Клиент отключен");  // выводим ссобщение в последовательный монитор
        Serial.println("");                 // "Клиент отключен"
      }
    }