from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.auth import router as auth_router
from api.custodian import router as custodian_router
from api.incidents import router as incidents_router
from api.lookups import router as lookups_router
from api.management import router as management_router
from config import get_settings
from repositories.excel_repository import RepositoryContainer


PAGE_MAP = {
    '/': 'index.html',
    '/home': 'pages/home.html',
    '/signin': 'pages/signin.html',
    '/signup': 'pages/signup.html',
    '/incident-reporting': 'pages/incident-reporting.html',
    '/custodian-dashboard': 'pages/custodian-dashboard.html',
    '/management-dashboard': 'pages/management-dashboard.html',
}


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.repositories = RepositoryContainer.build(settings.data_file)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception):
        if request.url.path.startswith('/api/'):
            return JSONResponse(status_code=500, content={'detail': 'Something went wrong while processing your request. Please try again.'})
        raise exc

    app.include_router(auth_router)
    app.include_router(lookups_router)
    app.include_router(incidents_router)
    app.include_router(custodian_router)
    app.include_router(management_router)

    app.mount('/static', StaticFiles(directory=settings.frontend_dir), name='static')

    for route_path, relative_file in PAGE_MAP.items():
        app.add_api_route(route_path, _page_factory(settings.frontend_dir / relative_file), methods=['GET'], include_in_schema=False)

    @app.get('/health', include_in_schema=False)
    def health():
        return {'status': 'ok'}

    return app


def _page_factory(file_path: Path):
    async def serve_page():
        return FileResponse(file_path)

    return serve_page


app = create_app()
