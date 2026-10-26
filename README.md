# API_Listropik 

A lightweight Python backend server designed to handle YouTube audio extraction and serve files locally to the **Listropik** Android app over Wi-Fi.

---

##  Features

* **Audio Extraction:** Processes YouTube links to extract and convert audio streams.
* **Local Network Server:** Serves downloaded audio files directly to the Listropik mobile application over local Wi-Fi.
* **Simple Setup:** Minimal configuration required to get up and running.

---

##  Requirements

* Python 3.10 or higher
* FFmpeg installed on your system (required for audio processing)

---

##  Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/4x3l-MT/API_Listropik.git](https://github.com/4x3l-MT/API_Listropik.git)
   cd API_Listropik

2. **Create and activate a virtual environment (recommended):
   python -m venv venv
   # On Linux/macOS:
    source venv/bin/activate
   # On Windows:
    venv\Scripts\activate

3. **Install dependencies:
   pip install -r requirements.txt

4. **Start the server:
   python main.py

5. **Connect to Mobile App:
  Find your computer's local IP address (e.g., 192.168.1.X) and input it into the Listropik Android app settings.

## Related Repository

Mobile Aplication: [Listropik]([https://github.com/4x3l-MT/Listropik?tab=MIT-1-ov-file](https://github.com/4x3l-MT/Listropik.git))
