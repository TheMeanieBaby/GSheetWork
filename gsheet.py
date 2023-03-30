import streamlit as st
import cohere
import openai
import os.path
from cohere.responses.classify import Example
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

COHERE_API_KEY = 'secret'
co_client = cohere.Client(COHERE_API_KEY)

api_key = 'secret'

# Google Sheets API configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1-tlggreTx5Wk1fPAdhfkC0LjdEnuyh5pkluXdH13At4'
LEADERBOARD_RANGE = 'Sheet1!A2:C'


# Get Google Sheets API credentials

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
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

    #values = [['pat', 'like', 9]]


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
            f"{i + 1}. {entry.username}: {entry.comment} ({entry.score})")


display_leaderboard()

with st.form(key='comment_form'):
    username = st.text_input("Username")
    comment = st.text_area("Comment")
    progress_bar = st.progress(0)
    submit_button = st.form_submit_button("Submit")

if submit_button:
    progress_bar.progress(25)
    examples = [
        Example("you are hot trash", "Toxic"),
        Example("go to hell", "Toxic"),
        Example("get rekt moron", "Toxic"),
        Example("get a brain and use it", "Toxic"),
        Example("say what you mean, you jerk.", "Toxic"),
        Example("Are you really this stupid", "Toxic"),
        Example("I will honestly kill you", "Toxic"),
        Example("yo how are you", "Benign"),
        Example("I'm curious, how did that happen", "Benign"),
        Example("Try that again", "Benign"),
        Example("Hello everyone, excited to be here", "Benign"),
        Example("I think I saw it first", "Benign"),
        Example("That is an interesting point", "Benign"),
        Example("I love this", "Benign"),
        Example("We should try that sometime", "Benign"),
        Example("You should go for it", "Benign")
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

openai.api_key = "secret"
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
