from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import json

# Add root path to import fetch_usgs_data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from fetch_usgs_data import fetch_earthquake_data, insert_earthquake_data
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

default_args = {
    "owner": "airflow",
    'start_date': datetime(2023, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="usgs_earthquake_etl",
    default_args=default_args,
    description="ETL pipeline: fetch earthquake data and insert into Postgres",
    schedule_interval="@daily",
    catchup=False,
    tags=["earthquake", "usgs", "postgres"],
) as dag:

    def extract_data(**context):
        """
        Fetch earthquake data and push it to XCom.
        """
        data = fetch_earthquake_data(**context)
        # Store as JSON string (XCom only handles small, serializable data)
        # Warning: XCom has size limits (~48KB). Large payloads can fail silently.
        context['ti'].xcom_push(key='earthquake_data', value=json.dumps(data))

    def load_data(**context):
        """
        Pull earthquake data from XCom and insert into Postgres.
        """
        json_data = context['ti'].xcom_pull(task_ids='extract_earthquake_data', key='earthquake_data')
        data = json.loads(json_data)

        try:
            with psycopg2.connect(
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASS"),
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT")
            ) as conn:
                with conn.cursor() as cursor:
                    insert_earthquake_data(data, cursor)
                conn.commit()
        except Exception as e:
            raise RuntimeError(f"Failed to load earthquake data: {e}")

    extract_task = PythonOperator(
        task_id="extract_earthquake_data",
        python_callable=extract_data,
    )

    load_task = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_data,
    )

    extract_task >> load_task
