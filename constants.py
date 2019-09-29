from enum import Enum
import apikeys

# Endpoints
SPREADSHEET = 'https://script.google.com/macros/s/' + apikeys.GS_ID + '/exec'
SPREADSHEET_DEV = 'https://script.google.com/macros/s/' + apikeys.GS_ID + '/dev'

# Open Weather
OWM_API_KEY = apikeys.OWM
OWM_CITY = 'Madrid, Spain'
OWM_UNITS = 'celsius'

# Google Assistant queries
QUERY_INTEMP = 'Whats the thermostat temperature'
QUERY_INHUMIDITY = 'Whats the thermostat humidity'
QUERY_MODE = 'Whats the thermostat mode'
SET_MODE_HEAT = 'Set thermostat to heat mode'

# Assistant SDK
ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

# Parsing response
DIV_CLASS = '//div[@class="show_text_content"]/text()'
HEAT = 'heat'
ECO = 'eco'
OFF = 'turned off'
ERROR = -1

# Modes
class NestMode(Enum):
	HEAT = 1
	ECO = 2
	OFF = 3
	UNKNOWN = 4
