# 2-Factor-Authentication-and-IoT-based-Smart-Attendance-System-for-Institutions-and-Workplaces
IoT-based system for attendance by merging 2FA security with facial recognition. Requires both a physical face scan and a dynamic OTP, eliminates buddy punching. Designed for institutions, provides real-time, cloud-synced data and mobile-integrated management, ensuring a seamless, secure, and fully auditable attendance process for all workplaces.

This **Smart Attendance System** leverages IoT hardware and computer vision to provide a secure, automated solution for institutions and workplaces. It eliminates manual errors and "buddy punching" by requiring two-factor verification: a physical face scan and a time-sensitive OTP.

---

### **System Overview**

* **Location-Locked Security**: Attendance is restricted exclusively to the classroom environment; the system is configured to work only on the designated class network, ensuring that users must be physically present to sign in.
* **Facial Recognition**: Automatically detects and matches faces against a registered database.
* **2FA Security**: Requires a secondary OTP verification via a dedicated web app for every attendance entry.
* **Admin Dashboard**: A mobile-responsive web panel to manage class counts, monitor attendance in real-time, and perform administrative "undo" actions.
* **Cloud Synchronization**: Integrates with Firebase to ensure data availability across devices.
* **Automated Reporting**: Sends personalized attendance summaries via Gmail API.

---

### **Getting Started**

#### **1. Prerequisites**

Ensure you have Python 3.13+ installed and a Raspberry Pi (or Linux machine) with a connected camera.

```bash
sudo apt update
sudo apt install python3-venv sqlite3 -y

```

#### **2. Environment Setup**

```bash
# Clone your project and enter directory
git clone https://github.com/ishaanparikh14/2-Factor-Authentication-and-IoT-based-Smart-Attendance-System-for-Institutions-and-Workplaces.git
cd 2-Factor-Authentication-and-IoT-based-Smart-Attendance-System-for-Institutions-and-Workplaces

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask google-api-python-client google-auth-httplib2 google-auth-oauthlib opencv-python firebase-admin requests

```

#### **3. Database Initialization**

The system creates the `attendance.db` automatically on first run. To ensure a fresh start:

```bash
# Remove old DB to force a fresh schema creation
rm attendance.db

```

#### **4. Model Configuration**

The ArcFace model is not included due to size limits. Initialize it automatically:

```bash
python3 download_models.py

```

#### **5. Configuring Credentials**

Place your `credentials.json` (for Gmail/Firebase APIs) in the `/home/pi/face_attendance/` folder. Ensure your `GMAIL_SENDER` email is updated in `email_service.py`.

#### **6. Running the System**

You must run the two core components simultaneously in separate terminal sessions:

**Terminal 1: Start the Web/Admin Server**

```bash
source venv/bin/activate
python app.py
# The web interface is available at http://<PI_IP>:5000 (accessible only via class Wi-Fi)

```

**Terminal 2: Start the Attendance/Camera Loop**

```bash
source venv/bin/activate
python main.py

```

### **Architectural Workflow**

1. **Network Validation**: The system validates the request source; attendance requests from outside the local class network are automatically rejected.
2. **Detection**: `main.py` processes live camera frames.
3. **Verification**: Upon a face match, the user is prompted to enter an OTP from the web app.
4. **Sync**: `attendance_db.py` updates the local SQLite store, triggers the email report, and pushes the final data to Firebase.
5. **Admin Review**: The lecturer uses the `/admin` route to manage total sessions and view real-time statistics.

For troubleshooting, ensure your Raspberry Pi is connected to the same local network as the students' devices, and verify that the `credentials.json` has the correct `gmail.send` scope permissions.
