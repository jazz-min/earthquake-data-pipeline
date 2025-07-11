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
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="usgs_earthquake_etl",
    default_args=default_args,
    description="ETL pipeline: fetch earthquake data and insert into Postgres",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["earthquake", "usgs", "postgres"],
) as dag:

    def extract_data(**context):
        """
        Fetch earthquake data and push it to XCom.
        """
        data = fetch_earthquake_data()
        # Store as JSON string (XCom only handles small, serializable data)
        context['ti'].xcom_push(key='earthquake_data', value=json.dumps(data))

    def load_data(**context):
        """
        Pull earthquake data from XCom and insert into Postgres.
        """
        json_data = context['ti'].xcom_pull(task_ids='extract_earthquake_data', key='earthquake_data')
        data = json.loads(json_data)

        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cursor = conn.cursor()

        insert_earthquake_data(data, cursor)

        conn.commit()
        cursor.close()
        conn.close()

    extract_task = PythonOperator(
        task_id="extract_earthquake_data",
        python_callable=extract_data,
        provide_context=True
    )

    load_task = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_data,
        provide_context=True
    )

    extract_task >> load_task
