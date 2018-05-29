from __future__ import print_function

from rasahub import RasahubPlugin

from flask import Flask, render_template, session, request, redirect, url_for, abort, jsonify
from authlib.client import OAuth2Session
import json
import sys

is_py2 = sys.version[0] == '2'
if is_py2:
    import thread as thread
else:
    import _thread as thread
import requests

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from oauth2client.client import AccessTokenCredentials, AccessTokenCredentialsError, OAuth2WebServerFlow, GoogleCredentials
from oauth2client.file import Storage

import datetime, time

app = Flask(__name__)
client = 0
client_id = 0
client_secret = 0

def flaskThread():
    """
    Start flask webserver
    """
    app.run(debug=False, host='localhost', port=8080)

class RasaGoogleCalendar(RasahubPlugin):
    """
    Class RasaGoogleCalendar serves as a API to access Google Calendars. It handles
    auth process and token management.
    """
    def __init__(self, **kwargs):
        """
        As a Rasahub plugin initialize itself and create OAuth Server Flow
        """
        super(RasaGoogleCalendar, self).__init__()

        self.client_id = kwargs.get('client_id', '')
        self.client_secret = kwargs.get('client_secret', '')
        self.redirect_uri = kwargs.get('redirect_uri', 'http://localhost:8080/oauth2callback')
        self.scope = kwargs.get('scope', 'https://www.googleapis.com/auth/calendar')

        global client
        global client_id
        global client_secret
        client = OAuth2WebServerFlow(client_id=self.client_id,
                                   client_secret=self.client_secret,
                                   scope=self.scope,
                                   redirect_uri=self.redirect_uri,
                                   access_type='offline', # This is the default
                                   prompt='consent')
        client_id = self.client_id
        client_secret = self.client_secret

        app.secret_key = 'hello world'
        # start flask webserver
        thread.start_new_thread(flaskThread,())

def get_google_calendar_items(user_id):
    """
    Returns Google calendar items of a specific user

    :param int user_id: (Humhub) User ID
    :return: Busy appointments
    :rtype: list
    """
    global client_id
    global client_secret

    with open('tokens.json') as f:
        try:
            data = json.load(f)
        except ValueError:
            raise AccessTokenCredentialsError
    credentials = GoogleCredentials(
        data[str(user_id)]['access_token'],
        client_id,
        client_secret,
        data[str(user_id)]['refresh_token'],
        None,
        "https://accounts.google.com/o/oauth2/token",
        'my-user-agent/1.0'
    )
    service = build('calendar', 'v3', credentials=credentials)

    page_token = None
    # get utc time diff
    utcdiff = (time.mktime(time.localtime()) - time.mktime(time.gmtime())) / 60 / 60
    # check if diff is full-hour or half
    minutes = utcdiff * 2
    if minutes % 2: # full hour
        minutesoffset = '30'
    else: # half hour
        minutesoffset = '00'
    # check sign
    if utcdiff < 0:
        sign = '-'
    else:
        sign = '+'
    utcdiff = str(abs(int(utcdiff))).zfill(2)
    appointments = []
    while True:
        try:
            calendar_list = service.events().list(
                calendarId='primary', # TODO handle other calendars too
                timeMin=time.strftime("%Y-%m-%dT00:00:00")+sign+utcdiff+':'+minutesoffset,
                timeMax=time.strftime("%Y-%m-%dT23:59:59")+sign+utcdiff+':'+minutesoffset,
                pageToken=page_token).execute()
        except AccessTokenCredentialsError:
            # re-auth
            raise AccessTokenCredentialsError

        # collect busy appointments
        for calendar_list_entry in calendar_list['items']:
            appointments.append({"start": calendar_list_entry['start']['dateTime'][:-6], "end": calendar_list_entry['end']['dateTime'][:-6]}) # remove utc diff
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    return appointments


    @app.route('/login')
    def login():
        """
        Handles login process, gets auth url

        :return: Redirect to auth url
        """
        global client
        auth_uri = client.step1_get_authorize_url()
        return redirect(auth_uri)


    @app.route('/oauth2callback')
    def oauth2callback():
        """
        Handles token exchange, saves token

        :return: Redirect to index
        """
        code = request.args.get('code')
        credentials = client.step2_exchange(code)

        # save credentials
        with open('tokens.json') as f:
            try:
                data = json.load(f)
            except ValueError:
                data = {}

        token = {}
        token['refresh_token'] = credentials.refresh_token
        token['access_token'] = credentials.access_token
        token['token_expiry'] = time.mktime(credentials.token_expiry.timetuple()) # read: datetime.fromtimestamp(<timestamp>)
        data[session['user_id']] = token

        # store credentials
        with open('tokens.json', mode='w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile)

        # redirect to index
        return redirect(url_for('index'))


    @app.route('/')
    @app.route('/<int:user_id>')
    def index(user_id = 0):
        """
        Main page, displays calendar items if logged in, redirects to login otherwise

        :param int user_id: (Humhub) User ID
        """
        # check user id
        if (user_id == 0):
            if session is not None and 'user_id' in session and session['user_id'] is not None:
                user_id = session['user_id']
            else:
                return "No User ID specified."
        else:
            session['user_id'] = user_id

        # check if token is available for user
        with open('tokens.json') as f:
            try:
                data = json.load(f)
            except ValueError:
                return redirect(url_for('login'))
        body = ""
        if str(user_id) in data:
            global client_id
            global client_secret
            credentials = GoogleCredentials(
                data[str(user_id)]['access_token'],
                client_id,
                client_secret,
                data[str(user_id)]['refresh_token'],
                None,
                "https://accounts.google.com/o/oauth2/token",
                'my-user-agent/1.0'
            )
            #credentials = AccessTokenCredentials(data[str(user_id)]['access_token'], 'my-user-agent/1.0')
            service = build('calendar', 'v3', credentials=credentials)

            page_token = None
            # get utc time diff
            utcdiff = (time.mktime(time.localtime()) - time.mktime(time.gmtime())) / 60 / 60
            # check if diff is full-hour or half
            minutes = utcdiff * 2
            if minutes % 2: # full hour
                minutesoffset = '30'
            else: # half hour
                minutesoffset = '00'
            # check sign
            if utcdiff < 0:
                sign = '-'
            else:
                sign = '+'
            utcdiff = str(abs(int(utcdiff))).zfill(2)
            appointments = []
            while True:
                try:
                    calendar_list = service.events().list(
                        calendarId='primary', # TODO handle other calendars too
                        timeMin=time.strftime("%Y-%m-%dT00:00:00")+sign+utcdiff+':'+minutesoffset,
                        timeMax=time.strftime("%Y-%m-%dT23:59:59")+sign+utcdiff+':'+minutesoffset,
                        pageToken=page_token).execute()
                except AccessTokenCredentialsError:
                    # re-auth
                    return redirect(url_for('login'))

                for calendar_list_entry in calendar_list['items']:
                    appointments.append({"start": calendar_list_entry['start']['dateTime'][:-6], "end": calendar_list_entry['end']['dateTime'][:-6]}) # remove utc diff
                page_token = calendar_list.get('nextPageToken')
                if not page_token:
                    break

            for event in appointments:
                body += json.dumps(event)
        else:
            return redirect(url_for('login'))
        return body
