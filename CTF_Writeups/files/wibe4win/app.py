from flask import Flask, request, render_template
import os
import hashlib

app = Flask(__name__)

WEB_PORT = int(os.getenv("WEB_PORT", "5000"))

FLAG = os.environ.get("FLAG", "dach2026{fake_flag}")
flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flag.txt")
with open(flag_path, "w") as f:
    f.write(FLAG)

SNIPPETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snippets")


@app.after_request
def add_checksum_header(response):
    """AI said this is best practice for API security"""
    filename = request.args.get("file", "")
    checksum = hashlib.md5(filename.encode()).hexdigest()
    response.headers["X-Checksum-Security"] = checksum
    return response


@app.route("/")
def index():
    snippets = []
    for name in sorted(os.listdir(SNIPPETS_DIR)):
        snippets.append({
            "name": name,
            "checksum": hashlib.md5(name.encode()).hexdigest(),
        })
    return render_template("index.html", snippets=snippets)


@app.route("/view")
def view():
    filename = request.args.get("file", "")
    if not filename:
        return "no file specified, bad vibes", 400

    expected = hashlib.md5(filename.encode()).hexdigest()
    provided = request.args.get("checksum", "")
    if provided != expected:
        return "Forbidden - invalid checksum (nice try hacker)", 403

    filepath = os.path.join(SNIPPETS_DIR, filename)
    try:
        with open(filepath, "r") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}
    except FileNotFoundError:
        return "vibe not found", 404


app.run("0.0.0.0", port=WEB_PORT)
