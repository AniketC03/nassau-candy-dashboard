# Nassau Candy Distributor — Shipping Analytics Dashboard

A Streamlit web app for shipping route efficiency analysis.

## Files
- `app.py` — main dashboard
- `data.csv` — order dataset (10,194 rows)
- `requirements.txt` — Python dependencies

## Deploy on Streamlit Community Cloud (Free, ~3 minutes)

1. **Create a GitHub account** at https://github.com if you don't have one.

2. **Create a new repository** on GitHub:
   - Click the "+" icon → "New repository"
   - Name it: `nassau-candy-dashboard`
   - Set it to **Public**
   - Click "Create repository"

3. **Upload these files** to the repo:
   - Click "uploading an existing file"
   - Drag and drop `app.py`, `data.csv`, and `requirements.txt`
   - Click "Commit changes"

4. **Go to** https://share.streamlit.io
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repo: `nassau-candy-dashboard`
   - Branch: `main`
   - Main file path: `app.py`
   - Click "Deploy!"

5. **Wait ~60 seconds** — your app will be live at:
   `https://<your-username>-nassau-candy-dashboard-app-<hash>.streamlit.app`

That's it! The URL is shareable with anyone.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
