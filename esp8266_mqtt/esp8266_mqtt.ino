#include <Arduino.h>

#include <ESP8266WiFi.h>

#include <WiFiClientSecure.h>

#include <PubSubClient.h>

#include <Adafruit_BME280.h>                 

#include <iarduino_OLED.h>                             

#define mq2_pin 0

iarduino_OLED myOLED(0x3C); 
extern uint8_t SmallFontRus[]; 
extern uint8_t MediumFontRus[];

Adafruit_BME280 bme;

const char * wifi_ssid = ""; //paste wifi ssid
const char * wifi_pass = ""; //paste wifi ssid

const char * mqtt_server = ""; //paste url to mqtt server
const char * mqtt_client_id = ""; //paste client id
const char * mqtt_user = ""; //paste mqtt username
const char * mqtt_pass = ""; //paste mqtt password

//if you need, change mqtt topics
const char mqtt_pub_topic_lat[] = "psms/lat";
const char mqtt_pub_topic_lon[] = "psms/lon";
const char mqtt_pub_bme280_temp[] = "psms/temp";
const char mqtt_pub_bme280_hum[] = "psms/humidity";
const char mqtt_pub_bme280_pres[] = "psms/pres";
const char mqtt_pub_bme280_stat[] = "psms/stat";
const char mqtt_pub_methane[] = "psms/methane";

extern uint8_t Img_Level_1[];
extern uint8_t Img_Level_2[];
extern uint8_t Img_Level_3[]; 
extern uint8_t Img_Level_4[]; 
extern uint8_t Img_Antenna[];
extern uint8_t Img_Battery_0[]; 
extern uint8_t Img_Battery_1[]; 
extern uint8_t Img_Battery_2[]; 
extern uint8_t Img_Battery_3[];
extern uint8_t Img_BigBattery_low[]; 
int8_t i = 4; 
bool need_to_clear_oled = false;
bool danger_area = false;
bool view_danger = false;
bool suit_state = false;
String suit_state_str = "Выключен";
bool draw_now = false;

int8_t num_of_coords_pack = -1;
bool return_coord_pac = true;

uint16_t new_coord_delay = 6143;
uint16_t draw_new_state_delay = 2345;
uint16_t mqtt_pub_delay = 999;

const char pem_ca[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
paste certificate
-----END CERTIFICATE-----
)EOF";
X509List ca(pem_ca);

WiFiClientSecure wifi;
PubSubClient mqtt(wifi);

time_t now;

void mqtt_connect() {
  Serial.println("Attempting MQTT connection");
  while (!mqtt.connected()) {
    check_WiFi();
    if (mqtt.connect(mqtt_client_id, mqtt_user, mqtt_pass)) {
      Serial.println("MQTT server connected");
    } else {
      Serial.print("Failed, status code=");
      Serial.print(mqtt.state());
      Serial.println(". Try again in 2 seconds.");
      delay(2000);
    }
  }
}

void check_WiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Reconnect to Wifi");
    while (WiFi.waitForConnectResult() != WL_CONNECTED) {
      WiFi.begin(wifi_ssid, wifi_pass);
      Serial.print(".");
      delay(10);
    }
    Serial.println("");
    Serial.println("WiFi connected");
  }
}

void check_MQTT() {
  if (!mqtt.connected()) {
    mqtt_connect();
  } else {
    mqtt.loop();
  }
}

void received_callback(char * topic, byte * payload, unsigned int length) {
  String payload_str = "";
  String topic_str = String(topic);
  Serial.print(topic_str);
  if (topic_str == "psms/danger_area") {
    if ((char) payload[0] == '0') {
      danger_area = false;
    } else {
      danger_area = true;
    }
    Serial.println(danger_area);
  }
  if (topic_str == "psms/suit_state") {
    if ((char) payload[0] == '0') {
      suit_state = false;
    } else {
      suit_state = true;
    }
    Serial.println(suit_state);
  }
}

