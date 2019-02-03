# NestTweaks

Homemade tweaks through Google Assistant (as Nest API for Thermostat E is not available in EU)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. You can also deploy the examples on any compatible device (such as rpi) and program its execution using crontabs.

### Prerequisites

* [Python](http://www.dropwizard.io/1.0.2/docs/) (>= 3.4 recommended)
* An [Actions Console Project](https://maven.apache.org/)
* A [Google Account](https://rometools.github.io/rome/)

### Setup

Install Python 3 (Ubuntu/Debian GNU/Linux)

```
sudo apt-get update
sudo apt-get install python3 python3-venv
```

Or [MacOSX, Windows, Others](https://www.python.org/downloads/).

Create a new virtual environment:

```
python3 -m venv env
env/bin/python -m pip install --upgrade pip setuptools wheel
source env/bin/activate
```

Install the required dependencies:

```
sudo apt-get install portaudio19-dev libffi-dev libssl-dev
pip install --upgrade -r requirements.txt
```

## Authorization

* Follow the steps to configure the Actions Console project and the Google account.
* Follow the steps to [register a new device model and download the client secrets file](https://developers.google.com/assistant/sdk/guides/service/python/embed/register-device).
* Generate device credentials using google-oauthlib-tool:

```
pip install --upgrade google-auth-oauthlib[tool] google-oauthlib-tool --client-secrets path/to/client_secret_<client-id>.json --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save --headless
```

## Run the samples

You will find two different samples:

* Nest Thermostat History Data Logger (thermostat-monitor.py): get all the data from your Thermostat (temperature, humidity and working mode), the current outside weather and push the data to your Google SpreadSheet. 

```
python /path/to/thermostat-monitor.py --device-model-id <device-model-id> --device-id <device-id> --display
```

* Pre-warm your home after work (thermostat-eco.py): if you enable the ECO mode (either manually or automatically when you are away), it won't change to HEAT mode until you are back home (and probably, your home will be terribly cold). With this script, the mode will be changed to HEAT if the thermostat is currently in ECO mode.

```
python /path/to/thermostat-eco.py --device-model-id <device-model-id> --device-id <device-id> --display
```

In order to make thermostat-monitor work, don't forget to replace both the OWM (OpenWeatherMap) API Key to get the outside weather data and the GS_ID (GoogleSpreadsheet ID) if you want to push the data to your Google SpreadSheet as explained [here](https://www.instructables.com/id/Nest-Thermostat-Data-Logger/). You can find my own google script within gs folder.

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Google Assistant SDK for devices](https://github.com/googlesamples/assistant-sdk-python) - Used gRPC API
* [pyowm](https://github.com/csparpa/pyowm) - A Python wrapper around the OpenWeatherMap web API to get current weather
* [lxml](https://lxml.de/) - Used to parse Google Assistant HTML replies

## Contributing

Please, feel free to submit any pull request. I've created this project to meet my needs, due the lack of any Nest official API on Thermostat E (atleast, here in Europe) and I'm sure we can build something better!

## Authors

* **Roberto Bermejo** - *Initial work* - [Android in Spain](http://main.androidinspain.com/)

See also the list of [contributors](https://github.com/Batlin/NestTweaks/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details