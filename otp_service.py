import os
import base64
import hashlib
import secrets

from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    GMAIL_SENDER,
    GMAIL_CLIENT_SECRET,
    GMAIL_TOKEN_FILE,
)

from attendance_db import store_otp_session

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


def generate_otp(length=6):

    lower = 10 ** (length - 1)
    upper = (10 ** length) - 1

    return str(
        secrets.randbelow(
            upper - lower + 1
        ) + lower
    )


def hash_otp(otp):

    return hashlib.sha256(
        otp.encode()
    ).hexdigest()


def get_gmail_service():

    creds = None

    if os.path.exists(GMAIL_TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            GMAIL_TOKEN_FILE,
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:

            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CLIENT_SECRET,
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        with open(
            GMAIL_TOKEN_FILE,
            "w"
        ) as token:

            token.write(
                creds.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


def send_email_otp(
    recipient_email,
    student_name,
    otp
):

    service = get_gmail_service()
    html_body = f"""
    <html>
    <body style="margin: 0; padding: 0; background-color: #f4f7f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding: 20px;">
            <tr>
                <td align="center">
                    <div style="max-width: 600px; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                        <div style="background-color: #0056b3; color: white; padding: 30px 20px; text-align: center;">
                            <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;">Authentication Required</h1>
                            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">RV College of Engineering</p>
                        </div>
                        <div style="padding: 40px 30px; text-align: center;">
                            <p style="font-size: 16px; color: #333; margin-bottom: 25px;">Hello <b>{student_name}</b>,</p>
                            <p style="font-size: 15px; color: #555; margin-bottom: 30px;">A login attempt was detected. Please use the following One-Time Password (OTP) to verify your identity.</p>
                            
                            <div style="background-color: #f8f9fa; border: 2px dashed #0056b3; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                                <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #0056b3;">{otp}</span>
                            </div>
                            
                            <p style="font-size: 13px; color: #888;">This code is valid for a limited time. If you did not request this, please ignore this email.</p>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
     
    message = MIMEText(
        html_body,
        "html"
    )

    message["to"] = recipient_email
    message["from"] = GMAIL_SENDER

    message["subject"] = (
        "RVCE Smart Attendance Verification OTP"
    )

    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={
            "raw": raw
        }
    ).execute()


def issue_otp(
    student_id,
    email,
    student_name
):

    otp = generate_otp()

    otp_hash = hash_otp(
        otp
    )

    store_otp_session(
        student_id,
        email,
        otp_hash
    )

    send_email_otp(
        email,
        student_name,
        otp
    )

    return otp_hash
   

def send_attendance_report(
    email,
    student_name,
    attended,
    total,
    percentage
):

    service = get_gmail_service()

    if percentage >= 85:
        status = "Excellent"
        color = "#28a745"

    elif percentage >= 75:
        status = "Good"
        color = "#17a2b8"

    elif percentage >= 65:
        status = "Average"
        color = "#ffc107"

    else:
        status = "Low"
        color = "#dc3545"

    html_body = f"""
    <html>

    <body style="
        background:#f4f6f9;
        font-family:Arial,sans-serif;
        padding:30px;
    ">

    <div style="
        max-width:700px;
        margin:auto;
        background:white;
        border-radius:20px;
        overflow:hidden;
        box-shadow:0 0 20px rgba(0,0,0,0.15);
    ">

        <div style="
            background:{color};
            color:white;
            text-align:center;
            padding:30px;
        ">

            <h1>
                Attendance Recorded Successfully
            </h1>

            <h3>
                RV College of Engineering
            </h3>

        </div>

        <div style="padding:35px;">

            <p>
                Hello <b>{student_name}</b>,
            </p>

            <p>
                Your attendance has been successfully
                recorded in the Smart Attendance System.
            </p>

            <table style="
                width:100%;
                border-collapse:collapse;
                margin-top:20px;
            ">

                <tr>
                    <td style="padding:12px;">
                        <b>Classes Attended</b>
                    </td>
                    <td style="padding:12px;">
                        {attended}
                    </td>
                </tr>

                <tr>
                    <td style="padding:12px;">
                        <b>Total Classes</b>
                    </td>
                    <td style="padding:12px;">
                        {total}
                    </td>
                </tr>

                <tr>
                    <td style="padding:12px;">
                        <b>Attendance Percentage</b>
                    </td>
                    <td style="padding:12px;">
                        {percentage:.2f}%
                    </td>
                </tr>

                <tr>
                    <td style="padding:12px;">
                        <b>Status</b>
                    </td>
                    <td style="
                        padding:12px;
                        color:{color};
                    ">
                        <b>{status}</b>
                    </td>
                </tr>

            </table>

            <div style="
                margin-top:30px;
                background:#f8f9fa;
                border-left:8px solid {color};
                padding:20px;
                border-radius:8px;
            ">

                <h2 style="margin:0;">
                    Current Attendance:
                    {percentage:.2f}%
                </h2>

            </div>

            <br>

            <p style="
                font-size:12px;
                color:gray;
            ">
                AI Smart Attendance System
                <br>
                Department of Computer Science and Engineering
                <br>
                RV College of Engineering
            </p>

        </div>

    </div>

    </body>

    </html>
    """

    message = MIMEText(
        html_body,
        "html"
    )

    message["to"] = email

    message["from"] = GMAIL_SENDER

    message["subject"] = (
        "Attendance Successfully Recorded"
    )

    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={
            "raw": raw
        }
    ).execute()
