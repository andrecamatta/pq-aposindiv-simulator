# Instruções do Projeto - Simulador Atuarial Individual

## Subir Backend e Frontend

### Backend
```bash
cd simulador-atuarial-individual/backend
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd simulador-atuarial-individual/frontend
npm run dev
```

### URLs
- Backend: http://localhost:8000
- Frontend: http://localhost:5173