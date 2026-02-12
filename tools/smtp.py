import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

msg = EmailMessage()
msg["From"] = os.getenv("EMAIL_ADDRESS")
msg["To"] = os.getenv("EMAIL_ADDRESS")
msg["Subject"] = "SMTP Test"
msg.set_content("Test email")

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
  smtp.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
  smtp.send_message(msg)

print("Email sent successfully")
