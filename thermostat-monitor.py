import os
import logging
import json

import re
import pyowm
import requests

import click
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials

import constants
import utils
from constants import NestMode

DEBUG = False

def get_inconditions(assistant, mode):
  humidity, temp, target = ('',)*3
  get_humidity = re.findall(r'[\d.]+[\d]+', utils.query_assistant(assistant,constants.QUERY_INHUMIDITY))
  get_temp = re.findall(r'[\d.]+[\d]+', utils.query_assistant(assistant, constants.QUERY_INTEMP))

  if((len(get_temp) > 0) & (len(get_humidity) > 0)):
    #The Termostato has a current humidity reading of 28%.
    humidity = get_humidity[0]
    if (mode == NestMode.HEAT):
      temp = get_temp[0]
      if(len(get_temp) > 1):
        #Heating is set to 25, with a current temperature of 24. 
        target = get_temp[0]
        temp = get_temp[1]
    elif (mode == NestMode.ECO):
      #It's currently 24.5 degrees, and eco mode is set to keep the temperature above 16.5 degrees.
      temp = get_temp[0]
      if(len(get_temp) > 1):
        target = get_temp[1]
    else:
      #It\'s currently 25 degrees.
      #It's currently 24.5 degrees, and the Termostato is off.
      temp = get_temp[0]

  return (humidity, temp, target)

def get_current_weather():
  owm = pyowm.OWM(constants.OWM_API_KEY)
  observation = owm.weather_at_place(constants.OWM_CITY)
  w = observation.get_weather()
 
  #87
  humidity = w.get_humidity()
  # {'temp_max': 10.5, 'temp': 9.7, 'temp_min': 9.0}
  temp = w.get_temperature(constants.OWM_UNITS)['temp']  

  return (humidity, temp)

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

    with utils.TextAssistant(lang, device_model_id, device_id, display,
                             grpc_channel, grpc_deadline) as assistant:
        nest_mode = utils.get_mode(assistant)

        # Variables
        temp, humidity, home_temp, home_humidity, home_target = ('',)*5

        home_humidity, home_temp, home_target = get_inconditions(assistant, nest_mode)
        humidity, temp = get_current_weather()

        payload = {'temp': temp, 'humidity': humidity, 'hometemp': home_temp,
         'hometarget': home_target, 'homehumidity': home_humidity, 'nestmode': nest_mode}

        logging.info('Payload %s ', payload)
        
        if not DEBUG:
          r = requests.get(constants.SPREADSHEET, params=payload)
        
if __name__ == '__main__':
    main()
