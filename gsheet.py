import streamlit as st
import cohere
import openai
import os.path
from cohere.classify import Example
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

COHERE_API_KEY = 'XXXXXXXXXXXXXXX'
co_client = cohere.Client(COHERE_API_KEY)

api_key='AIzaSyBVELSj3MCNsmFQRtr7a6DTLodBXIdXO4A'

# Google Sheets API configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1-tlggreTx5Wk1fPAdhfkC0LjdEnuyh5pkluXdH13At4'
LEADERBOARD_RANGE = 'Sheet1!A2:C'

# Get Google Sheets API credentials

def get_credentials():
    creds = None
    if os.path.exists('/Users/vaughn.robinson/Downloads/token.json'):
        creds = Credentials.from_authorized_user_file('/Users/vaughn.robinson/Downloads/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/Users/vaughn.robinson/Downloads/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('/Users/vaughn.robinson/Downloads/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Function to read leaderboard data from Google Sheets


def get_leaderboard_data():
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds, developerKey=api_key)
    result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range=LEADERBOARD_RANGE).execute()
    values = result.get('values', [])
    leaderboard = [LeaderboardEntry(
        row[0], row[1], float(row[2])) for row in values]
    return leaderboard

# Function to write leaderboard data to Google Sheets


def update_leaderboard_data(leaderboard):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds, developerKey=api_key)
    values = [[entry.username, entry.comment, entry.score]
              for entry in leaderboard]
    body = {'values': values}
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=LEADERBOARD_RANGE,
        valueInputOption='RAW', body=body).execute()
        
st.set_page_config(page_title="Snark Attack v2", layout="wide")
st.title("Snark Attack v2")


def calculate_mean_score(benign_confidence, toxic_confidence):
    return round(50 * (toxic_confidence - benign_confidence) + 50, 2)


class LeaderboardEntry:
    def __init__(self, username, comment, score):
        self.username = username
        self.comment = comment
        self.score = score


def display_leaderboard():
    leaderboard = get_leaderboard_data()
    st.sidebar.title("Leaderboard")
    for i, entry in enumerate(leaderboard):
        st.sidebar.markdown(
            f"{i+1}. {entry.username}: {entry.comment} ({entry.score})")


display_leaderboard()

with st.form(key='comment_form'):
    username = st.text_input("Username")
    comment = st.text_area("Comment")
    progress_bar = st.progress(0)
    submit_button = st.form_submit_button("Submit")

if submit_button:
    progress_bar.progress(25)
    examples = [
    ]
    inputs = [comment]
    response = co_client.classify(model='small', inputs=inputs, examples=examples)
    classifications = response.classifications
    progress_bar.progress(75)
    benign_confidence = classifications[0].labels["Benign"].confidence
    toxic_confidence = classifications[0].labels["Toxic"].confidence
    mean_score = calculate_mean_score(benign_confidence, toxic_confidence)
    new_entry = LeaderboardEntry(username, comment, mean_score)
    leaderboard = get_leaderboard_data()
    for i, entry in enumerate(leaderboard):
        if new_entry.score > entry.score:
            leaderboard.insert(i, new_entry)
            leaderboard.pop()
        break
    update_leaderboard_data(leaderboard)

openai.api_key = "sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": f"The comment is: {comment}"},
    ],
)

game_host_response = response["choices"][0]["message"]["content"]
st.write(f"basedSkyNet: {game_host_response}")
progress_bar.progress(100)
display_leaderboard()
