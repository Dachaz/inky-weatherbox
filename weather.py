#!/usr/bin/python3

import json
import requests
import datetime
from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne

# Gives baufort scale value for speed in kmh
def to_baufort(windspeed):
    scale = [1, 6, 12, 20, 29, 39, 50, 62, 75, 89, 103, 118]
    i = 0
    while i < len(scale) and windspeed > scale[i]:
        i += 1
    return i

def fetch_data(lattitude=52.37, longitude=4.89, temperature_unit="celsius", windspeed_unit="kmh"):
    # Minimum input cleaning
    temperature_unit = "fahrenheit" if temperature_unit == "F" else "celsius"

    # Not using match as default python in RaspberryOS is outdated
    if windspeed_unit == "mph":
        wind_scale = 1.61
    elif windspeed_unit == "ms":
        wind_scale = 3.6
    elif windspeed_unit == "kn":
        wind_scale = 1.852
    else:
        windspeed_unit = "kmh"
        wind_scale = 1

    url = "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&hourly=precipitation&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,windspeed_10m_max&current_weather=true&timezone=%s&temperature_unit=%s&windspeed_unit=%s" % (lattitude, longitude, 'auto', temperature_unit, windspeed_unit)
    response = requests.get(url)
    raw_data = json.loads(response.text)

    TEMPUNIT = raw_data['daily_units']['temperature_2m_max']
    WINDUNIT = raw_data['daily_units']['windspeed_10m_max']
    windspeed = raw_data['current_weather']["windspeed"]

    data = {
        'baufort': to_baufort(windspeed * wind_scale),
        'icon': raw_data['current_weather']['weathercode'],
        'precipitation': raw_data['hourly']['precipitation'],
        'range': str(round(raw_data['daily']['temperature_2m_min'][0])) + "—" + str(round(raw_data['daily']['temperature_2m_max'][0])) + TEMPUNIT,
        'sunrise': raw_data['daily']['sunrise'][0],
        'sunset': raw_data['daily']['sunset'][0],
        'temp': str(round(raw_data['current_weather']["temperature"])) + TEMPUNIT,
        'wind': str(round(windspeed)) + WINDUNIT,
        'wind_direction': raw_data['current_weather']["wind_direction"],

        'TEMPUNIT': TEMPUNIT,
        'WINDUNIT': WINDUNIT,
    }

    return data

