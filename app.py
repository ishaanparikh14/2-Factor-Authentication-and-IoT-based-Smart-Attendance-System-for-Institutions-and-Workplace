from flask import Flask, render_template, request, jsonify
from attendance_db import (
    verify_otp, 
    get_student_attendance, 
    get_total_classes, 
    increment_class_count, 
    decrement_class_count
)
from otp_service import hash_otp

app = Flask(__name__)

# --- Cache Prevention Hook ---
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# --- Student Portal Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    student_id = data.get('student_id')
    entered_otp = data.get('otp')

    if not student_id or not entered_otp:
        return jsonify({"success": False, "message": "Missing ID or OTP"}), 400

    entered_hash = hash_otp(entered_otp)

    if verify_otp(student_id, entered_hash):
        attended = get_student_attendance(student_id)
        return jsonify({
            "success": True, 
            "message": "Attendance Verified!",
            "attended": attended
        })
    else:
        return jsonify({"success": False, "message": "Invalid or Expired OTP"}), 401

# --- Admin Panel Routes ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Check password and perform action
        if request.form.get('password') == "RVCE123":
            action = request.form.get('action')
            if action == 'start':
                increment_class_count()
            elif action == 'undo':
                decrement_class_count()
    
    # Always fetch the latest total from DB before rendering
    total = get_total_classes()
    return render_template('admin.html', total=total)

if __name__ == '__main__':
    # host='0.0.0.0' allows connections from your hotspot
    app.run(host='0.0.0.0', port=5000, debug=True)
