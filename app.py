from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"
DATA_FILE = "reactions.json"
DB_FILE = DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "users.db"))

# ----- DB SETUP -----
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
        conn.commit()

# ----- REACTION STORAGE -----
def load_reactions():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_reactions(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ----- ROUTES -----
@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    images_path = os.path.join(app.static_folder, "images")
    try:
        images = os.listdir(images_path)
    except FileNotFoundError:
        images = []
    reactions = load_reactions()
    return render_template("index.html", images=images, reactions=reactions, username=session["username"])

@app.route("/react", methods=["POST"])
def react():
    if "username" not in session:
        return jsonify(success=False, message="Unauthorized"), 403

    data = request.json
    image = data["image"]
    reaction = data["reaction"]
    
    reactions = load_reactions()
    if image not in reactions:
        reactions[image] = {"like": 0, "love": 0, "wow": 0}
    reactions[image][reaction] += 1
    save_reactions(reactions)
    return jsonify(success=True)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        try:
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already taken!"
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username = ?", (username,))
            row = c.fetchone()
            if row and check_password_hash(row[0], password):
                session["username"] = username
                return redirect(url_for("index"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# ----- MAIN -----
if __name__ == "__main__":
    init_db()
    app.run(debug=True)