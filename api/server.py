from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import workflows, execute, viz


def create_app(orchestrator) -> FastAPI:
    from api.dependencies import init_orchestrator
    init_orchestrator(orchestrator)

    app = FastAPI(title="OptiMoldIQ API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite dev server
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(workflows.router)
    app.include_router(execute.router)
    app.include_router(viz.router)

    # Serve React build in production
    dist = Path("control_panel_dist")
    if dist.exists():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

    return app