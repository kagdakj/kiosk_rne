from flask import Flask, render_template, send_file, send_from_directory, redirect, url_for

app = Flask(__name__, static_folder="static")

@app.route('/<path:path>')
def send_report(path):
    # Using request args for path will expose you to directory traversal attacks
    return send_from_directory('static', path)

@app.route('/')
def home():
    return redirect("static/main.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)