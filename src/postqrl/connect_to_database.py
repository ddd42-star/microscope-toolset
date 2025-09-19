import psycopg2
from dotenv import load_dotenv
import os
import logging

# Load env variable from .env
load_dotenv()

# Database connection details
DB_HOST=os.getenv("DB_HOST")
DB_NAME=os.getenv("DB_NAME")
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_PASSWORD")
DB_PORT= int(os.getenv("DB_PORT"))

logger = logging.getLogger(__name__)
try:
    # Connect to the database
    connection = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    logger.info("Connection successful")

except Exception as e:
    logger.info("An error occurred during connection to the database: %s", e)

