# Stream Tracker — Backlog & Ideas

A running list of potential features, improvements, and known edge cases for future work.
Nothing here is committed work — it's a place to capture ideas with enough context that
a future session (with or without an AI assistant) can pick them up informed.

Ordered roughly by value, not by effort.

---

## Features

### Local-storage option (highest value for sharing)
Add the ability to store data in a local `.csv` file instead of Google Sheets, selectable
via a setting. Removes the need for the entire Google Cloud / OAuth setup, which is the
single biggest barrier to other people trying the app. Tradeoff: a local file is only
accessible from the computer running the app, not other devices. Design-sensitive — needs
a clean switch between "Sheets" and "local" storage modes, primarily in `sheets.py` and
wherever the app reads/writes data. Once built, update the README to document both paths.

### Genre tracking + filtering
Watchmode already returns genre data (`genre_names` in the title details response), so the
data is available. Add a genre column to the sheet, populate it when a show is added, and
extend the existing My List filter bar (which already filters by status) to also filter or
sort by genre. Mostly additive — reuses the current filtering mechanism.

### New-content lifecycle management
When a per-show check finds a new season, do NOT overwrite the show's status. Instead set a
separate persistent "new content available" flag (a new sheet column), shown on the My List
card as a "🆕 New season" marker. Add a "Mark as caught up" button that clears the flag and
advances the stored season baseline to the current count. On My List, allow sorting/filtering
by "has new content" to act as a backlog view.

Rationale: status (Watching / Want to Watch / Watched) describes your overall relationship to
a show; "is there new stuff to catch up on" is a separate dimension. Folding them into one
field causes status to get overwritten in ways that confuse (e.g. a show you're actively
"Watching" shouldn't flip to "Want to Watch" just because a season was announced).

Decision status: leaning toward this flag-based approach over the simpler alternative of
auto-setting status to "Want to Watch." Confirm after living with the current new-season
feature for a couple of weeks — real usage will reveal which model fits.

### Leaving-soon detection
Companion to new-season detection: flag shows about to leave the user's services. Caveat:
Watchmode's expiration data is inconsistent across titles, so this would be best-effort —
useful when the data exists, silent when it doesn't. Set expectations accordingly.

---

## Known edge cases / polish

### Messy network string on expanded results
In expand-search mode, a result's network can be a string like "Netflix, Hulu (not
subscribed)". If a show is added to the list from an expanded result, that whole string gets
saved as the network. Not wrong, but messy. Consider cleaning it before saving, or disabling
"Add to List" on not-subscribed expanded results.

### Movies show "0 seasons"
The new-season check counts seasons, so running it on a Movie shows "0 season(s)". Harmless,
since you'd rarely check a movie, but slightly odd. Could hide the refresh button on Movies.

### Port 5000 conflicts (minor)
If another program is already using port 5000, Flask won't start ("address already in use").
Rare, so left out of the README troubleshooting section. Could document or make the port
configurable if it ever comes up.

---

## Done (for reference)
- Search with relevance ranking + service filtering
- Add / view / edit status / remove (full CRUD) backed by Google Sheets via OAuth
- Duplicate prevention keyed on Watchmode ID
- Persistent settings storage (local JSON file)
- Custom confirmation modal (replaced the browser popup)
- Expand-search when nothing is on the user's services
- Where-to-buy/rent lookup page (informational, no purchase links)
- Per-show new-season detection with persistent baseline tracking
- Published to GitHub with README and GPL v3 license
