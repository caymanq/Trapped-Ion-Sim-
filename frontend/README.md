# Ion Trap Web Frontend

Next.js app intended for Vercel hosting. It calls the Python compute API through `NEXT_PUBLIC_ION_TRAP_API_URL`.

## Deploy on Vercel (why the site might look “unchanged”)

Your Git repo is a **monorepo**: the Next app lives in **`frontend/`**, not at the repo root.

1. In the Vercel project: **Settings → Build & Deployment → Root Directory** must be **`frontend`**.  
   If this is left as `.`, Vercel will not reliably build this app (wrong directory or framework detection).
2. After connecting **GitHub `caymanq/Trapped-Ion-Sim-`**, open the latest deployment **Build** log and confirm it used the commits you pushed. If deployments never run, Git is not wired to this project.
3. Hard-refresh production (`Ctrl+Shift+R`): browsers can serve cached HTML aggressively.
4. On each production build, Vercel sets `VERCEL_GIT_COMMIT_SHA`. The UI shows **`deploy #######`** in the bottom-right; that short SHA should match the commit on GitHub.

## Run Locally

```bash
cd frontend
npm install
npm run dev
```

Set the API URL when the backend is not running on `http://localhost:8000`:

```bash
NEXT_PUBLIC_ION_TRAP_API_URL=https://your-python-api.example.com
```
