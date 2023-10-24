# You will need the following circuitpy libraries in your lib folder:
# adafruit_requests
# adafruit_thermal_printer
# neopixel
import board
import busio
import adafruit_thermal_printer
import time
import ssl
import wifi
import socketpool
import adafruit_requests
import os
import struct
import neopixel
import microcontroller

pixel = neopixel.NeoPixel(board.D0, 1, brightness=0.4, auto_write=True) 
# start LED as red to indicate nothing has happened yet
pixel.fill((0,150,0))

ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.168)
uart = busio.UART(board.TX, board.RX, baudrate=9600)
printer = ThermalPrinter(uart)
TINY_CODE_READER_I2C_ADDRESS = 0x0C

# How long to pause between sensor polls.
TINY_CODE_READER_DELAY = 0.2

# QR scanner code adapted from Tiny Code Reader circuitpy examples
# https://github.com/usefulsensors/tiny_code_reader_trinkey_keyboard/tree/main
TINY_CODE_READER_LENGTH_OFFSET = 0
TINY_CODE_READER_LENGTH_FORMAT = "H"
TINY_CODE_READER_MESSAGE_OFFSET = TINY_CODE_READER_LENGTH_OFFSET + struct.calcsize(TINY_CODE_READER_LENGTH_FORMAT)
TINY_CODE_READER_MESSAGE_SIZE = 254
TINY_CODE_READER_MESSAGE_FORMAT = "B" * TINY_CODE_READER_MESSAGE_SIZE
TINY_CODE_READER_I2C_FORMAT = TINY_CODE_READER_LENGTH_FORMAT + TINY_CODE_READER_MESSAGE_FORMAT
TINY_CODE_READER_I2C_BYTE_COUNT = struct.calcsize(TINY_CODE_READER_I2C_FORMAT)

last_code_time = 0.0

def flash(color):
    pixel.fill(color)
    for i in range(20):
        pixel.brightness = i / 20
        time.sleep(0.01)
    pixel.brightness = 0.4

i2c = board.I2C()
# Wait until we can access the bus.
while not i2c.try_lock():
    pass

pool = socketpool.SocketPool(wifi.radio)
# make sure each of these items are available in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
pwd = os.getenv("CIRCUITPY_WIFI_PASSWORD")
server_location = os.getenv("QR_SERVER_LOCATION")

print("\n===============================")
print("Connecting to WiFi...")
requests = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(ssid, pwd)
    except ConnectionError as e:
        print("Connection Error:", e)
        print("Retrying in 4 seconds")
        time.sleep(4)

print("Connected!\n")
print(f"{wifi.radio.ipv4_address}")
# change light to purple, indicating ready-to-scan
flash((0, 100, 150))

# cache vars for currently printing menu
active_menu = None
active_cat_index = 0
active_done = {}

def process_menu(menu):
    global active_cat_index
    process_again = False
    for key, value in menu.items():
        if key == "completed":
            continue
        # each item in the menu dict is a category - each has an index
        # use these to print in consistent order
        index = value["_index"]
        if index == active_cat_index + 1:
            print("new category", key)
            time.sleep(0.1)
            printer.justify = adafruit_thermal_printer.JUSTIFY_LEFT
            printer.size = adafruit_thermal_printer.SIZE_MEDIUM
            printer.feed(1)
            printer.print(key)
            active_cat_index += 1 
            # signal to outer loop that we should come back again after
            # printing this category to check for others.
            process_again = True
        if active_cat_index >= 1 and index == active_cat_index:
            for item, price in value.items():
                if item != "_index" and active_done.get(item) is None:
                    active_done[item] = True
                    printer.justify = adafruit_thermal_printer.JUSTIFY_LEFT
                    printer.size = adafruit_thermal_printer.SIZE_SMALL
                    printer.bold = True
                    printer.print(item)
                    print(item, price)
                    printer.bold = False
                    printer.justify = adafruit_thermal_printer.JUSTIFY_RIGHT
                    if not '$' in price:
                        price = f"${price}"
                    printer.print(price)
                    printer.feed(1)
    return process_again

def get_menu(url):
    global active_menu, active_cat_index, active_done
    wrapped_url = f"{server_location}/?menu_url={url}" 
    active_cat_index = 0
    active_menu = {}
    active_done = {}
    while True:
        # change LED to yellow, indicating a menu print is in progress
        flash((150, 100, 0))
        try:
            response = requests.get(wrapped_url)
        except Exception as e:
            print("failed to request, resetting")
            microcontroller.reset()
        j = response.json()
        response.close()
        menu = j.get("menu")
        if menu is None:
            pass
        else:
            repeat = process_menu(menu)
            while repeat:
                 # Keep flashing same color occasionally so we know it's not frozen
                flash((150, 100, 0))
                repeat = process_menu(menu)
            if menu.get("completed") is not None:
                # The backend will add a "completed" field when the menu has been 
                # fully processed
                printer.feed(2)
                print("last update!!")
                break
        time.sleep(2)
    # loop broken, menu print done. Back to purple.
    flash((0, 100, 150))

while True:
    read_data = bytearray(TINY_CODE_READER_I2C_BYTE_COUNT)
    i2c.readfrom_into(TINY_CODE_READER_I2C_ADDRESS, read_data)
    message_length,  = struct.unpack_from(TINY_CODE_READER_LENGTH_FORMAT, read_data, TINY_CODE_READER_LENGTH_OFFSET)
    message_bytes = struct.unpack_from(TINY_CODE_READER_MESSAGE_FORMAT, read_data, TINY_CODE_READER_MESSAGE_OFFSET)

    if message_length > 0:
        try:
            message_string = str(bytearray(message_bytes[:message_length]), 'ascii')
        except Exception as e:
            print("error: ", e)
            time.sleep(0.5)
            continue
        last_message_string = message_string
        current_time = time.monotonic()
        time_since_last_code = current_time - last_code_time
        last_code_time = current_time
        # Debounce the input by making sure there's been a gap in time since we
        # last saw this code.
        if (time_since_last_code > 1.0):
            print(f'got menu: {message_string}')
            get_menu(message_string)
        time.sleep(1)
    time.sleep(0.2)

