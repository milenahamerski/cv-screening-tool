"""Run script for CV Optimizer application."""

import uvicorn

if __name__ == "__main__":
    print("Iniciando CV Optimizer em http://localhost:8000...")
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
