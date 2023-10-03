import requests
import os
import json
import datetime

from gpiozero import RGBLED

def new_led(pins: str):
    pins = [int(x.strip()) for x in pins.split(",")]
    return RGBLED(red=pins[0], green=pins[1], blue=pins[2])

lln_lat = 50.66829
lln_long = 4.61443
interval_minutes = 15

config_server_url = "http://localhost:5000/config"

cache_file = ".weatherpi_cache.json"
cache_expiration_seconds = 3600

MOCK_LEDS = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]

LEDS = [
    new_led(os.getenv("RASPBERRY_RAIN_PINS_LED_0")),
    new_led(os.getenv("RASPBERRY_RAIN_PINS_LED_1")),
    new_led(os.getenv("RASPBERRY_RAIN_PINS_LED_2")),
    new_led(os.getenv("RASPBERRY_RAIN_PINS_LED_3")),
]


def get_dbz_intervals(long, lat, interval, api_key, ms_client_id):
    """ Returns a dbz measures for several intervals of `interval` minutes from now"""
    if interval not in [1, 5, 15, 30]:
        raise Exception("bad interval")
    request_interval = min(interval, 15)
    r = requests.get('https://atlas.microsoft.com/weather/forecast/minute/json',
                 params={
                     "api-version":"1.1",
                     "query": f"{lat},{long}",
                     "interval": str(request_interval),
                     "subscription-key": api_key
                 },
                 headers={
                     "x-ms-client-id": ms_client_id
                 })
    r.raise_for_status()
    forecast = r.json()
    intervals = [{"timestamp": forecast_interval["startTime"], "dbz": forecast_interval["dbz"]} for forecast_interval in forecast["intervals"]]
    if interval == 30:
        mean_intervals = []
        # mean of 15min intervals
        for i in range(0, len(intervals), 2):
            mean_intervals.append({"timestamp": interval[i]["timestamp"], "dbz": (intervals[i] + intervals[i+1])/2})
        intervals = mean_intervals
    return intervals

def get_config(url):
    r = requests.get(url)
    r.raise_for_status()
    config = r.json()
    return config

def get_and_refresh_dbz_measures(long, lat, interval, api_key, ms_client_id, cache_expiration_seconds):
    cache = None
    cache_age = None
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)
            cache_age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(cache[0]["timestamp"])).total_seconds()
    if cache is not None and cache_age < cache_expiration_seconds:
        return cache
    intervals = get_dbz_intervals(long, lat, interval, api_key, ms_client_id)
    with open(cache_file, "w") as f:
        json.dump(intervals, f)
    return intervals
        
def find_color(colors, dbz):
    """ We find the color to display for the measured `dbz` value. The `colors` dict
        indicates which color to display for threshold dbz values. The color to
        display is the one with the dbz threshold just above the measured
        `dbz`. """
    colors_with_float_keys = { float(k): v for k, v in colors.items() }
    for k in sorted(colors_with_float_keys.keys()):
        if dbz <= k:
            # we found the intensity category, so let's return the color
            return colors_with_float_keys[k]["rgb"]

def set_leds_colors_mock(leds_colors_rgb):
    leds_colors_rgb = leds_colors_rgb[:4]
    for i, color_rgb in enumerate(leds_colors_rgb):
        MOCK_LEDS[i] = color_rgb

def update_leds_mock(config_url):
    config = get_config(config_url)
    measures = get_and_refresh_dbz_measures(config["longitude"], config["latitude"], 
                                            config["forecast_interval_minutes"],
                                            os.getenv("RASPBERRY_RAIN_WEATHER_API_KEY"), os.getenv("RASPBERRY_RAIN_WEATHER_MS_ID"),
                                            cache_expiration_seconds)
    colors_rgb = [find_color(config["colors"], measure["dbz"]) for measure in measures]
    set_leds_colors_mock(colors_rgb)

def set_leds_colors(leds_colors_rgb):
    leds_colors_rgb = leds_colors_rgb[:4]
    for i, color_rgb in enumerate(leds_colors_rgb):
        LEDS[i].color = [color/255 for color in color_rgb]
        
def update_leds(config_url):
    config = get_config(config_url)
    measures = get_and_refresh_dbz_measures(config["longitude"], config["latitude"], 
                                            config["forecast_interval_minutes"],
                                            os.getenv("RASPBERRY_RAIN_WEATHER_API_KEY"), os.getenv("RASPBERRY_RAIN_WEATHER_MS_ID"),
                                            cache_expiration_seconds)
    colors_rgb = [find_color(config["colors"], measure["dbz"]) for measure in measures]
    set_leds_colors(colors_rgb)



if __name__ == "__main__":
    config = get_config(config_server_url)
    update_leds(config_server_url)
