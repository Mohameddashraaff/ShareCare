#!/usr/bin/env python3
# ShCa ultra-simplified — file sharing + QR code
# Fully documented and visually expanded version
# Functionality unchanged from previous version

import os, time, secrets, shutil, threading, argparse
from flask import Flask, request, send_file, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import qrcode

try:
    import pyperclip  # Optional clipboard auto-copy
except Exception:
    pyperclip = None

# Base Directory

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
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Download — Local Share</title>
  <style>
    :root {
      --bg1: #0f172a;
      --bg2: #111827;
      --card: rgba(17, 24, 39, 0.82);
      --card-border: rgba(255,255,255,0.10);
      --text: #e5e7eb;
      --muted: #9ca3af;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --shadow: 0 18px 60px rgba(0,0,0,0.35);
      --radius: 20px;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(79,70,229,0.20), transparent 28%),
        radial-gradient(circle at bottom right, rgba(14,165,233,0.16), transparent 26%),
        linear-gradient(160deg, var(--bg1), var(--bg2));
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .shell {
      width: min(100%, 560px);
    }

    .card {
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(10px);
    }

    .header {
      padding: 22px 22px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(79,70,229,0.16);
      color: #c7d2fe;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.2px;
    }

    h1 {
      margin: 14px 0 8px;
      font-size: clamp(24px, 4vw, 34px);
      line-height: 1.1;
    }

    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.6;
    }

    .content {
      padding: 22px;
    }

    .filebox {
      border: 1px solid rgba(255,255,255,0.10);
      background: rgba(255,255,255,0.03);
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 18px;
    }

    .label {
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      margin-bottom: 8px;
    }

    .filename {
      font-size: 18px;
      font-weight: 700;
      word-break: break-word;
    }

    .meta {
      margin-top: 8px;
      font-size: 13px;
      color: var(--muted);
    }

    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .btn {
      appearance: none;
      border: 0;
      border-radius: 14px;
      padding: 14px 18px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      text-align: center;
      transition: transform 0.12s ease, background 0.2s ease, box-shadow 0.2s ease;
      min-width: 180px;
      flex: 1 1 180px;
    }

    .btn:active { transform: translateY(1px); }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent), #7c3aed);
      color: white;
      box-shadow: 0 12px 30px rgba(79,70,229,0.30);
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, var(--accent-hover), #6d28d9);
    }

    .footer {
      padding: 0 22px 22px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    @media (max-width: 480px) {
      body { padding: 14px; }
      .content, .header, .footer { padding-left: 16px; padding-right: 16px; }
      .btn { min-width: 100%; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card">
      <div class="header">
        <span class="badge">Local Share</span>
        <h1>Ready to download</h1>
        <p class="subtitle">Open the file below and save it to your device.</p>
      </div>

      <div class="content">
        <div class="filebox">
          <span class="label">Filename</span>
          <div class="filename">{{filename}}</div>
          <div class="meta">Token: {{token}}</div>
        </div>

        <div class="actions">
          <a class="btn btn-primary" href="/download/{{token}}">Download</a>
        </div>
      </div>

      <div class="footer">
        The link is temporary and may expire automatically.
      </div>
    </section>
  </main>
</body>
</html>
"""

UPLOAD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Upload — Local Share</title>
  <style>
    :root {
      --bg1: #0f172a;
      --bg2: #111827;
      --card: rgba(17, 24, 39, 0.82);
      --card-border: rgba(255,255,255,0.10);
      --text: #e5e7eb;
      --muted: #9ca3af;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --shadow: 0 18px 60px rgba(0,0,0,0.35);
      --radius: 20px;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(79,70,229,0.20), transparent 28%),
        radial-gradient(circle at bottom right, rgba(14,165,233,0.16), transparent 26%),
        linear-gradient(160deg, var(--bg1), var(--bg2));
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .shell { width: min(100%, 560px); }

    .card {
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(10px);
    }

    .header {
      padding: 22px 22px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(79,70,229,0.16);
      color: #c7d2fe;
      font-size: 13px;
      font-weight: 600;
    }

    h1 {
      margin: 14px 0 8px;
      font-size: clamp(24px, 4vw, 34px);
      line-height: 1.1;
    }

    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.6;
    }

    .content { padding: 22px; }

    .msg {
      margin-bottom: 18px;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(34, 197, 94, 0.12);
      border: 1px solid rgba(34, 197, 94, 0.25);
      color: #bbf7d0;
      font-size: 14px;
      line-height: 1.5;
    }

    .filebox {
      border: 1px dashed rgba(255,255,255,0.16);
      background: rgba(255,255,255,0.03);
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 18px;
    }

    .label {
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      margin-bottom: 8px;
    }

    input[type="file"] {
      width: 100%;
      color: var(--muted);
      font-size: 14px;
    }

    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 18px;
    }

    .btn {
      appearance: none;
      border: 0;
      border-radius: 14px;
      padding: 14px 18px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      text-align: center;
      transition: transform 0.12s ease, background 0.2s ease, box-shadow 0.2s ease;
      min-width: 180px;
      flex: 1 1 180px;
    }

    .btn:active { transform: translateY(1px); }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent), #7c3aed);
      color: white;
      box-shadow: 0 12px 30px rgba(79,70,229,0.30);
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, var(--accent-hover), #6d28d9);
    }

    .footer {
      padding: 0 22px 22px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    @media (max-width: 480px) {
      body { padding: 14px; }
      .content, .header, .footer { padding-left: 16px; padding-right: 16px; }
      .btn { min-width: 100%; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card">
      <div class="header">
        <span class="badge">Local Share</span>
        <h1>Upload a file</h1>
        <p class="subtitle">Choose a file from your phone or laptop and send it to this device.</p>
      </div>

      <div class="content">
        {% if msg %}
        <div class="msg">{{ msg }}</div>
        {% endif %}

        <form class="filebox" action="/upload" method="post" enctype="multipart/form-data">
          <span class="label">Select file</span>
          <input id="file" name="file" type="file" required multiple>
          <div class="actions">
            <button class="btn btn-primary" type="submit">Upload</button>
          </div>
        </form>
      </div>

      <div class="footer">
        Your file will be saved on the server after upload.
      </div>
    </section>
  </main>
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
        <h1>Simple Local Share Server Running</h1>
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
    name_file = os.path.join(share_dir(token), "filename.txt")
    if not os.path.exists(name_file):
        return "Invalid or expired link", 404

    with open(name_file, encoding="utf-8") as fh:
        filename = fh.read().strip()

    path = os.path.join(share_dir(token), filename)
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
    name_file = os.path.join(share_dir(token), "filename.txt")
    if not os.path.exists(name_file):
        return "Invalid or expired link", 404

    with open(name_file, encoding="utf-8") as fh:
        filename = fh.read().strip()

    path = os.path.join(share_dir(token), filename)
    if not os.path.exists(path):
        return "Invalid or expired link", 404

    return send_file(path, as_attachment=True, download_name=filename)


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
    Saves selected file(s) to UPLOADS_DIR and redirects to upload page with message.

    Returns:
    - Redirect to /upload with success message
    """
    if 'file' not in request.files:
        return "No file", 400

    files = request.files.getlist('file')
    uploaded_files = []

    for f in files:
        if not f or not f.filename:
            continue

        filename = secure_filename(os.path.basename(f.filename))
        if not filename:
            continue

        path = os.path.join(UPLOADS_DIR, filename)
        f.save(path)
        uploaded_files.append(filename)

    if not uploaded_files:
        return "No valid file selected", 400

    msg = f" Uploaded successfully: {', '.join(uploaded_files)}"
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

    filename = os.path.basename(file_path)
    dest = os.path.join(d, filename)
    shutil.copy(file_path, dest)

    with open(os.path.join(d, "filename.txt"), "w", encoding="utf-8") as f:
        f.write(filename)

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
    if pyperclip is not None:
        try:
            pyperclip.copy(url)
            print("✅ Share link copied to clipboard!")
        except Exception:
            print("⚠️ Could not copy to clipboard.")
    else:
        print("⚠️ pyperclip is not installed; clipboard copy skipped.")

    print(f"\nQR Image saved at: {qr_path}\n")


# Cleanup

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
                    with open(exp_file) as fh:
                        exp = float(fh.read())
                    if now > exp:
                        shutil.rmtree(d, ignore_errors=True)
            except Exception:
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
            target=lambda: app.run(host=args.host, port=args.port, use_reloader=False),
            daemon=True
        ).start()

        time.sleep(1)

        create_share(args.file, args.host, args.port, args.ttl)

        print("\n🚀 Server running... Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n Server stopped cleanly")

    elif args.cmd == "serve":
        threading.Thread(target=cleanup, daemon=True).start()
        app.run(host=args.host, port=args.port, use_reloader=False)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
