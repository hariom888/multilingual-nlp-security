# Deploy: Vercel frontend + Render Python API

This repository contains the original Streamlit project (kept intact), a FastAPI wrapper around its existing guardrail model, and a small Next.js demo frontend.

## 1. Push this project to GitHub
1. Extract the ZIP.
2. Create a new GitHub repository.
3. Upload the *contents* of this folder so `render.yaml`, `backend/`, `frontend/`, `guardrails/`, and `models/` are at the repository root.
4. Commit the files. Do not upload `.env` or API keys.

## 2. Deploy the backend on Render
1. Open https://render.com and sign in with GitHub.
2. Choose **New +** -> **Blueprint**.
3. Select the GitHub repository containing this project.
4. Render detects `render.yaml`. Review and apply.
5. Wait for the service to become Live.
6. Copy its URL, e.g. `https://multilingual-nlp-security-api.onrender.com`.
7. Open `https://YOUR-RENDER-URL/health`. It should return JSON with `"status":"ok"` and `"model_loaded":true`.

The backend uses `backend/requirements.txt` and starts with `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

## 3. Deploy the frontend on Vercel
1. Open https://vercel.com and sign in with GitHub.
2. Click **Add New** -> **Project**, then import the same repository.
3. In project configuration set **Root Directory** to `frontend` (choose it in the directory picker).
4. Framework preset: **Next.js**. Build command and output directory can stay at defaults.
5. Under **Environment Variables**, add:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: your Render service URL, without a trailing slash (for example `https://multilingual-nlp-security-api.onrender.com`)
6. Click **Deploy**.
7. Open the Vercel URL. Load the attack sample and click **RUN SECURITY CHECK** with Protected selected.

## 4. Demo
- **Baseline** deliberately shows the supplied content passing through without guardrail inspection. This endpoint does not execute tools or external actions.
- **Protected** runs the project's existing document sanitizer and trained classifier/rule checks. The result shows the decision, score when available, quarantine count, and retained text.
- Try the benign sample too.

## Notes
- Render free services may sleep after inactivity. Open the Render `/health` endpoint a few minutes before the presentation to wake it up.
- The frontend reports a connection error if `NEXT_PUBLIC_API_URL` is missing or wrong.
- This is a demonstration integration, not a claim of production security. The project's own documented limitations still apply.
- The original Streamlit app and its files remain in the repository and can still be run separately.
