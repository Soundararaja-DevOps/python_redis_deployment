import os
import redis
from pymongo import MongoClient, errors
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")

# MongoDB connection
name_collection = None
try:
    mongo_client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
    mongo_client.server_info()
    mongo_db = mongo_client["testdb"]
    name_collection = mongo_db["names"]
except errors.ServerSelectionTimeoutError as e:
    print(f"[MongoDB ERROR] Could not connect to MongoDB: {e}")

# Redis connection
redis_client = None
try:
    redis_client = redis.Redis.from_url(redis_url)
    redis_client.ping()
except redis.exceptions.RedisError as e:
    print(f"[Redis ERROR] Could not connect to Redis: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        name = request.form.get("name")
        try:
            if name_collection is not None and name:
                name_collection.insert_one({"name": name})
            if redis_client is not None and name:
                redis_client.set("last_name", name)
        except Exception as e:
            error = str(e)
        return redirect("/")

    names = []
    last_name = "None"
    try:
        if name_collection is not None:
            names = [doc["name"] for doc in name_collection.find()]
        if redis_client is not None:
            last_name_raw = redis_client.get("last_name")
            last_name = last_name_raw.decode() if last_name_raw else "None"
    except Exception as e:
        error = str(e)

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BMW | Name Logger</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #0a0a0a;
            font-family: 'Inter', Helvetica, Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            color: #f1f1f1;
        }

        .container {
            background: #111;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            max-width: 500px;
            width: 100%;
            text-align: center;
        }

        h2 {
            margin-bottom: 20px;
            font-weight: 600;
            font-size: 26px;
            color: #fff;
        }

        form {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            justify-content: center;
        }

        input {
            padding: 10px 12px;
            font-size: 16px;
            background: #222;
            color: #fff;
            border: 1px solid #333;
            border-radius: 6px;
            flex: 1;
        }

        button {
            padding: 10px 16px;
            background-color: #1c69d4;
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s ease-in-out;
        }

        button:hover {
            background-color: #155ab6;
        }

        .info, ul {
            text-align: left;
            margin-top: 10px;
        }

        ul {
            padding-left: 20px;
        }

        li {
            padding: 4px 0;
            color: #ccc;
        }

        .error {
            color: #ff4d4d;
            margin-bottom: 20px;
            font-size: 14px;
        }

        @media (max-width: 500px) {
            form {
                flex-direction: column;
            }
            button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>BMW Name Logger</h2>
        {% if error %}
            <p class="error">Error: {{ error }}</p>
        {% endif %}
        <form method="post">
            <input name="name" placeholder="Your Name" required>
            <button type="submit">Submit</button>
        </form>
        <p class="info">Last name in Redis: <strong>{{ last_name }}</strong></p>
        <h3>All Names:</h3>
        <ul>{% for name in names %}<li>{{ name }}</li>{% endfor %}</ul>
    </div>
</body>
</html>
""", names=names, last_name=last_name, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999)
