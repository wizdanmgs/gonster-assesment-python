import logging
import subprocess
import sys
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run Alembic migrations using a subprocess to avoid event loop conflicts.
    """
    logger.info("Checking for database migrations...")
    
    # Ensure ALEMBIC_CONFIG is set or just use the local alembic.ini
    env = os.environ.copy()
    env["PYTHONPATH"] = f".:{env.get('PYTHONPATH', '')}"
    
    try:
        # Run 'alembic upgrade head' as a subprocess
        # We use sys.executable -m alembic to ensure we use the same environment
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout:
            for line in result.stdout.splitlines():
                if "Running upgrade" in line:
                    logger.info(f"Migration: {line}")
        
        logger.info("Database migration check completed.")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed with exit code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        # In production, you might want to exit if migrations fail
        # sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error running migrations: {e}")
