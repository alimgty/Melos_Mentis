from dotenv import load_dotenv
load_dotenv()

import os
import sys
import traceback
import subprocess

from flask import Flask, render_template, Response, jsonify, request, session, flash, redirect, url_for
from flask_session import Session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

from models.emotion_context import gen_frames, capture_for_30_seconds
from chatbot.chatbot import get_bot_response

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
# read MONGO_URI from env; ensure no leading/trailing whitespace
raw_uri = os.getenv("MONGO_URI", "mongodb+srv://divyanshu:divyanshu123@cluster0.rdc0nfb.mongodb.net/melos_mentis?appName=Cluster0")
if raw_uri is None:
    raw_uri = ""
MONGO_URI = raw_uri.strip()
app.config["MONGO_URI"] = MONGO_URI
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# Debug: show what MONGO_URI the app is using (repr to show whitespace)
print("MONGO_URI repr:", repr(raw_uri))
print("Using MONGO_URI (stripped) repr:", repr(MONGO_URI))

users_coll = None
mongo = None
try:
    mongo = PyMongo(app)
    users_coll = mongo.db.users
    print("Mongo initialized. users_coll:", users_coll)
    try:
        # list existing collections in the default database (may be empty)
        print("Existing collections:", mongo.db.list_collection_names())
    except Exception as e:
        print("Could not list collections:", repr(e))
except Exception as e:
    print("MongoDB connection failed during init:", repr(e))
    users_coll = None

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/signup', methods=["POST"])
def signup():
    print(">>> /signup called")
    print("users_coll is None?", users_coll is None)
    if users_coll is None:
        flash("Database connection error!", "error")
        print("Signup aborted: DB not available")
        return redirect("/")

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    print("Form received:", {"username": username, "email": email, "password_present": bool(password)})

    try:
        existing = users_coll.find_one({"email": email})
        print("Existing user check result:", existing)
        if existing:
            flash("Email already exists!", "error")
            print("Signup aborted: email exists")
            return redirect("/")

        hashed_password = generate_password_hash(password)
        res = users_coll.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password
        })
        print("Inserted user id:", getattr(res, "inserted_id", None))
        # Debug: show collections after insert
        try:
            print("Collections after insert:", mongo.db.list_collection_names())
        except Exception:
            pass

        flash("Sign-up successful! Please log in.", "success")
        return redirect("/")
    except Exception as e:
        traceback.print_exc()
        flash("An error occurred while saving to DB: " + str(e), "error")
        return redirect("/")

@app.route('/login', methods=['POST'])
def login():
    if users_coll is None:
        flash("Database connection error!", "error")
        return redirect("/")

    email = request.form.get("email")
    password = request.form.get("password")

    try:
        user = users_coll.find_one({"email": email})
        print("Login lookup result:", user)
        if user and check_password_hash(user.get("password", ""), password):
            session["user"] = user.get("username")
            flash("Login successful!", "success")
            return redirect("/dashboard")
        else:
            flash("Invalid credentials!", "error")
            return redirect("/")
    except Exception as e:
        traceback.print_exc()
        flash("An error occurred while logging in: " + str(e), "error")
        return redirect("/")

@app.route('/dashboard')
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", username=session.get('user'))
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
        base_dir = os.path.dirname(os.path.abspath(__file__))

        gp = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'models', 'generate_prompt.py')],
            check=True,
            capture_output=True,
            text=True,
            cwd=base_dir
        )
        print("Generate Prompt Output:\n", gp.stdout)

        gt = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'models', 'tune_generation.py')],
            check=True,
            capture_output=True,
            text=True,
            cwd=base_dir
        )
        print("Tune Generation Output:\n", gt.stdout)

        generated_path = os.path.join(base_dir, 'static', 'generated_tune.wav')
        if not os.path.exists(generated_path):
            raise FileNotFoundError(f"Expected audio not found at {generated_path}")

        audio_url = url_for('static', filename='generated_tune.wav')
        return jsonify({'status': 'success', 'audio_url': audio_url})

    except subprocess.CalledProcessError as e:
        print("Subprocess error stdout/stderr:\n", getattr(e, "stdout", None), getattr(e, "stderr", None))
        return jsonify({'status': 'error', 'message': (e.stderr or e.stdout or str(e))}), 500
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
