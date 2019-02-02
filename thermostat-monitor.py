# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample that implements a text client for the Google Assistant Service."""

from constants import NestMode
import constants

import os
import logging
import json

from lxml import html
import re
import pyowm
import requests

import click
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)

try:
    from . import (
        assistant_helpers,
        browser_helpers,
    )
except (SystemError, ImportError):
    import assistant_helpers
    import browser_helpers

DEBUG = False

class TextAssistant(object):
    """Sample Assistant that supports text based conversations.

    Args:
      language_code: language for the conversation.
      device_model_id: identifier of the device model.
      device_id: identifier of the registered device instance.
      display: enable visual display of assistant response.
      channel: authorized gRPC channel for connection to the
        Google Assistant API.
      deadline_sec: gRPC deadline in seconds for Google Assistant API call.
    """

    def __init__(self, language_code, device_model_id, device_id,
                 display, channel, deadline_sec):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True
        self.display = display
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
            channel
        )
        self.deadline = deadline_sec

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False

    def assist(self, text_query):
        """Send a text request to the Assistant and playback the response.
        """
        def iter_assist_requests():
            config = embedded_assistant_pb2.AssistConfig(
                audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                    encoding='LINEAR16',
                    sample_rate_hertz=16000,
                    volume_percentage=0,
                ),
                dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                    language_code=self.language_code,
                    conversation_state=self.conversation_state,
                    is_new_conversation=self.is_new_conversation,
                ),
                device_config=embedded_assistant_pb2.DeviceConfig(
                    device_id=self.device_id,
                    device_model_id=self.device_model_id,
                ),
                text_query=text_query,
            )
            # Continue current conversation with later requests.
            self.is_new_conversation = False
            if self.display:
                config.screen_out_config.screen_mode = embedded_assistant_pb2.ScreenOutConfig.PLAYING
            req = embedded_assistant_pb2.AssistRequest(config=config)
            assistant_helpers.log_assist_request_without_audio(req)
            yield req

        text_response = None
        html_response = None
        for resp in self.assistant.Assist(iter_assist_requests(),
                                          self.deadline):
            assistant_helpers.log_assist_response_without_audio(resp)
            if resp.screen_out.data:
                html_response = resp.screen_out.data
            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                self.conversation_state = conversation_state
            if resp.dialog_state_out.supplemental_display_text:
                text_response = resp.dialog_state_out.supplemental_display_text
        return text_response, html_response

def get_mode(assistant):
  mode = NestMode.UNKNOWN
  parse_mode = query_assistant(assistant, constants.QUERY_MODE)

  if constants.HEAT in parse_mode:
    mode = NestMode.HEAT
  elif constants.ECO in parse_mode:
    mode = NestMode.ECO
  elif constants.OFF in parse_mode:
    mode = NestMode.OFF
  return mode
  
def get_inconditions(assistant, mode):
  humidity, temp, target = ('',)*3
  get_humidity = re.findall(r'[\d.]+[\d]+', query_assistant(assistant,constants.QUERY_INHUMIDITY))
  get_temp = re.findall(r'[\d.]+[\d]+', query_assistant(assistant, constants.QUERY_INTEMP))

  if((len(get_temp) > 0) & (len(get_humidity) > 0)):
    humidity = get_humidity[0]
    if (mode == NestMode.HEAT):
      temp = get_temp[0]
      if(len(get_temp) > 1):
        target = get_temp[0]
        temp = get_temp[1]
    elif (mode == NestMode.ECO):
      temp = get_temp[0]
      if(len(get_temp) > 1):
        target = get_temp[1]
    else:
      temp = get_temp[0]

  return (humidity, temp, target)

def query_assistant(assistant, query):
  response_text, response_html = assistant.assist(text_query=query)
  return parse_response(response_html)

def parse_response(response_html):
  tree = html.fromstring(response_html)
  return str(tree.xpath(constants.DIV_CLASS))

@click.command()
@click.option('--api-endpoint', default=constants.ASSISTANT_API_ENDPOINT,
              metavar='<api endpoint>', show_default=True,
              help='Address of Google Assistant API service.')
@click.option('--credentials',
              metavar='<credentials>', show_default=True,
              default=os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json'),
              help='Path to read OAuth2 credentials.')
@click.option('--device-model-id',
              metavar='<device model id>',
              required=True,
              help=(('Unique device model identifier, '
                     'if not specifed, it is read from --device-config')))
@click.option('--device-id',
              metavar='<device id>',
              required=True,
              help=(('Unique registered device instance identifier, '
                     'if not specified, it is read from --device-config, '
                     'if no device_config found: a new device is registered '
                     'using a unique id and a new device config is saved')))
@click.option('--lang', show_default=True,
              metavar='<language code>',
              default='en-US',
              help='Language code of the Assistant')
@click.option('--display', is_flag=True, default=False,
              help='Enable visual display of Assistant responses in HTML.')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Verbose logging.')
@click.option('--grpc-deadline', default=constants.DEFAULT_GRPC_DEADLINE,
              metavar='<grpc deadline>', show_default=True,
              help='gRPC deadline in seconds')
def main(api_endpoint, credentials,
         device_model_id, device_id, lang, display, verbose,
         grpc_deadline, *args, **kwargs):
    # Setup logging.
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Load OAuth 2.0 credentials.
    try:
        with open(credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
    except Exception as e:
        logging.error('Error loading credentials: %s', e)
        logging.error('Run google-oauthlib-tool to initialize '
                      'new OAuth 2.0 credentials.')
        return

    # Create an authorized gRPC channel.
    grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, api_endpoint)
    logging.info('Connecting to %s', api_endpoint)

    with TextAssistant(lang, device_model_id, device_id, display,
                             grpc_channel, grpc_deadline) as assistant:
        nest_mode = get_mode(assistant)

        # Variables
        home_temp = ''
        home_humidity = ''
        home_target = ''

        home_humidity, home_temp, home_target = get_inconditions(assistant, nest_mode)

        owm = pyowm.OWM(constants.OWM_API_KEY)
        observation = owm.weather_at_place(constants.OWM_CITY)
        w = observation.get_weather()

        humidity = w.get_humidity()              # 87
        temp = w.get_temperature(constants.OWM_UNITS)['temp']  # {'temp_max': 10.5, 'temp': 9.7, 'temp_min': 9.0}

        payload = {'temp': temp, 'humidity': humidity, 'hometemp': home_temp,
         'hometarget': home_target, 'homehumidity': home_humidity, 'nestmode': nest_mode}

        logging.info('Payload %s ', payload)
        
        if not DEBUG:
          r = requests.get(constants.SPREADSHEET, params=payload)
        
if __name__ == '__main__':
    main()
