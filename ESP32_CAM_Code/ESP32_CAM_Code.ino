#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
const char* serverUrl = "http://84.252.75.99:5000/upload";
const uint32_t intervalMinutes = 10;
void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();
  Serial.println("🌱 PLANT MONITOR - ESP32-CAM");
  Serial.println("==============================");
  WiFi.begin(ssid, password);
  Serial.print("📡 Подключение к WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi подключён!");
    Serial.print("🌐 IP адрес: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Ошибка подключения к WiFi");
    ESP.restart();
  }
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Ошибка инициализации камеры: 0x%x", err);
    ESP.restart();
  }
  Serial.println("✅ Камера готова!");
  Serial.println("==============================");
  Serial.print("🕐 Интервал съёмки: ");
  Serial.print(intervalMinutes);
  Serial.println(" мин");
  Serial.print("📤 Сервер: ");
  Serial.println(serverUrl);
  Serial.println("==============================");
}
void loop() {
  captureAndSend();
  Serial.println("💤 Сон...");
  Serial.println();
  delay(intervalMinutes * 60 * 1000);
}
void captureAndSend() {
  Serial.println("📸 Съёмка...");
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Ошибка захвата кадра");
    return;
  }
  Serial.print("📦 Размер изображения: ");
  Serial.print(fb->len);
  Serial.println(" байт");
  WiFiClient client;
  HTTPClient http;
  if (http.begin(client, serverUrl)) {
    http.addHeader("Content-Type", "image/jpeg");
    http.addHeader("Content-Length", String(fb->len));
    Serial.print("📤 Отправка на сервер... ");
    int httpResponseCode = http.POST(fb->buf, fb->len);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.printf("✅ Успешно! HTTP %d\n", httpResponseCode);
      Serial.print("📥 Ответ сервера: ");
      Serial.println(response);
    } else {
      Serial.printf("❌ HTTP ошибка: %d\n", httpResponseCode);
      Serial.print("📥 Ответ: ");
      Serial.println(http.getString());
    }
    http.end();
  } else {
    Serial.println("❌ Ошибка подключения к серверу");
  }
  esp_camera_fb_return(fb);
  Serial.println("✅ Готово!");
}
