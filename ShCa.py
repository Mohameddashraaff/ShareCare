#!/usr/bin/env python3
# ShCa ultra-simplified — file sharing + QR code
# Fully documented and visually expanded version

import os
import time
import secrets
import shutil
import threading
import argparse
import socket

from flask import Flask, request, send_file, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import qrcode

try:
    import pyperclip  # Optional clipboard auto-copy
except Exception:
    pyperclip = None


# Base Directory

BASE_DIR = os.path.abspath(".")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
SHARES_DIR = os.path.join(BASE_DIR, "shares")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(SHARES_DIR, exist_ok=True)


# Flask App Setup

app = Flask(__name__)


# FUNCTIONS

def generate_token(n=8):
    """
    Generate a random alphanumeric token used for share URLs.
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(alphabet) for _ in range(n))


def share_dir(token):
    """
    Return the directory path for a given share token.
    """
    return os.path.join(SHARES_DIR, token)


def display_ascii_banner():
    """
    Display a large ASCII banner for ShCA in the terminal.
    """
    banner = r"""
   _____ _    ____ ____  
  / ____| |  / ___/ ___| 
 | (___ | | | |  | |     
  \___ \| | | |  | |     
  ____) | | | |__| |___  
 |_____/|_|  \____\____| 
                          
        ShCA - Local File Share
    """
    print(banner)


def get_local_ip():
    """
    Try to detect the local network IP address automatically.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# HTML Templates

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
    }

    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }

    .content { padding: 22px; }

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

    .actions { display: flex; gap: 12px; flex-wrap: wrap; }

    .btn {
      border: 0;
      border-radius: 14px;
      padding: 14px 18px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      text-align: center;
      min-width: 180px;
      flex: 1 1 180px;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent), #7c3aed);
      color: white;
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card">
      <div class="header">
        <span class="badge">Local Share</span>
        <h1>Ready to download</h1>
        <p class="subtitle">Download the file below.</p>
      </div>

      <div class="content">
        <div class="filebox">
          <span class="label">Filename</span>
          <div class="filename">{{filename}}</div>
        </div>

        <div class="actions">
          <a class="btn btn-primary" href="/download/{{token}}">Download</a>
        </div>
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
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
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
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(79,70,229,0.16);
      color: #c7d2fe;
      font-size: 13px;
      font-weight: 600;
    }

    h1 { margin: 14px 0 8px; font-size: 30px; }

    .subtitle { margin: 0; color: var(--muted); font-size: 15px; }

    .content { padding: 22px; }

    .msg {
      margin-bottom: 18px;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(34, 197, 94, 0.12);
      border: 1px solid rgba(34, 197, 94, 0.25);
      color: #bbf7d0;
      font-size: 14px;
    }

    .filebox {
      border: 1px dashed rgba(255,255,255,0.16);
      background: rgba(255,255,255,0.03);
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 18px;
    }

    input[type="file"] {
      width: 100%;
      color: var(--muted);
      font-size: 14px;
    }

    .btn {
      width: 100%;
      border: 0;
      border-radius: 14px;
      padding: 14px 18px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      background: linear-gradient(135deg, var(--accent), #7c3aed);
      color: white;
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card">
      <div class="header">
        <span class="badge">Local Share</span>
        <h1>Upload a file</h1>
        <p class="subtitle">Send a file from your phone to this laptop.</p>
      </div>

      <div class="content">
        {% if msg %}
        <div class="msg">{{ msg }}</div>
        {% endif %}

        <form class="filebox" action="/upload" method="post" enctype="multipart/form-data">
          <input name="file" type="file" required multiple>
          <br><br>
          <button class="btn" type="submit">Upload</button>
        </form>
      </div>
    </section>
  </main>
</body>
</html>
"""


# ROUTES

@app.route("/")
def index():
    return redirect("/upload")


@app.route("/upload", methods=["GET"])
@app.route("/upload/", methods=["GET"])
def upload_page():
    msg = request.args.get("msg")
    return render_template_string(UPLOAD_HTML, msg=msg)


@app.route("/upload", methods=["POST"])
@app.route("/upload/", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file", 400

    files = request.files.getlist("file")
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
    return redirect(url_for("upload_page", msg=msg))


@app.route("/share/<token>")
def share_page(token):
    name_file = os.path.join(share_dir(token), "filename.txt")
    if not os.path.exists(name_file):
        return "Invalid or expired link", 404

    with open(name_file, encoding="utf-8") as fh:
        filename = fh.read().strip()

    path = os.path.join(share_dir(token), filename)
    if not os.path.exists(path):
        return "Invalid or expired link", 404

    return render_template_string(DOWNLOAD_HTML, token=token, filename=os.path.basename(path))


@app.route("/download/<token>")
def download(token):
    name_file = os.path.join(share_dir(token), "filename.txt")
    if not os.path.exists(name_file):
        return "Invalid or expired link", 404

    with open(name_file, encoding="utf-8") as fh:
        filename = fh.read().strip()

    path = os.path.join(share_dir(token), filename)
    if not os.path.exists(path):
        return "Invalid or expired link", 404

    return send_file(path, as_attachment=True, download_name=filename)


# SHARE FUNCTION

def create_share(file_path, host, port, ttl):
    if not os.path.exists(file_path):
        print(" File not found")
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

    url = f"http://{host}:{port}/share/{token}"

    qr_path = os.path.join(d, "qr.png")
    qrcode.make(url).save(qr_path)

    print("\n Share created!")
    print(" Link:", url)

    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make()
    qr.print_ascii(invert=True)

    if pyperclip is not None:
        try:
            pyperclip.copy(url)
            print(" Link copied to clipboard!")
        except Exception:
            pass

    print(f"📷 QR saved at: {qr_path}\n")


# CLEANUP

def cleanup():
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


# MAIN

def main():
    display_ascii_banner()

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    share = sub.add_parser("share")
    share.add_argument("--file", required=True, help="Path to file anywhere")
    share.add_argument("--host", default="127.0.0.1")
    share.add_argument("--port", type=int, default=8080)
    share.add_argument("--ttl", type=int, default=30)

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

        local_ip = get_local_ip()

        print("\n ShCA Server Started Successfully!\n")
        print(" Upload Page (use this on your phone):")
        print(f"   http://{local_ip}:{args.port}/upload\n")
        print(" You can also access locally:")
        print(f"   http://127.0.0.1:{args.port}/upload\n")
        print("Press Ctrl+C to stop the server.\n")

        app.run(host=args.host, port=args.port, use_reloader=False)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
