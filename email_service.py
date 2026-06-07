import os.path
import base64
from email.mime.text import MIMEText

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    pass

GMAIL_SENDER = "your_actual_email@gmail.com" 
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("\n[WARNING] 'credentials.json' not found! Cannot send Gmail.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_attendance_report(email, student_name, attended, total, percentage):
    service = get_gmail_service() 
    if service is None:
        return
    
    # Corrected HTML body with placeholders for 'total' and 'percentage'
    html_body = f"""
    <html>
    <body style="margin: 0; padding: 0; background-color: #f4f7f6; font-family: sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding: 20px;">
            <tr>
                <td align="center">
                    <div style="max-width: 600px; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                        <div style="background-color: #28a745; color: white; padding: 30px 20px; text-align: center;">
                            <h1 style="margin: 0; font-size: 24px;">Attendance Verified</h1>
                        </div>
                        <div style="padding: 40px 30px;">
                            <p style="font-size: 16px;">Hello <b>{student_name}</b>,</p>
                            
                            <table width="100%" cellpadding="15" cellspacing="0" style="background-color: #f8f9fa; border-radius: 8px;">
                                <tr>
                                    <td>Classes Attended</td>
                                    <td align="right"><b>{attended}</b></td>
                                </tr>
                                <tr>
                                    <td>Total Classes Conducted</td>
                                    <td align="right"><b>{total}</b></td>
                                </tr>
                                <tr>
                                    <td style="border-top: 2px solid #ddd;"><b>Attendance Percentage</b></td>
                                    <td align="right" style="border-top: 2px solid #ddd; color: #0056b3;"><b>{percentage:.1f}%</b></td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    message = MIMEText(html_body, "html")
    message["to"] = email
    message["from"] = GMAIL_SENDER 
    message["subject"] = "Attendance Report"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"Email report successfully sent to {email}")
    except Exception as e:
        print(f"\n[ERROR] Failed to send email: {e}")
