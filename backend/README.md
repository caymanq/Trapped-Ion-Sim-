# Ion Trap Compute API

FastAPI service that exposes the notebook-derived ion-trap solver logic for the Vercel frontend.

## Run Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Endpoints

- `GET /health`
- `GET /traps`
- `POST /simulate`
- `POST /validate`

The simulation response includes the RF potential grid, pseudopotential grid in micro electron-volts, trap depth in micro electron-volts, and physics validation status.
