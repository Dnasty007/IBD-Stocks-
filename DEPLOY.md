# Deploying the IBD Stock Watcher (works on your phone, permanently)

The app runs fine locally (Cursor / `streamlit run app.py`), but to view it on
your **phone from anywhere** it needs to be deployed to a real host. Tunnels
(ngrok/localtunnel/cloudflared) do **not** work from sandboxed cloud
containers because their network policy blocks the outbound ports tunnels need.

The free, permanent fix is **Streamlit Community Cloud**.

## One-time deploy (~3 minutes)

1. Go to **https://share.streamlit.io**
2. Sign in with your **GitHub** account (`Dnasty007`)
3. Click **Create app** → **Deploy a public app from GitHub**
4. Fill in:
   - **Repository:** `Dnasty007/IBD-Stocks-`
   - **Branch:** `claude/add-stocks-to-app-i9w0he` (or `main` after merging)
   - **Main file path:** `app.py`
5. Click **Deploy**

You'll get a permanent URL like `https://ibd-stocks.streamlit.app` that works on
any device — phone, tablet, PC — without keeping anything running.

## After deploy

- Every push to the chosen branch auto-redeploys the app.
- To add stocks, edit `stock_watcher/config.py` (`DEFAULT_STOCKS`), commit, push.

## Run locally (Cursor / PC)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.
