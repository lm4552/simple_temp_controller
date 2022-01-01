import machine
import onewire
import ds18x20
import time


charmap = {
    '0': 0b00111111,
    '1': 0b00000110,
    '2': 0b01011011,
    '3': 0b01001111,
    '4': 0b01100110,
    '5': 0b01101101,
    '6': 0b01111101,
    '7': 0b00000111,
    '8': 0b01111111,
    '9': 0b01100111,
    '-': 0b01000000,
    ' ': 0b00000000
}

mapping = {
    'a': 0b00000001,
    'b': 0b00000010,
    'c': 0b00000100,
    'd': 0b00001000,
    'e': 0b00010000,
    'f': 0b00100000,
    'g': 0b01000000
}

pins_A = {'a': 12, 'b': 13, 'c': 19, 'd': 20, 'e': 21, 'f': 11, 'g': 10, 'h': 18}
pins_B = {'a': 7, 'b': 8, 'c': 27, 'd': 28,
          'e': 22, 'f': 6, 'g': 9, 'h': 26}

pinout = {
    'temperature_sensor' : 17,
    'blue_led' : 14,
    'red_led' : 15,
    'yellow_led' : 16,
    'cooler_output' : 3,
    'fan_output' : 5,
    'plus_switch' : 0,
    'minus_switch' : 1
}

display_B, display_A = {}, {}
cooling_state, fan_state = False, False
roms = []
threshold_temp = 28
seconds_to_retrigger = 60*10
last_retrigger = time.time()
trigger_twice = False


def main():
    init_displays()
    init_temp_sensor()
    init_leds()
    init_control()
    init_switches()

    while True:
        time.sleep_ms(1000)
        loop()


def loop():
    temp = read_temp_sensor()

    if temp != None:
        handle_temp_control(temp)

    handle_threshold_change()
    handle_retrigger_control()


def read_temp_sensor():
    global roms, ds_sensor
    temp = None
    try:
        ds_sensor.convert_temp()
        # print(roms)
    except:
        print('error')
        roms = []
    if roms != []:
        for rom in roms:
            try:
                temp = ds_sensor.read_temp(rom)
                render_temp(temp)
            except:
                print('error')
                roms = []
    else:
        print(ds_sensor)
        try:
            roms = ds_sensor.scan()
            print('Found a ds18x20 device')
        except:
            print('ds_sensor is None')
    return temp


def handle_temp_control(temp):
    global threshold_temp, cooling_state, fan_state, cooling, fan, led_blue, led_red, led_yellow
    if temp > threshold_temp:
        if cooling_state == False and fan_state == False:
            cooling.on()
            fan.on()
            time.sleep_ms(500)
            if trigger_twice:
                cooling.off()
                fan.off()
            cooling_state = True
            fan_state = True

        led_blue.off()
        led_red.on()
        led_yellow.on()
    elif temp < threshold_temp:
        if cooling_state == True and fan_state == True:
            if trigger_twice:
                cooling.on()
                fan.on()
            time.sleep_ms(500)
            cooling.off()
            fan.off()
            cooling_state = False
            fan_state = False

        # cooling.off()
        # fan.off()
        led_blue.on()
        led_red.off()
        led_yellow.off()
    else:
        if cooling_state == False and fan_state == False:
            cooling.on()
            fan.on()
            time.sleep_ms(500)
            if trigger_twice:
                cooling.off()
                fan.off()
            cooling_state = True
            fan_state = True
        led_blue.off()
        led_red.off()
        led_yellow.on()


