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


## Deploy on Render (free)

1. Push this project to GitHub.
2. In Render, choose **New → Blueprint**, connect the repository, and select `render.yaml`.
3. Set the prompted `ADMIN_PASSWORD` secret, then deploy the Free web service.

This setup uses Render's Free plan and does not attach a persistent disk or require paid resources. Free web services have an ephemeral filesystem: the SQLite database and uploaded photos can be erased whenever the service spins down, restarts, or redeploys. Free services can also take about a minute to wake after 15 minutes without traffic. This setup is suitable for a demo; use persistent external storage if reports must be retained.

The map loads Leaflet and OpenStreetMap tiles from external services, so browsers need internet access for map tiles.
## Project structure

- `app.py` — Flask routes, validation, SQLite storage, admin session
- `templates/` — public reporting experience and admin console
- `static/` — responsive styles, map interactions, uploaded photos

