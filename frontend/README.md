# Ion Trap Web Frontend

Next.js app intended for Vercel hosting. It calls the Python compute API through `NEXT_PUBLIC_ION_TRAP_API_URL`.

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
