#!/usr/bin/env python3
# ShCa ultra-simplified — file sharing + QR code
# Fully documented and visually expanded version
# Functionality unchanged from previous version

import os, time, secrets, shutil, threading, argparse
from flask import Flask, request, send_file, render_template_string, redirect, url_for
import qrcode
import pyperclip  # For clipboard auto-copy

# Bsae Directoy

BASE_DIR = os.path.abspath(".")  # Root directory of the tool
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")  # Folder where uploaded files are saved
SHARES_DIR = os.path.join(BASE_DIR, "shares")   # Folder where shared files and metadata are stored

os.makedirs(UPLOADS_DIR, exist_ok=True)  # Ensure upload directory exists
os.makedirs(SHARES_DIR, exist_ok=True)   # Ensure shares directory exists

# Flask App Setup

app = Flask(__name__)  # Initialize Flask app

# functions


def generate_token(n=8):
    """
    Generate a random alphanumeric token used for share URLs.
    
    Parameters:
    - n (int): Length of the token (default 8)
    
    Returns:
    - str: Random token composed of uppercase letters and digits
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(alphabet) for _ in range(n))  # Build token character by character


def share_dir(token):
    """
    Return the directory path for a given share token.

    Parameters:
    - token (str): Share token

    Returns:
    - str: Path to the share folder inside SHARES_DIR
    """
    return os.path.join(SHARES_DIR, token)


def display_ascii_banner():
    """
    Display a large ASCII banner for ShCA in the terminal.
    """
    banner = r"""
    # ASCII
   _____ _    ____ ____  
  / ____| |  / ___/ ___| 
 | (___ | | | |  | |     
  \___ \| | | |  | |     
  ____) | | | |__| |___  
 |_____/|_|  \____\____| 
                          
        ShCA - Local File Share
    """
    print(banner)


# HTML two pages

DOWNLOAD_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Download</title>
</head>
<body style="text-align:center;font-size:22px;">
<h1>Download File</h1>
<p><b>Filename:</b> {{filename}}</p>
<a href="/download/{{token}}">
    <button style="font-size:22px;padding:15px 25px;">Download</button>
</a>
</body>
</html>
"""

UPLOAD_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Upload File</title>
</head>
<body style="text-align:center;font-size:22px;">
<h1>Upload File to Laptop</h1>
{% if msg %}
<p>{{msg}}</p>
{% endif %}
<form action="/upload" method="post" enctype="multipart/form-data">
  <input type="file" name="file" multiple required style="font-size:20px;">
  <br><br>
  <button type="submit" style="font-size:22px;padding:15px 25px;">Upload Files</button>
</form>
</body>
</html>
"""


# Routs for pages

@app.route("/")
def index():
    """
    Home page route.
    Displays a centered, large-font welcome message and link to upload page.
    """
    return """
    <!doctype html>
    <html>
    <head><meta charset="utf-8"><title>ShCA</title></head>
    <body style="text-align:center;font-size:22px;">
        <h1>✅ Simple Local Share Server Running</h1>
        <p>Use your phone to upload files to this laptop.</p>
        <a href="/upload">
            <button style="font-size:22px;padding:15px 25px;">Upload Files</button>
        </a>
    </body>
    </html>
    """


@app.route("/share/<token>")
def share_page(token):
    """
    Share page route.
    Displays the download page for a given token.

    Parameters:
    - token (str): The share token

    Returns:
    - HTML page with filename and download button
    - 404 if the token is invalid or expired
    """
    path = os.path.join(share_dir(token), "file")
    if not os.path.exists(path):
        return "Invalid or expired link", 404
    filename = os.path.basename(path)
    return render_template_string(DOWNLOAD_HTML, token=token, filename=filename)


@app.route("/download/<token>")
def download(token):
    """
    Download route.
    Sends the shared file as an attachment.

    Parameters:
    - token (str): The share token

    Returns:
    - File download or 404 if invalid
    """
    path = os.path.join(share_dir(token), "file")
    if not os.path.exists(path):
        return "Invalid or expired link", 404
    return send_file(path, as_attachment=True)


@app.route("/upload", methods=["GET"])
def upload_page():
    """
    Upload page route (GET).
    Displays the upload form and optional success message.

    Query Parameters:
    - msg (str, optional): Message to display after upload
    """
    msg = request.args.get("msg")
    return render_template_string(UPLOAD_HTML, msg=msg)


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Handle file uploads (POST).
    Saves all selected files to UPLOADS_DIR and redirects to upload page with message.

    Returns:
    - Redirect to /upload with success message
    """
    if 'file' not in request.files:
        return "No file", 400

    files = request.files.getlist('file')
    uploaded_files = []

    for f in files:
        # Save each file to the upload directory
        filename = f.filename
        path = os.path.join(UPLOADS_DIR, filename)
        f.save(path)
        uploaded_files.append(filename)
        # End of single file save loop

    msg = f"✅ Uploaded successfully: {', '.join(uploaded_files)}"
    return redirect(url_for('upload_page', msg=msg))


