# 🚀 NEXUS AI: Deployment Guide

Current Issue: **Vercel** serverless functions generally do not support persistent SQLite databases or long-running Streamlit websocket connections well, leading to "Server Error" or data reset issues.

**Solution**: Deploy the Frontend to **Streamlit Community Cloud** (native support) and the Backend to **Render** (supports persistent backend processes).

---

## Part 1: Deploy Backend to Render (Free)

1.  **Sign Up/Login**: [render.com](https://render.com)
2.  **New Web Service**: Click "New +" -> "Web Service".
3.  **Connect Repo**: Select your repo `Mahaboob26/NEXUS-TRUSAI`.
4.  **Configure Settings**:
    *   **Root Directory**: `trus-ai-mvp/backend` (Critical setting!)
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
    *   **Instance Type**: Free
5.  **Environment Variables**:
    *   Add `PYTHON_VERSION` = `3.9.0` (optional but recommended)
6.  **Deploy**: Click "Create Web Service".
7.  **Get URL**: Once live, copy the URL (e.g., `https://nexus-backend-xyz.onrender.com`).

> **Note**: On the free tier, the backend will "sleep" after 15 mins of inactivity. It will take 50s to wake up on the first request.

---

## Part 2: Deploy Frontend to Streamlit Cloud (Free)

1.  **Sign Up/Login**: [share.streamlit.io](https://share.streamlit.io)
2.  **New App**: Click "New App".
3.  **Connect Repo**: Select `Mahaboob26/NEXUS-TRUSAI`.
4.  **Configure Settings**:
    *   **Main file path**: `trus-ai-mvp/frontend/streamlit_app.py`
5.  **Advanced Settings** (Crucial Step):
    *   Click "Advanced Settings" -> "Secrets" (or Environment Variables).
    *   Add the following variable:
        ```env
        BACKEND_URL="https://nexus-backend-xyz.onrender.com"
        ```
        *(Replace with your actual Render Backend URL from Part 1)*
6.  **Deploy**: Click "Deploy!".

---

## Part 3: Why Not Vercel?

*   **SQLite**: Your database (`audit.db`) is a *file*. On Vercel, the filesystem is ephemeral (read-only or resets). If you deploy to Vercel, every time the app restarts, your user data and audit logs are deleted.
*   **Streamlit**: Streamlit relies on WebSockets for its interactive UI. Vercel's serverless functions have a 10-second timeout by default and don't maintain the persistent connection Streamlit needs.

**Recommendation**: Stick to the **Streamlit Cloud + Render** combo for the most stable Hackathon demo.
