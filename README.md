# A LA QRTE
### A portable device for turning QR code menus into physical copies!

## WARNING
This code was written hastily, and I have no intention of maintaining it. Feel free to ask questions, but I reserve the right to say "IDK, Sorry!"

## Software Components
- [Backend](./backend/): The web app that takes a menu URL and converts it into a simple, common, printable format. Runs on a normal computer/server.
- [CircuitPython](./circuitpython/): The firmware that runs inside the device, on a Seeed Studio XIAO ESP-32 S3 microcontroller. This handles scanning QR Codes, passing the URL to the backend, and driving the thermal printer.