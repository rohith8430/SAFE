# SafeSpot — Community Safety Mapping

A Flask and SQLite community safety reporting app built from the project brief. Residents can submit location-based hazard reports, optionally attach a photo, explore reports on an OpenStreetMap map, search and filter by category/status, and follow status updates. Administrators can review reports and record progress notes.

## Run locally

1. Install Python 3.10+.
2. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Configure an admin password and a private Flask signing key, then start the server:

   ```powershell
   $env:ADMIN_PASSWORD = "choose-a-password"
   $env:FLASK_SECRET_KEY = "replace-with-a-long-random-secret"
   python app.py
   ```

4. Open http://127.0.0.1:5000. The first start creates `safespot.db` automatically. Admin sign-in is at the bottom of the home page.

The map tiles and Leaflet library load from OpenStreetMap and unpkg, so those external services need to be reachable in the browser. Uploaded report images are limited to PNG/JPG/JPEG/WEBP and 5 MB. `safespot.db` and uploaded images are runtime data and are intentionally not included in version control.


## Deploy on Render

1. Push this project to a GitHub repository.
2. In Render, choose **New → Blueprint**, connect the repository, and select `render.yaml`.
3. Set the prompted `ADMIN_PASSWORD` secret in Render, then deploy.

The Blueprint creates a persistent disk at `/var/data` for SQLite and uploaded photos. The disk uses the Render Starter service plan. Keep the disk attached to preserve report data and images between deploys. Leaflet and map tiles are served by external providers, so users need internet access for the map.
## Project structure

- `app.py` — Flask routes, validation, SQLite storage, admin session
- `templates/` — public reporting experience and admin console
- `static/` — responsive styles, map interactions, uploaded photos

