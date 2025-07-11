from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
with DAG(
    dag_id='run_dbt_with_bash',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Run dbt transformations using BashOperator',
    doc_md="""
        ### DAG: Run dbt with BashOperator
    
        This DAG runs dbt transformations and tests using BashOperator.
    
        **Steps:**
        - `dbt run`: Applies model transformations
        - `dbt test`: Runs data quality tests
        - `dbt docs generate`: Builds updated docs
        """,
) as dag:

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command="""
            set -a
            source /opt/airflow/.env
            set +a
            cd /usr/app/earthquake_dbt && dbt run
        """,
        env={
            'PATH': '/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin',
            'DBT_PROFILES_DIR': '/usr/app',
        }
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command="""
            set -a
            source /opt/airflow/.env
            set +a
            cd /usr/app/earthquake_dbt && dbt test
        """,
        env={
            'PATH': '/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin',
            'DBT_PROFILES_DIR': '/usr/app',
        }
    )

    dbt_docs_generate = BashOperator(
        task_id='dbt_docs_generate',
        bash_command="""
            set -a
            source /opt/airflow/.env
            set +a
            cd /usr/app/earthquake_dbt && dbt docs generate
        """,
        env={
            'PATH': '/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin',
            'DBT_PROFILES_DIR': '/usr/app',
        }
    )

    dbt_run >> dbt_test >> dbt_docs_generate