def handle_retrigger_control():
    global last_retrigger, seconds_to_retrigger, led_blue, led_red, led_yellow, cooling_state, fan_state, cooling, fan
    print(time.time())
    if (time.time() > last_retrigger + seconds_to_retrigger):
        if trigger_twice:
            # just activate the switches two times (state restored)
            led_blue.off()
            led_red.off()
            led_yellow.off()
            cooling.on()
            fan.on()
            time.sleep_ms(250)
            cooling.off()
            fan.off()
            time.sleep_ms(250)
            cooling.on()
            fan.on()
            time.sleep_ms(250)
            cooling.off()
            fan.off()
            led_blue.on()
            led_red.on()
            led_yellow.on()
            time.sleep_ms(250)
        else:
            # activate output according to current state
            led_blue.off()
            led_red.off()
            led_yellow.off()
            if cooling_state == True and fan_state == True:
                cooling.off()
                fan.off()
            else:
                cooling.on()
                fan.on()
            time.sleep_ms(250)
            if cooling_state == True and fan_state == True:
                cooling.on()
                fan.on()
            else:
                cooling.off()
                fan.off()
            time.sleep_ms(250)

            led_blue.on()
            led_red.on()
            led_yellow.on()
            time.sleep_ms(250)


        print('retriggered outputs')
        last_retrigger = time.time()


def handle_threshold_change():
    global threshold_temp, switch_plus, switch_minus

    if not switch_plus.value():
        threshold_temp = threshold_temp + 1
        clear_temp()
        time.sleep_ms(100)
        render_temp(threshold_temp)
        time.sleep_ms(1000)
        clear_temp()
        time.sleep_ms(100)
    if not switch_minus.value():
        threshold_temp = threshold_temp - 1
        clear_temp()
        time.sleep_ms(100)
        render_temp(threshold_temp)
        time.sleep_ms(1000)
        clear_temp()
        time.sleep_ms(100)


def init_displays():
    global display_A, display_B, pins_A, pins_B
    for pin in pins_A:
        out = machine.Pin(pins_A[pin], machine.Pin.OUT)
        display_A[pin] = out

    for pin in pins_B:
        out = machine.Pin(pins_B[pin], machine.Pin.OUT)
        display_B[pin] = out


def init_temp_sensor():
    global ds_sensor, pinout
    ds_pin = machine.Pin(pinout['temperature_sensor'])
    ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))


def init_leds():
    global led_blue, led_yellow, led_red,pinout
    led_blue = machine.Pin(pinout['blue_led'], machine.Pin.OUT)
    led_yellow = machine.Pin(pinout['yellow_led'], machine.Pin.OUT)
    led_red = machine.Pin(pinout['red_led'], machine.Pin.OUT)


def init_control():
    global cooling, fan, pinout 
    cooling = machine.Pin(pinout['cooler_output'], machine.Pin.OUT)
    fan = machine.Pin(pinout['fan_output'], machine.Pin.OUT)


def init_switches():
    global switch_plus, switch_minus
    switch_plus = machine.Pin(pinout['plus_switch'], machine.Pin.IN, machine.Pin.PULL_UP)
    switch_minus = machine.Pin(pinout['minus_switch'], machine.Pin.IN, machine.Pin.PULL_UP)


def renderChar(c, disp, dp=False):
    global charmap, mapping
    val = charmap[c]

    for pin in disp:
        disp[pin].on()
    disp['h'].on()

    for key in mapping:
        v = mapping[key]
        if val & v == v:
            disp[key].off()
    if dp:
        disp['h'].off()


def render_temp(t):
    global display_A, display_B
    print(t)
    # print(str(int(t/10)%10))
    # print(str(int(t)%10))
    if t >= 10:
        renderChar(str(int(t) % 10)[0], display_A, True)
        renderChar(str(int(t/10) % 10)[0], display_B)
    elif t <= -10:
        renderChar(str(int(t*(-1)/10) % 10)[0], display_A)
        renderChar('-', display_B)
    elif t < 0:
        renderChar(str(int(t*(-1)) % 10)[0], display_A, True)
        renderChar('-', display_B)
    else:
        renderChar(str(int(t*10) % 10)[0], display_A)
        renderChar(str(int(t) % 10)[0], display_B, True)


def clear_temp():
    global display_A, display_B
    renderChar(' ', display_A)
    renderChar(' ', display_B)


if __name__ == "__main__":
    main()
