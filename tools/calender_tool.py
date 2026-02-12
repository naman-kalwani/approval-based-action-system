from langchain_core.tools import tool
from pydantic import BaseModel
from datetime import datetime, timedelta
from dateutil import parser
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarEventInput(BaseModel):
  event_name: str
  date: str   # format: YYYY-MM-DD
  time: str   # format: HH:MM (24hr)


def get_calendar_service():
  creds = None

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(
      "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
      token.write(creds.to_json())

  return build("calendar", "v3", credentials=creds)

@tool("calendar_tool")
def calendar_tool(input: CalendarEventInput) -> str:
  """Create a Google Calendar event from name, date, and time."""

  try:
    service = get_calendar_service()

    start_datetime = parser.parse(f"{input.date} {input.time}")
    end_datetime = start_datetime + timedelta(hours=1)

    if start_datetime < datetime.now():
      return "Cannot create event in the past."

    event = {
      "summary": input.event_name,
      "start": {
        "dateTime": start_datetime.isoformat(),
        "timeZone": os.getenv("TIMEZONE", "Asia/Kolkata"),
      },
      "end": {
        "dateTime": end_datetime.isoformat(),
        "timeZone": os.getenv("TIMEZONE", "Asia/Kolkata"),
      },
    }

    created_event = service.events().insert(
      calendarId="primary",
      body=event
    ).execute()

    return f"Event created successfully: {created_event.get('htmlLink')}"

  except Exception as e:
    return f"Failed to create calendar event: {str(e)}"
