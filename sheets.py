import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Permission scope: read and write sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# PASTE YOUR SHEET ID BETWEEN THE QUOTES BELOW
SHEET_ID = "1tUWH96-Ia-c_e8kLQGQWko9soDxbS1MuOuf1Z5q8YOE"

# The tab/range we work with. "Sheet1" is the default tab name.
RANGE = "Sheet1!A:H"


def get_service():
    """Authenticate and return a Sheets API service object."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def get_all_shows():
    """Return every row in the sheet as a list of lists (including header)."""
    service = get_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=RANGE
    ).execute()
    return result.get("values", [])


def show_exists(watchmode_id):
    """Check whether a Watchmode_ID is already in the sheet."""
    rows = get_all_shows()
    # Watchmode_ID is column E = index 4. Skip the header row.
    for row in rows[1:]:
        if len(row) > 4 and str(row[4]) == str(watchmode_id):
            return True
    return False


def add_show(title, type_label, network, status, watchmode_id, year):
    """Append one show to the sheet if it isn't already there.
    Returns a status string: 'added' or 'duplicate'."""
    if show_exists(watchmode_id):
        return "duplicate"

    new_row = [[
        title,
        type_label,
        network,
        status,
        str(watchmode_id),
        str(year),
    ]]

    service = get_service()
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=RANGE,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": new_row}
    ).execute()
    return "added"

def update_status(watchmode_id, new_status):
    """Find the show by Watchmode_ID and update its Status cell.
    Returns 'updated' or 'not_found'."""
    rows = get_all_shows()

    # Find the row index. Row 0 is the header, so sheet row numbers
    # are list-index + 1 (sheets are 1-based).
    for i, row in enumerate(rows):
        if i == 0:
            continue  # skip header
        if len(row) > 4 and str(row[4]) == str(watchmode_id):
            sheet_row_number = i + 1  # convert to 1-based sheet row
            # Status is column D
            target_range = f"Sheet1!D{sheet_row_number}"
            service = get_service()
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=target_range,
                valueInputOption="USER_ENTERED",
                body={"values": [[new_status]]}
            ).execute()
            return "updated"
    return "not_found"


def delete_show(watchmode_id):
    """Remove a show by rewriting the sheet without it.
    Returns 'deleted' or 'not_found'."""
    rows = get_all_shows()
    if not rows:
        return "not_found"

    header = rows[0]
    kept = []
    found = False
    for row in rows[1:]:
        if len(row) > 4 and str(row[4]) == str(watchmode_id):
            found = True
            continue  # skip the one we're deleting
        kept.append(row)

    if not found:
        return "not_found"

    service = get_service()

    # Clear the whole data area first, then write back what we kept
    service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A:F"
    ).execute()

    new_values = [header] + kept
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A1",
        valueInputOption="USER_ENTERED",
        body={"values": new_values}
    ).execute()

    return "deleted"

def update_season_baseline(watchmode_id, season_count, checked_date):
    """Write the known season count (col G) and last-checked date (col H)
    for the row matching watchmode_id. Returns 'updated' or 'not_found'."""
    rows = get_all_shows()
    for i, row in enumerate(rows):
        if i == 0:
            continue  # header
        if len(row) > 4 and str(row[4]) == str(watchmode_id):
            sheet_row_number = i + 1
            target_range = f"Sheet1!G{sheet_row_number}:H{sheet_row_number}"
            service = get_service()
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=target_range,
                valueInputOption="USER_ENTERED",
                body={"values": [[str(season_count), checked_date]]}
            ).execute()
            return "updated"
    return "not_found"


def get_season_baseline(watchmode_id):
    """Return the stored season count for a show, or None if never checked.
    Season count is column G = index 6."""
    rows = get_all_shows()
    for i, row in enumerate(rows):
        if i == 0:
            continue
        if len(row) > 4 and str(row[4]) == str(watchmode_id):
            if len(row) > 6 and str(row[6]).strip() != "":
                try:
                    return int(row[6])
                except ValueError:
                    return None
            return None
    return None