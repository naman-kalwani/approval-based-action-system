from langchain_core.tools import tool
import smtplib
from email.message import EmailMessage 
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
load_dotenv()

class EmailToolInput(BaseModel):
  to: str
  subject: str
  body: str

@tool("email_tool")
def email_tool(input: EmailToolInput) -> str:
  """A tool to send an email using Gmail SMTP."""
  
  print(os.getenv("EMAIL_ADDRESS"))
  print(os.getenv("EMAIL_PASSWORD"))
  email_address = os.getenv("EMAIL_ADDRESS") 
  email_password = os.getenv("EMAIL_PASSWORD")
  
  msg = EmailMessage()
  msg["From"] = email_address
  msg["To"] = input.to
  msg["Subject"] = input.subject  
  msg.set_content(input.body)
  
  try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
      smtp.login(email_address, email_password)
      smtp.send_message(msg)
      return  f"Email successfully sent to {input.to}"
  except Exception as e:
    return f"Failed to send email: {str(e)}"


