"""Legacy filename, new backend: MyceliaDB without SQL.

This Flask app is kept so existing start scripts still work, but it no longer
imports no SQL client and never opens a relational connection.  It talks to
the autarkic Mycelia platform API exposed by mycelia_platform.py.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any, Mapping

from flask import Flask, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "WebSessionSecretKey"
MYCELIA_API_URL = "http://127.0.0.1:9999"


def call_mycelia(command: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(
        {"command": command, "payload": dict(payload or {})},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        MYCELIA_API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, dict):
            return {"status": "error", "message": "Ungültige Mycelia-Antwort"}
        return decoded


HTML_LOGIN = """<!DOCTYPE html><html lang="de"><head><title>MyceliaDB</title><style>body{background:#121212;color:#00ff99;font-family:monospace;text-align:center;margin-top:50px}.box{border:1px solid #333;display:inline-block;padding:20px;background:#1e1e1e;margin:10px;width:310px;vertical-align:top}input{background:#333;border:1px solid #555;color:white;padding:8px;margin:5px;width:90%}button{background:#00ff99;border:none;padding:10px;font-weight:bold;cursor:pointer;width:95%}.alert{color:#ffcc66}</style></head><body><h1>MYCELIA ENTERPRISE DB</h1><p class="alert">{{ msg }}</p><div class="box"><h2>Login via CognitiveCore</h2><form method="post" action="/login"><input type="text" name="user" placeholder="Username" required><br><input type="password" name="pass" placeholder="Passwort" required><br><button type="submit">ATTRAKTOR PRÜFEN</button></form></div><div class="box"><h2>Registrierung</h2><form method="post" action="/register"><input type="text" name="user" placeholder="Username" required><br><input type="password" name="pass" placeholder="Passwort" required><br><hr><input type="text" name="vorname" placeholder="Vorname"><br><input type="text" name="nachname" placeholder="Nachname"><br><input type="email" name="email" placeholder="E-Mail"><br><button type="submit">NUTRIENT-NODE ERZEUGEN</button></form></div></body></html>"""

HTML_PROFILE = """<!DOCTYPE html><html lang="de"><head><style>body{background:#121212;color:#e0e0e0;font-family:monospace;padding:50px}.raw{background:#000;color:#777;padding:15px;border:1px dashed #333;margin-bottom:20px;word-break:break-all;font-size:10px}input{background:#222;border:1px solid #444;color:white;padding:8px;margin:5px}button{background:#00ff99;border:none;padding:10px;font-weight:bold;cursor:pointer}a{color:#00ff99;margin-left:10px}</style></head><body><h1>User: {{ username }}</h1><p style="color:#00ff99">{{ msg }}</p><h3>Mycelia Node</h3><div class="raw">SIGNATURE: {{ signature }}<br>STABILITY: {{ node.stability }}<br>MODE: {{ mode }}</div><h3>QuantumOracle-Rekonstruktion</h3><form method="post" action="/update"><input type="text" name="vorname" value="{{ data.vorname }}"><input type="text" name="nachname" value="{{ data.nachname }}"><input type="email" name="email" value="{{ data.email }}"><button type="submit">Update</button><a href="/logout">Logout</a></form></body></html>"""


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template_string(HTML_LOGIN, msg="")


@app.route("/register", methods=["POST"])
def register():
    payload = {
        "username": request.form["user"],
        "password": request.form["pass"],
        "profile": {
            "vorname": request.form.get("vorname", ""),
            "nachname": request.form.get("nachname", ""),
            "email": request.form.get("email", ""),
        },
    }
    result = call_mycelia("register_user", payload)
    msg = "Registrierung erfolgreich." if result.get("status") == "ok" else result.get("message", "Fehler")
    return render_template_string(HTML_LOGIN, msg=msg)


@app.route("/login", methods=["POST"])
def login():
    result = call_mycelia(
        "login_attractor",
        {"username": request.form["user"], "password": request.form["pass"]},
    )
    if result.get("status") == "ok":
        session["mycelia_signature"] = result["signature"]
        session["mycelia_username"] = result["username"]
        return redirect(url_for("profile"))
    return render_template_string(HTML_LOGIN, msg=result.get("message", "Falsche Daten."))


@app.route("/profile")
def profile():
    signature = session.get("mycelia_signature")
    if not signature:
        return redirect("/")
    result = call_mycelia("get_profile", {"signature": signature})
    if result.get("status") != "ok":
        return "CRITICAL INTEGRITY ERROR", 500
    return render_template_string(
        HTML_PROFILE,
        username=result.get("username", session.get("mycelia_username")),
        data=result.get("profile", {}),
        node=result.get("node", {}),
        signature=signature,
        mode=result.get("driver_mode", "unknown"),
        msg="",
    )


@app.route("/update", methods=["POST"])
def update():
    signature = session.get("mycelia_signature")
    if not signature:
        return redirect("/")
    result = call_mycelia(
        "update_profile",
        {
            "signature": signature,
            "profile": {
                "vorname": request.form.get("vorname", ""),
                "nachname": request.form.get("nachname", ""),
                "email": request.form.get("email", ""),
            },
        },
    )
    if result.get("status") == "ok":
        session["mycelia_signature"] = result.get("signature", signature)
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    print("--- Mycelia Enterprise Server (DAD/OpenCL Backend, no SQL) ---")
    app.run(debug=True, use_reloader=False)
