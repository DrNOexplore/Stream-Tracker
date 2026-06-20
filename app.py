from flask import Flask, render_template, request, jsonify
import watchmode
import sheets
import json
import os

app = Flask(__name__)

# Streaming services using Watchmode-style naming
STREAMING_SERVICES = [
    "Netflix",
    "Prime Video",
    "Max",
    "Disney+",
    "Hulu",
    "Paramount+",
    "Paramount+ with Showtime",
    "AppleTV+",
    "Peacock Premium",
    "ESPN+",
    "AMC+",
    "Shudder",
    "Britbox",
    "STARZ",
    "MGM+",
]

SETTINGS_FILE = "settings.json"

def get_user_services():
    """Return the user's selected services from the settings file.
    Defaults to all services if the file doesn't exist yet."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                return data.get("services", STREAMING_SERVICES)
        except (json.JSONDecodeError, IOError):
            # If the file is corrupted or unreadable, fall back to defaults
            return STREAMING_SERVICES
    return STREAMING_SERVICES

def save_user_services(services):
    """Write the user's selected services to the settings file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"services": services}, f, indent=2)

@app.route("/")
def home():
    return render_template("index.html", services=get_user_services())

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        selected = request.json.get("services", [])
        save_user_services(selected)
        return jsonify({"success": True})
    return render_template(
        "settings.html",
        all_services=STREAMING_SERVICES,
        selected_services=get_user_services(),
    )

@app.route("/search")
def search():
    query = request.args.get("query", "")
    expand = request.args.get("expand", "false") == "true"
    if not query:
        return jsonify({"results": [], "found_but_filtered": False})
    user_services = get_user_services()
    data = watchmode.search_shows(query, user_services, ignore_services=expand)
    return jsonify(data)

@app.route("/my-list")
def my_list():
    rows = sheets.get_all_shows()
    # First row is the header; the rest are shows
    header = rows[0] if rows else []
    shows = rows[1:] if len(rows) > 1 else []

    # Convert each row into a dictionary for easy template access
    show_list = []
    for row in shows:
        # Pad short rows so we never get an index error
        padded = row + [""] * (8 - len(row))
        show_list.append({
            "title": padded[0],
            "type": padded[1],
            "network": padded[2],
            "status": padded[3],
            "watchmode_id": padded[4],
            "year": padded[5],
            "last_known_seasons": padded[6],
            "last_checked": padded[7],
        })
    return render_template("my_list.html", shows=show_list)

@app.route("/where-to-watch")
def where_to_watch():
    watchmode_id = request.args.get("id", "")
    if not watchmode_id:
        return render_template("where_to_watch.html", data=None)
    data = watchmode.get_purchase_options(watchmode_id)
    return render_template("where_to_watch.html", data=data)

@app.route("/update-status", methods=["POST"])
def update_status_route():
    data = request.json
    result = sheets.update_status(
        watchmode_id=data.get("watchmode_id", ""),
        new_status=data.get("status", "")
    )
    return jsonify({"success": result == "updated", "result": result})


@app.route("/delete-show", methods=["POST"])
def delete_show_route():
    data = request.json
    result = sheets.delete_show(watchmode_id=data.get("watchmode_id", ""))
    return jsonify({"success": result == "deleted", "result": result})

@app.route("/add-show", methods=["POST"])
def add_show():
    data = request.json
    result = sheets.add_show(
        title=data.get("title", ""),
        type_label=data.get("type", ""),
        network=data.get("network", ""),
        status=data.get("status", ""),
        watchmode_id=data.get("watchmode_id", ""),
        year=data.get("year", ""),
    )
    if result == "duplicate":
        return jsonify({"success": False, "error": "Already in your list"})
    return jsonify({"success": True, "message": "Show added"})

from datetime import date

@app.route("/refresh-show", methods=["POST"])
def refresh_show():
    data = request.json
    watchmode_id = data.get("watchmode_id", "")
    if not watchmode_id:
        return jsonify({"success": False, "error": "No show specified"})

    current_count = watchmode.get_aired_season_count(watchmode_id)
    stored_count = sheets.get_season_baseline(watchmode_id)
    today = date.today().isoformat()

    # Always update the sheet with the current count and today's date
    sheets.update_season_baseline(watchmode_id, current_count, today)

    if stored_count is None:
        # First check - just establishing the baseline, nothing is "new"
        status = "baseline_set"
        message = f"Tracking started — {current_count} season(s) on record."
    elif current_count > stored_count:
        status = "new_season"
        message = f"🎉 New season! Now {current_count} (was {stored_count})."
    else:
        status = "no_change"
        message = f"No new seasons. Still {current_count}."

    return jsonify({
        "success": True,
        "status": status,
        "message": message,
        "current_count": current_count
    })

if __name__ == "__main__":
    app.run(debug=True)