# Share function

def create_share(file_path, host, port, ttl):
    """
    Create a share for a given file.

    Parameters:
    - file_path (str): Absolute or relative path to the file
    - host (str): Host IP for the Flask server
    - port (int): Port for the Flask server
    - ttl (int): Time-to-live in minutes
    """
    if not os.path.exists(file_path):
        print("File not found")
        return

    token = generate_token()
    d = share_dir(token)
    os.makedirs(d, exist_ok=True)

    dest = os.path.join(d, "file")
    shutil.copy(file_path, dest)

    expiry = time.time() + ttl * 60
    with open(os.path.join(d, "expiry.txt"), "w") as f:
        f.write(str(expiry))

    # Define the share URL
    url = f"http://{host}:{port}/share/{token}"

    # Generate QR code image
    qr_path = os.path.join(d, "qr.png")
    qrcode.make(url).save(qr_path)

    # Display ASCII QR in terminal
    print("\n Share created!")
    print("Link:", url)
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make()
    qr.print_ascii(invert=True)

    # Copy link to clipboard
    try:
        pyperclip.copy(url)
        print(" Share link copied to clipboard!")
    except:
        print(" Could not copy to clipboard. Install pyperclip.")

    print(f"\nQR Image saved at: {qr_path}\n")


# Cleaup

def cleanup():
    """
    Background thread to remove expired shares.
    Runs every 30 seconds.
    """
    while True:
        now = time.time()
        for token in os.listdir(SHARES_DIR):
            d = share_dir(token)
            exp_file = os.path.join(d, "expiry.txt")
            try:
                if os.path.exists(exp_file):
                    exp = float(open(exp_file).read())
                    if now > exp:
                        shutil.rmtree(d, ignore_errors=True)
            except:
                pass
        time.sleep(30)


# Main

def main():
    """
    Main entry point for the ShCA tool.
    Handles CLI arguments, starts Flask server, and manages shares.
    """
    display_ascii_banner()

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    # Share command
    share = sub.add_parser("share")
    share.add_argument("--file", required=True, help="Path to file anywhere")
    share.add_argument("--host", default="127.0.0.1")
    share.add_argument("--port", type=int, default=8080)
    share.add_argument("--ttl", type=int, default=30)

    # Serve command
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8080)

    args = parser.parse_args()

    if args.cmd == "share":
        threading.Thread(target=cleanup, daemon=True).start()
        threading.Thread(
            target=lambda: app.run(host=args.host, port=args.port),
            daemon=True
        ).start()

        time.sleep(1)
        create_share(args.file, args.host, args.port, args.ttl)

        print("\n🚀 Server running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)

    elif args.cmd == "serve":
        threading.Thread(target=cleanup, daemon=True).start()
        app.run(host=args.host, port=args.port)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()