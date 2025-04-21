import picobot_api

picobot_api.init()

i = 0
while True:
    picobot_api.setLedColor(0, 0, 0, i % 255)
    msg(i)
    if i > 1000:
        i / 0
    i += 1
