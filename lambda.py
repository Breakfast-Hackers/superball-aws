import http.client
import json

"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

valid_game_actions = ['start', 'stop', 'pause', 'weiter']
valid_directions = ['links', 'rechts']


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


def call_server(action_type, action):
    body = json.dumps({'action': action})
    headers = {"Content-type": "application/json"}
    conn = http.client.HTTPSConnection("superball.herokuapp.com")
    conn.request("POST", "/api/{}".format(action_type), body, headers)
    response = conn.getresponse()
    return response


def stop_game():
    call_server('game', 'stop')


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Willkommen bei Superball! " \
                    "beginne ein neues Spiel mit " \
                    "Spiel starten"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Ich hab dich nicht verstanden, " \
                    "aber du beginnst ein neues Spiel mit " \
                    "Spiel starten"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Danke, dass du Superball gespielt hast. " \
                    "Viel Spaß noch! "
    stop_game()
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def manage_game_in_session(intent, session):
    """ Manages the game state of play, pause, stop.
    """
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = "mach was!"

    if 'gameSlot' in intent['slots']:
        if 'value' in intent['slots']['gameSlot']:
            game_action = intent['slots']['gameSlot']['value']
        else:
            game_action = 'EMPTY'
        if game_action in valid_game_actions:
            response = call_server('game', game_action)
            if response.status == 200:
                speech_output = game_action + "!"
            else:
                speech_output = "Ooopsy. Der server sagt {}".format(response.status)
        else:
            print('unknown command: {}'.format(game_action))
            speech_output = "was denn, alter?"
    else:
        speech_output = "Ich weiß nicht was du machen möchtest." \
                        "Probier es nochmal."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def manage_direction_in_session(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = "links oder rechts?"

    if 'directionSlot' in intent['slots']:
        if 'value' in intent['slots']['directionSlot']:
            direction_movement = intent['slots']['directionSlot']['value']
        else:
            direction_movement = 'EMPTY'
        if direction_movement in valid_directions:
            session_attributes = dict()
            response = call_server('direction', direction_movement)
            if response.status == 200:
                speech_output = direction_movement + "!"
            else:
                speech_output = "Ooopsy. Der server sagt {}".format(response.status)
        else:
            print('unknown command: {}'.format(direction_movement))
            speech_output = 'Nein, man!'
    else:
        speech_output = "Ich weiß nicht wo du hin willst. " \
                        "versuche es nochmal."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GameIntent":
        return manage_game_in_session(intent, session)
    elif intent_name == "DirectionIntent":
        return manage_direction_in_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    stop_game()
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
