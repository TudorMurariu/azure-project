from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = "reactions.json"

def load_reactions():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_reactions(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def index():
    images = os.path.join("static", "images")
    reactions = load_reactions()
    return render_template("index.html", images=images, reactions=reactions)

@app.route("/react", methods=["POST"])
def react():
    data = request.json
    image = data["image"]
    reaction = data["reaction"]
    
    reactions = load_reactions()
    if image not in reactions:
        reactions[image] = {"like": 0, "love": 0, "wow": 0}
    reactions[image][reaction] += 1
    save_reactions(reactions)
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)
