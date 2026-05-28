
from flask import Flask, request, jsonify, render_template, send_file
import cv2
import numpy as np
import datetime
import os
import json
from pathlib import Path

app = Flask(__name__)

REFERENCE_REAL_HEIGHT_CM = 16.0
PIXELS_PER_CM = None

GREEN_RANGE = ((35, 40, 40), (85, 255, 255))
YELLOW_RANGE = ((15, 80, 80), (40, 255, 255))

DATA_DIR = Path("data")
STATIC_DIR = Path("static")
DATA_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

CSV_FILE = DATA_DIR / "plant_growth.csv"
LAST_IMAGE = STATIC_DIR / "last_image.jpg"

def get_object_height_px(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0, None
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    return h, (x, y, w, h)

def log_measurement(height_cm, plant_px, pencil_px):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    write_header = not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0

    with open(CSV_FILE, "a", encoding="utf-8") as f:
        if write_header:
            f.write("timestamp,height_cm,plant_pixels,pencil_pixels,px_per_cm\n")
        px_per_cm = PIXELS_PER_CM if PIXELS_PER_CM else 0
        f.write(f"{timestamp},{height_cm:.2f},{plant_px},{pencil_px},{px_per_cm:.2f}\n")

def get_measurements_history(limit=100):
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        return []

    try:
        import pandas as pd
        df = pd.read_csv(CSV_FILE)

        if 'timestamp' not in df.columns or 'height_cm' not in df.columns:
            print("⚠️ CSV имеет неверный формат, создаём новый...")
            return []

        df = df.tail(limit)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        return df.to_dict('records')
    except Exception as e:
        print(f"⚠️ Ошибка чтения CSV: {e}")
        return []

def process_image(image_bytes):
    global PIXELS_PER_CM

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None, "Invalid image"

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, GREEN_RANGE[0], GREEN_RANGE[1])
    yellow_mask = cv2.inRange(hsv, YELLOW_RANGE[0], YELLOW_RANGE[1])

    kernel = np.ones((5,5), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)

    plant_h, plant_bbox = get_object_height_px(green_mask)
    pencil_h, pencil_bbox = get_object_height_px(yellow_mask)

    if pencil_h == 0:
        return None, "Yellow pencil not found! Check lighting and HSV range."

    if PIXELS_PER_CM is None:
        PIXELS_PER_CM = pencil_h / REFERENCE_REAL_HEIGHT_CM
        print(f"✅ КАЛИБРОВКА: {PIXELS_PER_CM:.2f} px/cm (карандаш {pencil_h}px = 16 см)")

    plant_height_cm = plant_h / PIXELS_PER_CM if PIXELS_PER_CM else 0

    if plant_bbox:
        x, y, w, h = plant_bbox
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(img, f"Plant: {plant_height_cm:.1f}cm", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if pencil_bbox:
        x, y, w, h = pencil_bbox
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 255, 0), 2)
        cv2.putText(img, "Ref: 16cm", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imwrite(str(LAST_IMAGE), img)

    log_measurement(plant_height_cm, plant_h, pencil_h)

    print(f"🌱 Измерение: {plant_height_cm:.2f} см | Карандаш: {pencil_h}px | Растение: {plant_h}px")

    return {
        "height_cm": round(plant_height_cm, 2),
        "plant_pixels": plant_h,
        "pencil_pixels": pencil_h,
        "px_per_cm": round(PIXELS_PER_CM, 2) if PIXELS_PER_CM else None,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    try:
        history = get_measurements_history(1)
        latest = history[0] if history else {}
        return jsonify({
            "calibrated": PIXELS_PER_CM is not None,
            "px_per_cm": round(PIXELS_PER_CM, 2) if PIXELS_PER_CM else None,
            "latest_measurement": latest,
            "total_measurements": len(get_measurements_history(1000))
        })
    except Exception as e:
        print(f"⚠️ Ошибка в api_status: {e}")
        return jsonify({
            "calibrated": PIXELS_PER_CM is not None,
            "px_per_cm": round(PIXELS_PER_CM, 2) if PIXELS_PER_CM else None,
            "latest_measurement": {},
            "total_measurements": 0,
            "error": str(e)
        }), 200

@app.route('/api/history')
def api_history():
    return jsonify(get_measurements_history(100))

@app.route('/upload', methods=['POST'])
def upload():
    if request.data:
        result, error = process_image(request.data)
        if error:
            return jsonify({"error": error}), 400
        return jsonify(result)
    return jsonify({"error": "No image data"}), 400

@app.route('/upload', methods=['GET'])
def upload_get():
    return '''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Plant Monitor API</title>
    <style>body{font-family:sans-serif;max-width:600px;margin:50px auto;padding:20px;
    background:linear-gradient(135deg,#667eea,#764ba2);color:white;border-radius:15px;}
    a{color:#fff;font-weight:bold;}</style></head>
    <body>
    <h2>Plant Monitor API</h2>
    <p>This endpoint accepts <strong>POST requests</strong> with images from ESP32-CAM.</p>
    <p><a href="/">Open monitoring dashboard</a></p>
    <p><a href="/api/status">System status (JSON)</a></p>
    <p><a href="/api/image">Latest image</a></p>
    </body></html>
    ''', 200

@app.route('/api/image')
def get_image():
    if os.path.exists(LAST_IMAGE):
        return send_file(LAST_IMAGE, mimetype='image/jpeg')
    return jsonify({"error": "No image yet"}), 404

if __name__ == '__main__':
    print("=" * 60)
    print("🌱 PLANT GROWTH MONITORING SYSTEM")
    print("=" * 60)
    print(f"📁 Data directory: {DATA_DIR.absolute()}")
    print(f"📊 CSV file: {CSV_FILE.absolute()}")
    print(f"🖼️  Last image: {LAST_IMAGE.absolute()}")
    print("=" * 60)
    print("🌐 Запуск веб-сервера...")
    print(f"📱 Веб-панель: http://127.0.0.1:5000")
    print(f"🌐 По сети:   http://192.168.0.4:5000")
    print(f"📡 ESP32 отправляйте на: http://192.168.0.4:5000/upload")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False, threaded=True)
