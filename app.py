from flask import Flask, render_template, Response, jsonify, request
from models.emotion_context import gen_frames, capture_for_30_seconds
from flask_pymongo import PyMongo
from flask_session import Session
from flask import session, flash, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os
import sys
import traceback
from chatbot.chatbot import get_bot_response

app = Flask(__name__)

app.secret_key = "supersecretkey123"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://divyanshurajoria1:div4@cluster0.eugyn.mongodb.net/users?retryWrites=true&w=majority"

try:
    mongo = PyMongo(app)
    db = mongo.db.users  
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    db = None  

# Enable Flask session management
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/signup', methods=["POST"])
def signup():
    if db is None:
        flash("Database connection error!", "error")
        return redirect("/")

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    if db.find_one({"email": email}):
        flash("Email already exists!", "error")
        return redirect("/")

    hashed_password = generate_password_hash(password)
    db.insert_one({"username": username, "email": email, "password": hashed_password})
    flash("Sign-up successful! Please log in.", "success")
    return redirect("/")

@app.route('/login', methods=["POST"])
def login():
    if db is None:
        flash("Database connection error!", "error")
        return redirect("/")

    email = request.form["email"]
    password = request.form["password"]
    user = db.find_one({"email": email})

    if user and check_password_hash(user["password"], password):
        session["user"] = user["username"]
        flash("Login successful!", "success")
        return redirect("/dashboard")
    else:
        flash("Invalid credentials!", "error")
        return redirect("/")

@app.route('/dashboard')
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", username=session['user'])
    flash("You need to log in first.", "error")
    return redirect("/")

@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("Logged out successfully!", "success")
    return redirect("/")

@app.route('/video')
def video():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
def capture():
    results = capture_for_30_seconds()
    return jsonify({
        "status": "success",
        "message": "Capture completed!",
        "emotions": results.get("emotions", []),
        "objects": results.get("objects", [])
    })

@app.route('/start_music_therapy', methods=['POST'])
def start_music_therapy():
    try:
        print("Flask is using:", sys.executable)

        # Step 1: Generate Music Prompt
        result_prompt = subprocess.run(
            [sys.executable, 'models/generate_prompt.py'],
            check=True,
            capture_output=True,
            text=True
        )
        print("Generate Prompt Output:\n", result_prompt.stdout)

        print(">> Reached before calling tune_generation.py")

        # Step 2: Generate Music Tune
        result_tune = subprocess.run(
            [sys.executable, 'models/tune_generation.py'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'  # <-- Force UTF-8 decoding
        )

        print(">> Reached after calling tune_generation.py")
        print("Tune Generation Output:\n", result_tune.stdout)

        audio_url = '/static/generated_tune.wav'
        return jsonify({'status': 'success', 'audio_url': audio_url})

    except subprocess.CalledProcessError as e:
        print("Subprocess error:", e.stderr)
        return jsonify({'status': 'error', 'message': e.stderr}), 500
    except Exception as e:
        print("Unexpected error:", traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message", "")
    bot_response = get_bot_response(user_message)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
