import os 
import requests
import json
import streamlit as st
from datetime import datetime, timedelta
from apikey import OPENAI_API_KEY, OPEN_WEATHER_API_KEY
from openai import OpenAI
from datetime import datetime

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY


# Set up OpenAI client
client = OpenAI()


slot_url = 'https://api.cal.com/v1/slots'
def get_available_slots():
    def start_end():
        """
        Returns start date as tomorrow and end as one week after start
        """
        # Get today's date
        today = datetime.now()

        # Calculate tomorrow's date
        tomorrow = today + timedelta(days=1)
        one_week = today + timedelta(days =8)

        # Format tomorrow's date as 'YYYY-MM-DD'
        formatted_tomorrow = tomorrow.strftime('%Y-%m-%d')
        formatted_one_week = one_week.strftime('%Y-%m-%d')
        return formatted_tomorrow, formatted_one_week
    start_time, end_time =start_end()


    response = requests.get(slot_url + f"?apiKey={OPEN_WEATHER_API_KEY}" + f"&eventTypeId={873991}"+ f"&startTime={start_time}" + f"&endTime={end_time}")
    if response.status_code == 200:
        print('Request successful')

    else:
        print('Request failed')
        print(response.status_code, response.text)
    return response.json()

book_url = "https://api.cal.com/v1/bookings"

def book_slot(startTime, description):
    data = {
        "eventTypeId": 873991,
        "start": startTime,
        "description": description,
        "responses": {},
        "metadata": {},
        "language": "en",
        "timeZone": "America/Los_Angeles",
        "user": "prashant.sharma@gmail.com", 
        "responses": {
            "email": "prashant.abudhabi@gmail.com",
            "name": "Prashant Sharma",
            "location": {
                "optionValue": "",
                "value": "inPerson"
            }
        }
    }
    response = requests.post(book_url + f"?apiKey={OPEN_WEATHER_API_KEY}", json=data)
    
    return response.json()

def process_user_input(user_input):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that manages meetings and schedules."},
            {"role": "user", "content": user_input}
        ],
        functions=[
            {
                "name": "interpret_request",
                "description": "Interprets the user's request and categorizes it",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["book_meeting", "show_events", "show_available_slots" "other"],
                            "description": "The type of action requested by the user"
                        },
                        "details": {
                            "type": "string",
                            "description": "Any additional details extracted from the request"
                        }
                    },
                    "required": ["action"]
                }
            }
        ],
        function_call={"name": "interpret_request"}
    )

    return json.loads(response.choices[0].message.function_call.arguments)

def show_events():
    response =requests.get(book_url + f"?apiKey={OPEN_WEATHER_API_KEY}" )
    return response.json()

st.title("Meeting Scheduler Assistant")

user_input = st.text_input("How can I assist you with scheduling?")

if st.button("Submit"):
    if user_input:
        interpretation = process_user_input(user_input)
        
        if interpretation['action'] == "book_meeting":
            st.session_state.booking_state = 'datetime'
            st.session_state.booking_details = {}
            st.info("Let's book a meeting within this week. Please provide the following details.")
            st.text_input("Start Time (YYYY-MM-DDTHH:MM:SS, e.g., 2024-07-01T09:00:00):", key="meeting_datetime")
        
        elif interpretation['action'] == "show_events":
            st.info(show_events())

        elif interpretation['action'] == 'show_available_slots':
            st.info(get_available_slots())
        
        else:
            st.info("I'm sorry, I didn't understand that request. Can you please try again?")

if 'booking_state' in st.session_state:
    if st.session_state.booking_state == 'datetime':
        if st.session_state.meeting_datetime:
            st.session_state.booking_details['startTime'] = st.session_state.meeting_datetime
            st.session_state.booking_state = 'description'
            st.text_input("Meeting Description:", key="meeting_description")
    
    elif st.session_state.booking_state == 'description':
        if st.session_state.meeting_description:
            st.session_state.booking_details['description'] = st.session_state.meeting_description
            result = book_slot(
                st.session_state.booking_details['startTime'],
                st.session_state.booking_details['description']
            )
            if 'id' in result:
                st.success(f"Meeting booked successfully! Booking ID: {result['id']}")
            else:
                st.error(f"Failed to book meeting. Error: {result.get('message', 'Unknown error')}")
            del st.session_state.booking_state
            del st.session_state.booking_details

st.write("Type 'help me to book a meeting' to schedule a new meeting or 'show me the scheduled events' to see your calendar or 'show me available slots' to see slots available this week.")