def draw_image(display, data):
    img = Image.new("P", (display.WIDTH, display.HEIGHT))
    draw = ImageDraw.Draw(img)

    # fonts
    fonts = {
        'S': ImageFont.truetype(FredokaOne, int(0.11 * display.HEIGHT)),
        'M': ImageFont.truetype(FredokaOne, int(0.13 * display.HEIGHT)),
        'L': ImageFont.truetype(FredokaOne, int(0.27 * display.HEIGHT))
    }

    # clear the display
    draw.rectangle((0, 0, display.WIDTH, display.HEIGHT), display.BLACK)

    # Draw precipitation as a background polygon
    hour = datetime.datetime.now().hour
    line_width = int(display.WIDTH/6)
    line = []

    for i in range(0, 7):
        prec = data['precipitation'][hour+i]
        line.append(i * line_width)
        line.append(display.HEIGHT - (prec / 5 * display.HEIGHT))

    line.extend([display.WIDTH, display.HEIGHT, 0, display.HEIGHT])

    draw.polygon(line, display.RED)

    # Draw the temperature
    sx = 0.05 * display.WIDTH
    sy = 0.25 * display.HEIGHT
    draw.text((sx,   sy),    data['temp'],  display.WHITE, fonts['L'])
    draw.text((sx+1, sy+36), data['range'], display.BLACK, fonts['S']) # shadow
    draw.text((sx,   sy+35), data['range'], display.RED,   fonts['S'])

    # Draw the wind
    sx = 0.45 * display.WIDTH
    sy = 0.34 * display.HEIGHT
    # draw.arc starts at 3 o'clock, while wind direction starts at 12 o'clock — hence, shifting by 90º
    draw.arc((sx-4, sy-4, sx+24, sy+24), data['wind_direction']-60+90, data['wind_direction']+90, fill=display.WHITE, width=3)

    if (data['baufort'] < 10):
        draw.text((sx+5, sy),   str(data['baufort']), display.WHITE, fonts['M'])
    else:
        draw.text((sx+3, sy+2), str(data['baufort']), display.WHITE, fonts['S'])

    draw.text((sx-9,  sy+26), data['wind'], display.BLACK, fonts['S']) # shadow
    draw.text((sx-10, sy+25), data['wind'], display.RED,   fonts['S'])

    # Icons aligned with WMO Weather interpretation codes (https://open-meteo.com/en/docs#weathervariables)

    # clear and partly cloudy
    icon = data['icon']
    if icon < 3:
        # big moon
        if datetime.datetime.now() > datetime.datetime.fromisoformat(data['sunset']) or datetime.datetime.now() < datetime.datetime.fromisoformat(data['sunrise']):
            sx = 0.70 * display.WIDTH
            sy = 0.24 * display.HEIGHT
            # moon
            draw.ellipse((sx,    sy,    sx+50, sy+50), display.WHITE)
            draw.ellipse((sx+10, sy-10, sx+60, sy+40), display.BLACK)

            # clear skies = stars
            if icon == 0:
                draw.line((sx+20, sy,   sx+30, sy), display.WHITE, 2)
                draw.line((sx+25, sy-5, sx+25, sy+5), display.WHITE, 2)
        # big sun
        else:
            sx = 0.73 * display.WIDTH
            sy = 0.33 * display.HEIGHT
            # rays
            draw.polygon((sx+12, sy-16, sx+17, sy,    sx+7, sy,    sx+12, sy-16), display.WHITE, 4) # top
            draw.polygon((sx+12, sy+40, sx+17, sy+30, sx+7, sy+30, sx+12, sy+40), display.WHITE, 4) # down
            draw.polygon((sx-17, sy+12, sx,    sy+7,  sx,   sy+17, sx-16, sy+12), display.WHITE, 4) # left
            draw.polygon((sx+40, sy+12, sx+24, sy+7, sx+24, sy+17, sx+40, sy+12), display.WHITE, 4) # right

            draw.line((sx-5, sy-5,  sx+29, sy+29), display.WHITE, 4)
            draw.line((sx-5, sy+29, sx+29, sy-5), display.WHITE, 4)

            # sun
            draw.ellipse((sx-5, sy-5, sx+29, sy+29), display.BLACK)
            draw.ellipse((sx,   sy,   sx+24, sy+24), display.WHITE)

        # secondary "heavy" cloud
        if (icon == 2):
            sx = 0.85 * display.WIDTH
            sy = 0.34 * display.HEIGHT

            # black
            draw.ellipse((sx-5, sy-5, sx+20, sy+20), display.BLACK)
            draw.ellipse((sx+5, sy,   sx+30, sy+20), display.BLACK)

            # white
            draw.ellipse((sx,    sy,   sx+15, sy+15), display.WHITE)
            draw.ellipse((sx+10, sy+5, sx+25, sy+15), display.WHITE)

        # small cloud
        if (icon == 1) or (icon == 2):
            sx = 0.80 * display.WIDTH
            sy = 0.34 * display.HEIGHT

            # outline
            draw.ellipse((sx-3,  sy-3,  sx+8,  sy+8), display.BLACK)
            draw.ellipse((sx+2,  sy-8,  sx+18, sy+8), display.BLACK)
            draw.ellipse((sx+7,  sy-13, sx+28, sy+8), display.BLACK)
            draw.ellipse((sx+17, sy-8,  sx+33, sy+8), display.BLACK)

            # white
            draw.ellipse((sx,    sy,    sx+5,  sy+5), display.WHITE)
            draw.ellipse((sx+5,  sy-5,  sx+15, sy+5), display.WHITE)
            draw.ellipse((sx+10, sy-10, sx+25, sy+5), display.WHITE)
            draw.ellipse((sx+20, sy-5,  sx+30, sy+5), display.WHITE)

    # If icon has a big cloud
    else:
        sx = 0.70 * display.WIDTH
        sy = 0.45 * display.HEIGHT

        # dark
        draw.ellipse((sx-5,  sy-5,  sx+15, sy+15), display.BLACK)
        draw.ellipse((sx,    sy-15, sx+30, sy+15), display.BLACK)
        draw.ellipse((sx+10, sy-25, sx+50, sy+15), display.BLACK)
        draw.ellipse((sx+30, sy-15, sx+60, sy+15), display.BLACK)

        # white
        draw.ellipse((sx,    sy,    sx+10, sy+10), display.WHITE)
        draw.ellipse((sx+5,  sy-10, sx+25, sy+10), display.WHITE)
        draw.ellipse((sx+15, sy-20, sx+45, sy+10), display.WHITE)
        draw.ellipse((sx+35, sy-10, sx+55, sy+10), display.WHITE)

        # foggy
        if icon in [45, 48]:
            sx = 0.74 * display.WIDTH
            sy = 0.60 * display.HEIGHT

            draw.line((sx,    sy,   sx+40, sy),   display.WHITE, 3)
            draw.line((sx+4,  sy+4, sx+12, sy+4), display.WHITE, 3)
            draw.line((sx+17, sy+4, sx+45, sy+4), display.WHITE, 3)
            draw.line((sx,    sy+8, sx+40, sy+8), display.WHITE, 3)

        # snow
        if icon in [71, 73, 75, 77, 85, 86]:
            sx = 0.76 * display.WIDTH
            sy = 0.60 * display.HEIGHT

            symbol = "*" if icon != 77 else "·"

            draw.text((sx,    sy),   symbol, display.WHITE, fonts['S'])
            draw.text((sx+18, sy+3), symbol, display.WHITE, fonts['S'])
            draw.text((sx+7,  sy+6), symbol, display.WHITE, fonts['M'])

        # heavy rain drop
        if icon in [55, 57, 65, 67, 81, 82, 95, 96, 99]:
            sx = 0.83 * display.WIDTH
            sy = 0.67 * display.HEIGHT
            draw.ellipse((sx, sy, sx+5, sy+5), display.WHITE)
            draw.polygon((sx-5, sy-5, sx, sy+3, sx+5, sy+1, sx-5, sy-5), display.WHITE)

        # left rain drop
        if icon in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]:
            sx = 0.76 * display.WIDTH
            sy = 0.67 * display.HEIGHT
            draw.ellipse((sx+3, sy-3, sx+7, sy), display.WHITE)
            draw.polygon((sx, sy-6, sx+5, sy-1, sx+6, sy-4, sx+2, sy-6), display.WHITE)

        # right rain drop
        if icon in [53, 55, 63, 65, 81, 82, 95, 96, 99]:
            sx = 0.86 * display.WIDTH
            sy = 0.67 * display.HEIGHT
            draw.ellipse((sx+3, sy-4, sx+7, sy-1), display.WHITE)
            draw.polygon((sx, sy-6, sx+5, sy-1, sx+6, sy-4, sx+2, sy-6), display.WHITE)

        # right lightning bolt
        if icon in [95, 96, 99]:
            sx = 0.85 * display.WIDTH
            sy = 0.55 * display.HEIGHT
            draw.polygon(((sx+2, sy+6), (sx+10, sy+6), (sx+14, sy+12), (sx+8, sy+12),
                         (sx+10, sy+18), (sx+2, sy+10), (sx+7, sy+10), (sx+2, sy+6)), display.WHITE)

        # freezing drizzle/rain
        if icon in [56, 57, 66, 67]:
            sx = 0.87 * display.WIDTH
            sy = 0.58 * display.HEIGHT
            draw.text((sx, sy), "*", display.WHITE, fonts['S'])

    return img