void setup() {
  Serial.begin(9600);

  myOLED.begin();
  myOLED.clrScr();
  myOLED.setFont(SmallFontRus);
  myOLED.print("Подключение к", OLED_C, OLED_T);
  myOLED.setCursorShift(0, 10); 
  myOLED.print("Rightech IoT", OLED_C); 
  myOLED.setCursorShift(0, 10);
  myOLED.print("cloud...", OLED_C); 
  need_to_clear_oled = true;
  Serial.println();
  Serial.print("Connecting to ");
  Serial.print(wifi_ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid, wifi_pass);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  configTime(3 * 3600, 0, "pool.ntp.org", "time.nist.gov");

  Serial.print("Waiting for NTP time sync: ");
  time_t now = time(nullptr);
  while (now < 8 * 3600 * 2) {
    delay(1000);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("");

  struct tm timeinfo;
  gmtime_r( & now, & timeinfo);
  Serial.print("Current time: ");
  Serial.print(asctime( & timeinfo));

  wifi.setTrustAnchors( & ca);
  mqtt.setServer(mqtt_server, 8883);
  mqtt.setCallback(received_callback);
  mqtt_connect();
}

void loop() {
  check_WiFi();
  check_MQTT();
  if (millis() % mqtt_pub_delay == 0) {
    if (bme.begin(0x76)) {
      mqtt.publish(mqtt_pub_bme280_temp, String(bme.readTemperature()).c_str());
      mqtt.publish(mqtt_pub_bme280_hum, String(bme.readHumidity()).c_str());
      mqtt.publish(mqtt_pub_bme280_pres, String(bme.readPressure()).c_str());
      mqtt.publish(mqtt_pub_methane, String(analogRead(mq2_pin) * 0.00534 - 0.62173).c_str());
    }
  }
  if (danger_area and!view_danger) {
    myOLED.clrScr();
    myOLED.setFont(MediumFontRus); 
    myOLED.print("ОПАСНОСТЬ", OLED_L, OLED_C); 
    myOLED.setFont(SmallFontRus); 
    myOLED.setCursorShift(0, 10);
    myOLED.print("Покиньте", OLED_L);
    myOLED.setCursorShift(0, 10);
    myOLED.print("запрещённую геозону!", OLED_L);
    view_danger = true;
  } else if (!danger_area) {
    if (view_danger) {
      myOLED.clrScr();
      view_danger = false;
      draw_now = true;
    }
    if (millis() % draw_new_state_delay == 0 or draw_now) {
      draw_now = false;
      myOLED.setFont(SmallFontRus); 
      if (i < 0) {
        i = 3;
      } else {
        i--;
      } 
      switch (i) {
      case 0:
        myOLED.clrScr();
        myOLED.drawImage(Img_Level_1, 0, 7, IMG_ROM); 
        myOLED.drawImage(Img_Antenna, 12, 7, IMG_ROM); 
        myOLED.drawImage(Img_Battery_0, OLED_R, OLED_T, IMG_ROM);
        myOLED.drawImage(Img_BigBattery_low, OLED_C, OLED_C, IMG_ROM); 
        myOLED.setCursor(15, 50); 
        myOLED.print("Критически низкий"); 
        myOLED.print("заряд!", OLED_C, OLED_B);
        need_to_clear_oled = true;
        break; 
      case 1:
        if (need_to_clear_oled) {
          myOLED.clrScr();
          need_to_clear_oled = false;
        }
        myOLED.drawImage(Img_Level_3, 0, 7, IMG_ROM); 
        myOLED.drawImage(Img_Antenna, 12, 7, IMG_ROM); 
        myOLED.drawImage(Img_Battery_1, OLED_R, OLED_T, IMG_ROM);
        if (suit_state) {
          if (suit_state_str == "выключен") {
            need_to_clear_oled = true;
          }
          suit_state_str = "работает";
        } else {
          if (suit_state_str == "работает") {
            need_to_clear_oled = true;
          }
          suit_state_str = "выключен";
        }
        myOLED.print(("Коcтюм: " + suit_state_str), OLED_L, OLED_C); 
        break;
      case 2:
        if (need_to_clear_oled) {
          myOLED.clrScr();
          need_to_clear_oled = false;
        }
        myOLED.drawImage(Img_Level_4, 0, 7, IMG_ROM);
        myOLED.drawImage(Img_Antenna, 12, 7, IMG_ROM);
        myOLED.drawImage(Img_Battery_2, OLED_R, OLED_T, IMG_ROM);
        if (suit_state) {
          if (suit_state_str == "выключен") {
            need_to_clear_oled = true;
          }
          suit_state_str = "работает";
        } else {
          if (suit_state_str == "работает") {
            need_to_clear_oled = true;
          }
          suit_state_str = "выключен";
        }
        myOLED.print(("Коcтюм: " + suit_state_str), OLED_L, OLED_C);
        break; 
      case 3:
        if (need_to_clear_oled) {
          myOLED.clrScr();
          need_to_clear_oled = false;
        }
        myOLED.drawImage(Img_Level_2, 0, 7, IMG_ROM);
        myOLED.drawImage(Img_Antenna, 12, 7, IMG_ROM);
        myOLED.drawImage(Img_Battery_3, OLED_R, OLED_T, IMG_ROM);
        if (suit_state) {
          if (suit_state_str == "выключен") {
            need_to_clear_oled = true;
          }
          suit_state_str = "работает";
        } else {
          if (suit_state_str == "работает") {
            need_to_clear_oled = true;
          }
          suit_state_str = "выключен";
        }
        myOLED.print(("Коcтюм: " + suit_state_str), OLED_L, OLED_C);
        break;
      }
    }
  }
  if (millis() % new_coord_delay == 0) {
    if (return_coord_pac) {
      mqtt.publish(mqtt_pub_topic_lon, "63.873138");
      mqtt.publish(mqtt_pub_topic_lat, "67.618373");
      return_coord_pac = false;
      Serial.println("return");
    } else {
      num_of_coords_pack++;
      if (num_of_coords_pack == 4) {
        num_of_coords_pack = 0;
      }
      switch (num_of_coords_pack) {
      case 0:
        mqtt.publish(mqtt_pub_topic_lon, "63.681564");
        mqtt.publish(mqtt_pub_topic_lat, "67.608174");
        return_coord_pac = true;
        break;
      case 1:
        mqtt.publish(mqtt_pub_topic_lon, "63.896484");
        mqtt.publish(mqtt_pub_topic_lat, "67.648944");
        return_coord_pac = true;
        break;
      case 2:
        mqtt.publish(mqtt_pub_topic_lon, "64.13887");
        mqtt.publish(mqtt_pub_topic_lat, "67.627261");
        return_coord_pac = true;
        break;
      case 3:
        mqtt.publish(mqtt_pub_topic_lon, "63.92601");
        mqtt.publish(mqtt_pub_topic_lat, "67.584098");
        return_coord_pac = true;
        break;
      }
    }
  }
}
