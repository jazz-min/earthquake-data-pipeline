import requests
import psycopg2
from psycopg2.extras import Json
from datetime import datetime, timedelta
from typing import Dict
from dotenv import load_dotenv
import os
import logging
import argparse

# Load environment variables from .env
load_dotenv()

# --- DB config ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_earthquake_data(**context):
    """
    Fetch earthquake data from USGS Earthquake API with configurable date range and magnitude
    Returns:
        dict: Parsed JSON response (GeoJSON format).
    """
    dag_conf = context.get("dag_run").conf or {}

    start_date = dag_conf.get("start_date")
    end_date = dag_conf.get("end_date")
    min_magnitude = float(dag_conf.get("min_magnitude", 4.5))
    # Use default if no dates are passed
    if not start_date or not end_date:
        end = datetime.utcnow()
        start = end - timedelta(days=7)
        start_date = start.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_date,
        "endtime": end_date,
        "minmagnitude": min_magnitude
    }

    logger.info(f"Fetching earthquake data from {start_date} to {end_date}...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    logger.info(f"Successfully fetched data.")
    return response.json()


def insert_earthquake_data(data: Dict, cursor) -> None:
    """
    Insert parsed earthquake records into Postgres.
    Args:
        data (dict): USGS API data.
        cursor: Active psycopg2 cursor.
    """
    logger.info("Ensuring raw_earthquakes table exists...")
    # Create schema if it doesn't exist
    cursor.execute("CREATE SCHEMA IF NOT EXISTS raw_data")
    # Create table inside the raw_data schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_data.raw_earthquakes (
            id TEXT PRIMARY KEY,
            time TIMESTAMP,
            place TEXT,
            magnitude FLOAT,
            longitude FLOAT,
            latitude FLOAT,
            depth_km FLOAT,
            url TEXT,
            raw_json JSONB,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    insert_query = """
        INSERT INTO raw_data.raw_earthquakes (
            id, time, place, magnitude, longitude, latitude, depth_km, url, raw_json
        )
        VALUES (
            %s, to_timestamp(%s / 1000), %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (id) DO NOTHING
    """

    logger.info("Inserting earthquake records into Postgres...")
    count = 0
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coordinates = geom.get("coordinates", [None, None, None])
        quake_id = feature.get("id", None)

        values = (
            quake_id,
            props.get("time"),
            props.get("place"),
            props.get("mag"),
            coordinates[0],  # longitude
            coordinates[1],  # latitude
            coordinates[2],  # depth
            props.get("url"),
            Json(feature)
        )

        cursor.execute(insert_query, values)
        count += 1

    logger.info(f"{count} records processed and inserted (or skipped if already present).")


def main():
    # --- CLI args ---
    parser = argparse.ArgumentParser(description="Fetch and store earthquake data from USGS API.")
    parser.add_argument("--days-back", type=int, default=7, help="Number of past days to fetch data for.")
    parser.add_argument("--min-magnitude", type=float, default=4.5, help="Minimum earthquake magnitude to include.")
    args = parser.parse_args()

    try:
        logger.info("Connecting to Postgres database...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Fetch and insert
        earthquake_data = fetch_earthquake_data(days_back=args.days_back, min_magnitude=args.min_magnitude)
        insert_earthquake_data(earthquake_data, cursor)

        conn.commit()
        logger.info("✅ Data committed to the database.")
    except Exception as e:
        logger.exception("An error occurred while processing earthquake data.")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    main()
