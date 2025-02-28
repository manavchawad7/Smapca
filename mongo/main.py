from app import app
from threading import Timer
import webbrowser

def open_browser():
    """Open the default web browser to the /detect endpoint."""
    webbrowser.open_new("http://127.0.0.1:5000/detect")

if __name__ == "__main__":
    # Schedule the browser to open after 1 second
    Timer(1, open_browser).start()
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)