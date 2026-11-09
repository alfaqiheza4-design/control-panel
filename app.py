from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Daftar HP yang terdaftar
devices = {
    "hp_anak_1": {"name": "HP Anak Utama", "status": "online"},
    "hp_anak_2": {"name": "HP Cadangan", "status": "offline"}
}

# Nyimpen perintah buat masing-masing HP
latest_commands = {
    "hp_anak_1": "none",
    "hp_anak_2": "none"
}

# Halaman Depan: Daftar Perangkat
@app.route('/')
def index():
    return render_template('index.html', devices=devices)

# Halaman Kontrol per HP
@app.route('/device/<device_id>')
def device_panel(device_id):
    if device_id not in devices:
        return "Perangkat tidak ditemukan", 404
    return render_template('panel.html', device_id=device_id, device=devices[device_id])

# Endpoint terima perintah dari Web
@app.route('/api/command/<device_id>', methods=['POST'])
def receive_command(device_id):
    if device_id not in devices:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    data = request.json
    latest_commands[device_id] = data.get("command")
    print(f"[SERVER] Perintah masuk untuk {device_id}: {latest_commands[device_id]}")
    return jsonify({"status": "success", "received": latest_commands[device_id]})

# Endpoint dibaca oleh APK Target
@app.route('/api/get_command/<device_id>', methods=['GET'])
def get_command(device_id):
    if device_id not in devices:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    cmd = latest_commands.get(device_id, "none")
    latest_commands[device_id] = "none"
    return jsonify({"command": cmd})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
