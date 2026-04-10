#!/usr/bin/env python
"""Database initialization script"""
import logging
from app.config import settings
from app.services.database_service import DatabaseService
from app.utils.logger import get_logger

logger = get_logger(__name__)

def init_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    
    try:
        DatabaseService.initialize()
        logger.info("Database initialized successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_database()
