from functools import lru_cache
from pathlib import Path
import os


class Settings:
    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parent.parent
        self.app_name = 'EFQ PROJECT DASHBOARD'
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.secret_key = os.getenv('SECRET_KEY', 'efq-prototype-secret-change-me')
        self.cookie_name = 'efq_session'
        self.session_max_age_seconds = 60 * 60 * 8
        cors_origin = os.getenv('CORS_ORIGIN', 'http://localhost:8000')
        self.cors_origins = [origin.strip() for origin in cors_origin.split(',') if origin.strip()]
        self.data_file = Path(os.getenv('EFQ_DATA_FILE', self.base_dir / 'data' / 'EFQ_Dashboard.xlsx'))
        self.frontend_dir = self.base_dir / 'frontend'
        self.assets_dir = self.frontend_dir / 'assets'
        self.allow_cookie_secure = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
