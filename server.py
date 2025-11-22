import json
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).parent.resolve()
DATA_FILE = BASE_DIR / "data_store.json"


def load_data() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_data(records: list[dict]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)


def add_backend_id(record: dict) -> dict:
    backend_id = record.get("__backendId") or record.get("id") or f"rec_{uuid4().hex}"
    record["__backendId"] = backend_id
    record.setdefault("id", backend_id)
    return record


app = Flask(__name__, static_folder=str(BASE_DIR))


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/records", methods=["GET", "POST"])
def records():
    records = load_data()
    if request.method == "GET":
        return jsonify([add_backend_id(rec.copy()) for rec in records])

    payload = request.get_json(force=True) or {}
    payload = add_backend_id(payload)
    records.append(payload)
    save_data(records)
    return jsonify(payload), 201


@app.route("/api/records/<backend_id>", methods=["PUT", "DELETE"])
def record_detail(backend_id: str):
    records = load_data()
    match_index = next((idx for idx, rec in enumerate(records) if rec.get("__backendId") == backend_id), None)

    if match_index is None:
        return jsonify({"error": "Record not found"}), 404

    if request.method == "DELETE":
        records.pop(match_index)
        save_data(records)
        return "", 204

    payload = request.get_json(force=True) or {}
    payload["__backendId"] = backend_id
    payload.setdefault("id", backend_id)
    records[match_index] = payload
    save_data(records)
    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True)

