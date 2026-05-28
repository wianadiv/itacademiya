# Plant Monitor

Plant Monitor — это система для отслеживания роста растения с помощью ESP32-CAM и веб-панели на Flask.

## Возможности

- Принимает изображения с ESP32-CAM.
- Определяет высоту растения по изображению.
- Использует жёлтый карандаш как эталонный объект для калибровки масштаба.
- Сохраняет измерения в CSV-файл.
- Показывает текущую высоту, историю измерений и последнее обработанное изображение в веб-панели.

## Структура проекта

```text
server.py                  Flask-сервер и обработка изображений
templates/index.html       Веб-панель
static/style.css           Стили
data/plant_growth.csv      История измерений
ESP32_CAM_Code/            Скетч Arduino для ESP32-CAM
requirements.txt           Python-зависимости
```

## Запуск сервера

Установить зависимости:

```bash
pip install -r requirements.txt
```

Запустить Flask-сервер:

```bash
python server.py
```

Открыть веб-панель:

```text
http://127.0.0.1:5000
```

## Настройка ESP32-CAM

В файле `ESP32_CAM_Code/ESP32_CAM_Code.ino` нужно указать название и пароль от Wi-Fi:

```cpp
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
```

Также нужно указать адрес сервера, заменив `YOUR_PC_IP` на IP-адрес компьютера:

```cpp
const char* serverUrl = "http://YOUR_PC_IP:5000/upload";
```

После этого скетч можно загрузить на ESP32-CAM.

## API endpoints

```text
GET  /              Веб-панель
POST /upload        Загрузка изображения с ESP32-CAM
GET  /api/status    Текущий статус системы
GET  /api/history   История измерений
GET  /api/image     Последнее обработанное изображение
```
