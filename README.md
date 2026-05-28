# Plant Monitor

Plant Monitor is a system for tracking plant growth with an ESP32-CAM and a Flask web dashboard.

## Features

- Receives images from ESP32-CAM.
- Detects plant height from the image.
- Uses a yellow pencil as a reference object for scale calibration.
- Saves measurements to a CSV file.
- Shows current height, measurement history, and the latest processed image in a web dashboard.

## Project Structure

```text
server.py                  Flask server and image processing logic
templates/index.html       Web dashboard
static/style.css           Styles
data/plant_growth.csv      Measurement history
ESP32_CAM_Code/            ESP32-CAM Arduino sketch
requirements.txt           Python dependencies
```

## Server Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Flask server:

```bash
python server.py
```

Open the dashboard:

```text
http://127.0.0.1:5000
```

## ESP32-CAM Setup

In `ESP32_CAM_Code/ESP32_CAM_Code.ino`, set your Wi-Fi name and password:

```cpp
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
```

Set the server URL to your computer IP address:

```cpp
const char* serverUrl = "http://YOUR_PC_IP:5000/upload";
```

Then upload the sketch to the ESP32-CAM.

## API Endpoints

```text
GET  /              Web dashboard
POST /upload        Upload image from ESP32-CAM
GET  /api/status    Current system status
GET  /api/history   Measurement history
GET  /api/image     Latest processed image
```
