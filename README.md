# ShareCare

ShCA is a **lightweight local file sharing tool** that lets you easily share files between your devices over your local network. It features **QR code generation**, a **mobile-friendly upload page**, and temporary shares that automatically clean up.

---

## Features

-  Serve a simple local web server for uploading and downloading files.
-  Upload files from your phone to your laptop via a browser.
-  Create temporary file shares with QR codes.
-  QR codes displayed **in terminal** and saved as PNG.
-  Automatically copy share link to clipboard.
-  Multiple file upload support.
-  Temporary shares automatically cleaned up after expiry.


---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Mohameddashraaff/ShareCare.git
```

```
cd ShareCare
```

Linux:
```
python3 -m venv venv
source venv/bin/activate
```

Windows:
```
venv\Scripts\activate
```

```
pip install -r requirements.txt
```

## Usage
- Start the server for uploads
```
python3 ShCa.py serve --host 0.0.0.0 --port 8080
```

- Share a file through url or qr code
```
python3 ShCa.py share --file /path/to/file.pdf --host (your ip) --port 8080 --ttl 30
```

## Folder Structure
ShCA/
│
├── ShCa.py            # Main tool script
├── uploads/           # Uploaded files from phone or browser
├── shares/            # Temporary shares with QR codes and expiry
├── requirements.txt   # Python dependencies
└── README.md          # This file

# Note:
- Clipboard auto-copy works with pyperclip – may require xclip or xsel on Linux.
- YOu must put the file you want to share from your laptop in the same direcroty of tool
