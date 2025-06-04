from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"
DATA_FILE = "reactions.json"
DB_FILE = DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "users.db"))
UPLOAD_FOLDER = os.path.join(app.static_folder, 'reviews')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
REVIEW_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "reviews.json"))

# ----- DB SETUP -----
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
        conn.commit()

# ----- REACTION/ REVIEW STORAGE -----
def load_reviews():
    if not os.path.exists(REVIEW_FILE):
        return []
    with open(REVIEW_FILE, "r") as f:
        return json.load(f)

def save_reviews(reviews):
    with open(REVIEW_FILE, "w") as f:
        json.dump(reviews, f)

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

@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    if request.method == "POST":
        username = session.get("username", "Anonymous")
        text = request.form.get("text", "").strip()
        image_file = request.files.get("image")

        if not text:
            return "Text is required", 400

        image_filename = ""
        if image_file and image_file.filename:
            image_filename = f"{datetime.utcnow().timestamp()}_{secure_filename(image_file.filename)}"
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            image_file.save(image_path)

        review = {
            "username": username,
            "text": text,
            "image": f"reviews/{image_filename}" if image_filename else "",
            "timestamp": datetime.utcnow().isoformat()
        }

        reviews = load_reviews()
        reviews.insert(0, review)  # recent first
        save_reviews(reviews)
        return redirect(url_for("reviews"))

    reviews = load_reviews()
    return render_template("reviews.html", reviews=reviews)

# ----- MAIN -----
if __name__ == "__main__":
    init_db()
    app.run(debug=True)