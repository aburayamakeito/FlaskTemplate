import os
from flask import Flask, request, render_template

app = Flask(__name__, instance_relative_config=True)

# 標準設定ファイル読み込み
app.config.from_object("settings")

# 非公開設定ファイル読み込み
if app.config["ENV"] == "development":
    app.config.from_pyfile(os.path.join("config", "development.py"), silent=True)
else:
    app.config.from_pyfile(os.path.join("config", "production.py"), silent=True)

@app.route("/", methods=("GET", "POST"))
@app.route("/<string:greeting>", methods=("GET", "POST"))
def greeting_user(greeting="Hello"):
    if request.method == "POST":
        user_name = request.form["user_name"]
    else:
        user_name = request.args.get("user_name", "")

    return render_template("greeting.html", greeting=greeting, user_name=user_name)