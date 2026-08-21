# Dynasty Draft Command Center — Streamlit Cloud

This folder is ready to upload to GitHub and deploy on Streamlit Community Cloud.

## Files
- `app.py` — the application
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — dark mode / cloud settings
- `.gitignore`

## Deploy

1. Create a GitHub repository.
2. Upload **all files and folders in this folder**, including `.streamlit`.
3. Go to Streamlit Community Cloud.
4. Click **Create app**.
5. Connect your GitHub account/repository.
6. Choose:
   - Branch: `main`
   - Main file path: `app.py`
7. Pick a custom app URL if offered.
8. Click **Deploy**.

Your app will then be available at an address similar to:

`https://your-app-name.streamlit.app`

## Updating later

When you replace `app.py` in GitHub with a newer version, Streamlit Cloud will redeploy automatically.

## Privacy note

If you do not want league mates finding the code, use a **private GitHub repository** and configure Streamlit access accordingly.
