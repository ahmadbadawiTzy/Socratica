"""
Socratica Backend — Application entry point.
"""

from app.core.logging import setup_logging
from app.main import create_app

setup_logging()
app = create_app()
