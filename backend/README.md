# A LA QRTE BACKEND

This is a Python-based web server that takes in URLs of restaurant menus and uses ChatGPT to convert those menus into a simple, common format.

The high level process is:
1. Fetch website/PDF at given URL.
2. Screenshot the entire menu (or convert PDF to JPEGs).
3. Use OCR to extract all text from menu.
4. Send menu text to ChatGPT and ask it to format menu as CSV.

## WARNING
This code was written hastily, and I have no intention of maintaining it. Feel free to ask questions, but I reserve the right to say "IDK, Sorry!"

## Running The Server
I have *only* tested this on an M1 based Mac Mini, using Python 3.11! Mileage may vary.

1. Download this repo, ensure your terminal is parked in this directory (`/backend`).
2. Create a virtual environment: `python -m venv .`
3. Start it up: `source bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. [Install Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html)
6. Start the server: `uvicorn main:app --reload --host 0.0.0.0 --workers 4`
7. Hit the server with the url of a menu: `http://[your ip address]:8000/?menu_url=https://order.cloverfoodlab.com/order/locations/cloverhsq`
8. (Keep polling the same URL! The menu will populate as this server is updated from ChatGPT)