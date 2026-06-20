import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WATCHMODE_API_KEY")
BASE_URL = "https://api.watchmode.com/v1"


def normalize(name):
    """Normalize a service name so 'Paramount+' and 'Paramount Plus' match."""
    return (
        name.lower()
        .replace("+", "plus")
        .replace(" ", "")
        .strip()
    )


def get_title_details(watchmode_id, user_services):
    """Fetch details + streaming sources for one title.
    Returns matched services (on the user's list) AND all available sub/free sources."""
    url = f"{BASE_URL}/title/{watchmode_id}/details/"
    params = {
        "apiKey": API_KEY,
        "append_to_response": "sources",
        "regions": "US",
    }
    response = requests.get(url, params=params)
    data = response.json()

    sources_data = data.get("sources") or []

    matching_services = []
    all_sources = []
    for source in sources_data:
        if not isinstance(source, dict):
            continue
        source_name = source.get("name", "")
        source_type = source.get("type", "")

        # Subscription or free only -- skip "rent" and "buy"
        if source_type not in ("sub", "free"):
            continue
        # Skip "Via" add-on listings
        if "via" in source_name.lower():
            continue

        # Collect every available source name (de-duplicated)
        if source_name not in all_sources:
            all_sources.append(source_name)

        # Collect the ones that match the user's services
        sn = normalize(source_name)
        for service in user_services:
            if normalize(service) == sn and service not in matching_services:
                matching_services.append(service)

    network_display = ", ".join(matching_services) if matching_services else None
    all_sources_display = ", ".join(all_sources[:4]) if all_sources else None

    plot = data.get("plot_overview", "") or ""
    if len(plot) > 150:
        plot = plot[:150] + "..."

    return {
        "network": network_display,
        "all_sources": all_sources_display,
        "plot": plot or "No description available",
        "imdb_rating": data.get("user_rating", None),
    }


def search_shows(query, user_services, ignore_services=False):
    """Search Watchmode, then enrich the top results with source/network data.
    If ignore_services is True, return all results regardless of service match."""
    url = f"{BASE_URL}/search/"
    params = {
        "apiKey": API_KEY,
        "search_field": "name",
        "search_value": query,
        "types": "tv,movie",
    }
    response = requests.get(url, params=params)
    data = response.json()

    results = []
    for item in data.get("title_results", []):
        type_raw = item.get("type", "")

        # Skip individual episodes / specials
        if type_raw in ("tv_episode", "tv_special"):
            continue

        type_display = "tv" if "tv" in type_raw else "movie"

        results.append({
            "watchmode_id": item["id"],
            "title": item["name"],
            "type": type_display,
            "type_label": type_raw.replace("_", " ").title(),
            "year": item.get("year", None),
            "imdb_id": item.get("imdb_id", ""),
        })

    # Keep Watchmode's native relevance order
    top_results = results[:10]

    enriched = []
    for result in top_results:
        time.sleep(0.3)
        details = get_title_details(result["watchmode_id"], user_services)
        result["network"] = details["network"]
        result["plot"] = details["plot"]
        result["imdb_rating"] = details["imdb_rating"]

        if ignore_services:
            # Show everything; if not on the user's services, show where it IS
            # and tag those sources as not subscribed
            if result["network"] is None:
                if details["all_sources"]:
                    result["network"] = details["all_sources"] + " (not subscribed)"
                else:
                    result["network"] = "No streaming source found"
            enriched.append(result)
        else:
            # Normal mode: only include shows on the user's services
            if result["network"] is not None:
                enriched.append(result)

    # Tell the caller whether a wider search would surface anything new
    found_but_filtered = (len(top_results) > 0 and len(enriched) == 0 and not ignore_services)

    return {"results": enriched, "found_but_filtered": found_but_filtered}

def get_purchase_options(watchmode_id):
    """Fetch rent/buy options for a title. Informational only -- no links.
    Returns a list of dicts: [{name, type, price}, ...] sorted by price."""
    url = f"{BASE_URL}/title/{watchmode_id}/details/"
    params = {
        "apiKey": API_KEY,
        "append_to_response": "sources",
        "regions": "US",
    }
    response = requests.get(url, params=params)
    data = response.json()

    title = data.get("title", "Unknown")
    year = data.get("year", "")
    sources_data = data.get("sources") or []

    options = []
    seen = set()
    for source in sources_data:
        if not isinstance(source, dict):
            continue
        source_type = source.get("type", "")
        # Only rent and buy for this page
        if source_type not in ("rent", "buy"):
            continue

        name = source.get("name", "")
        price = source.get("price", None)

        # De-duplicate on name+type+price (Watchmode often repeats entries)
        key = (name, source_type, price)
        if key in seen:
            continue
        seen.add(key)

        options.append({
            "name": name,
            "type": source_type.capitalize(),  # "Rent" or "Buy"
            "price": price,
        })

    # Sort by price (cheapest first); entries with no price go last
    options.sort(key=lambda x: (x["price"] is None, x["price"] or 0))

    return {"title": title, "year": year, "options": options}

from datetime import date

def get_aired_season_count(watchmode_id):
    """Return the number of seasons that have already aired (air_date today or earlier)."""
    url = f"{BASE_URL}/title/{watchmode_id}/details/"
    params = {
        "apiKey": API_KEY,
        "append_to_response": "seasons",
        "regions": "US",
    }
    response = requests.get(url, params=params)
    data = response.json()

    seasons = data.get("seasons") or []
    today = date.today().isoformat()  # "YYYY-MM-DD" string, comparable to air_date

    aired = 0
    for s in seasons:
        air_date = s.get("air_date")
        # Count a season only if it has an air date that isn't in the future.
        # Season 0 is usually "specials" - skip it.
        if s.get("number", 0) == 0:
            continue
        if air_date and air_date <= today:
            aired += 1

    return aired