def get_display(mock):
    if mock:
        from MockDisplay import MockDisplay
        display = MockDisplay(mock)
    else:
        from inky.auto import auto
        display = auto()
        display.set_border(display.BLACK)

    return display

def main(lattitude, longitude, temperature_unit, windspeed_unit, mock=False):
    data = fetch_data(lattitude, longitude, temperature_unit, windspeed_unit)
    display = get_display(mock)
    img = draw_image(display, data)
    display.set_image(img)
    display.show()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Gets and draws weather conditions on your InkyPHAT'
    )

    parser.add_argument('-lat', '--lattitude',
                        action='store',
                        dest='lattitude',
                        default=52.37,
                        help='Get weather for this lattitude (default: 52.37)')

    parser.add_argument('-lon', '--longitude',
                        action='store',
                        dest='longitude',
                        default=4.89,
                        help='Get weather for this lattitude (default: 4.89)')

    parser.add_argument('-t', '--temp',
                        action='store',
                        dest='temperature_unit',
                        default='celsius',
                        help='Temperature unit. "C" (default) or "F"')

    parser.add_argument('-w', '--wind',
                        action='store',
                        dest='windspeed_unit',
                        default='kmh',
                        help='Windspeed unit. One of: "kmh" (default), "mph", "ms" or "kn" ')

    parser.add_argument('-m', '--mock',
                        action='store',
                        default=False,
                        dest='mock',
                        help='''Create inky.png instead of updating the display.
                                Accepted values are "v1" (212x104 model) or "v2" (250x122 model)''')

    args = parser.parse_args()
    main(**vars(args))
