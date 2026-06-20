# 🎬 Stream Tracker

A personal web app for tracking your favorite shows and movies across streaming services. Search a catalog powered by [Watchmode](https://www.watchmode.com/), save what you're watching to your own Google Sheet, and check whether your shows have new seasons available — solving the problem of new seasons getting buried by streaming-service algorithms after a long gap.

This is a personal project that runs locally on your own computer. It is not a hosted service — each person runs their own copy with their own data.

---

## What it does

- **Search** for shows and movies, with results ranked by relevance and filtered to the streaming services you actually subscribe to.
- **Save** shows to your personal Google Sheet with a status of *Watching*, *Want to Watch*, or *Watched*, with automatic duplicate prevention.
- **Manage** your list from a dedicated page — change a show's status or remove it.
- **Check for new seasons** on demand, per show, so you find out when something you track has a new season available.
- **Expand a search** to all services when nothing is found on yours, and look up rent/buy options for titles that aren't on any subscription.

---

## ⚠️ Before you start: a note on credentials

This app uses several private credential files: a Watchmode API key, Google OAuth credentials, and a saved Google login token. **These must never be shared publicly or committed to a public repository.** This project's `.gitignore` is already configured to exclude them (`.env`, `credentials.json`, `token.json`, `settings.json`). Do not remove those lines, and always verify with `git status` that none of those files appear before pushing changes anywhere public. A secret pushed even once to a public repo should be considered compromised.

---

## Requirements

- A computer running Windows, macOS, or Linux
- [Python 3.10 or newer](https://www.python.org/downloads/)
- A free [Watchmode API account](https://api.watchmode.com/)
- A Google account with a Google Sheet to store your data
- About 30–45 minutes for first-time setup (the Google authorization is the slow part)

---

## Setup

### 1. Install Python

Download Python from [python.org/downloads](https://www.python.org/downloads/) and run the installer.

**Important (Windows):** On the very first installer screen, check the box that says **"Add Python to PATH"** before clicking Install. This is easy to miss and causes problems if skipped.

Confirm it worked by opening a terminal and running:

```
python --version
```

You should see a version number like `Python 3.13.0`.

### 2. Get the project files

Download or clone this repository to a folder on your computer. If you have Git installed:

```
git clone https://github.com/DrNOexplore/Stream-Tracker.git
cd Stream-Tracker
```

Otherwise, use the green **Code** button on the repository page to download a ZIP, then unzip it.

### 3. Install the required Python libraries

From inside the project folder, run:

```
pip install flask requests python-dotenv google-auth google-auth-oauthlib google-api-python-client
```

### 4. Get a Watchmode API key

1. Sign up for a free account at [api.watchmode.com](https://api.watchmode.com/).
2. Find your API key on your account dashboard.
3. In the project folder, create a file named exactly `.env` and put this single line in it, replacing the placeholder with your real key:

```
WATCHMODE_API_KEY=your_key_here
```

No quotes, no spaces around the `=`. Save the file.

> The free Watchmode tier allows 2,500 API calls per month, which is plenty for personal use. Each search uses several calls, and each new-season check uses one.

### 5. Set up Google Sheets access

This is the most involved step, because Google requires authorization for an app to read and write your sheet. Take it slowly.

**5a. Create your data sheet**

1. Create a new Google Sheet in your Google account.
2. In the first row, add these six column headers, one per cell starting at A1:

   `Title` · `Type` · `Network` · `Status` · `Watchmode_ID` · `Year`

3. Add two more headers for new-season tracking: `Last_Known_Seasons` in **G1** and `Last_Checked` in **H1**.
4. Note the sheet's ID — it's the long string in the URL between `/d/` and `/edit`.

**5b. Create a Google Cloud project**

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in with the account that owns your sheet.
2. Create a new project (name it anything, e.g. `stream-tracker`).
3. Enable the **Google Sheets API**: go to the API Library, search for "Google Sheets API," and click **Enable**.

> Google may prompt you to set up a billing account. The Google Sheets API is free at personal-use levels and you will not be charged for normal use, but Google sometimes requires a billing account on file regardless. If you are not comfortable with that, see the alternative storage note at the bottom of this README.

**5c. Configure the OAuth consent screen**

1. In the Cloud console, go to the **OAuth consent screen** / **Google Auth Platform** section and start the configuration.
2. Choose **External** as the user type.
3. Fill in the app name (e.g. `Stream Tracker`), your support email, and your developer contact email. Other fields can be left blank.
4. **Add yourself as a Test User.** This step is essential — find the **Test users** section and add the Google address you'll sign in with. If you skip this, you'll get an "Access blocked" error later.

**5d. Create OAuth credentials**

1. Go to **Credentials** and create an **OAuth client ID**.
2. Choose **Desktop app** as the application type.
3. When the credentials are created, **download the JSON immediately** — Google only shows the client secret once, at creation time.
4. Move that file into the project folder and rename it exactly `credentials.json`.

**5e. Connect the code to your sheet**

Open `sheets.py` and put your sheet ID (from step 5a) into the `SHEET_ID` line near the top, between the quotes.

### 6. Run the app

From inside the project folder:

```
python app.py
```

Then open a browser and go to:

```
http://127.0.0.1:5000
```

**The first time you do something that touches your sheet** (like adding a show), a browser window will open asking you to authorize the app. You will see a **"Google hasn't verified this app"** warning — this is expected, because the app is in personal testing mode. Click **Advanced**, then **Go to (your app name) (unsafe)**, then allow access. This is your own app accessing your own sheet. After you approve once, a `token.json` file is saved and you won't be asked again.

---

## Using the app

- **Search** for a show or movie, choose a status, and click **Add to List**.
- Open **My List** to view, filter by status, change a status, or remove a show.
- On My List, click **⟳ Check** on any show to look up whether it has new seasons. The first check records a baseline; later checks tell you if a new season has appeared since.
- If a search finds nothing on your services, use **Search all services anyway**, and follow the **Where to buy/rent** link for purchase options.
- Manage which streaming services you subscribe to under **Settings**.

---

## Troubleshooting

- **`python` or `pip` not recognized:** Python isn't on your PATH. Reinstall and check "Add Python to PATH," then restart your terminal.
- **Changes don't seem to take effect:** Make sure you saved the file (look for the unsaved-changes dot on the editor tab) and that you fully stopped and restarted the app.
- **"Access blocked" during Google sign-in:** You haven't added yourself as a Test User on the OAuth consent screen (step 5c).
- **An empty or "no results" response when you expect results:** Confirm your `.env` has the correct Watchmode key and that your selected services in Settings actually carry the title.

---

## A note on storage: Google Sheets vs. a local file

By design, this app stores your data in a Google Sheet, which is why the Google authorization above is required. The benefit is that your list is accessible from anywhere and easy to edit by hand.

It is possible to **bypass Google entirely and store your data in a local `.csv` file** on your own computer instead. That would remove the need for the Google Cloud project, the OAuth setup, and the credential files — a much simpler setup. However, **this option is not built into the app as written.** It would require modifying the code (primarily `sheets.py` and how the app reads and writes data) to use a local file instead of the Sheets API.

If you'd like to go that route, it's a very achievable modification, and an AI coding assistant such as [Claude](https://claude.ai) (or a similar service) can walk you through making the change. The main tradeoff is that a local file can only be accessed from the computer the app runs on, not from other devices.

---

## Credits

Streaming availability data powered by [Watchmode.com](https://www.watchmode.com/).

This is a personal, non-commercial project built for learning and individual use.
