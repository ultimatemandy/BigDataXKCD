from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import requests
import pymongo
from pymongo import MongoClient

# Function to fetch data from the API
def fetch_comics_data():
    url = "https://xkcd.com/info.0.json"  # Replace with the actual API URL
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise ValueError("Failed to fetch data from API")

# Function to write data to MongoDB
def write_to_mongodb(data):
    client = MongoClient('localhost', 27017)  # Adjust if MongoDB is hosted elsewhere
    db = client['xkcd_database']
    collection = db['comics']
    collection.insert_one(data)  # Insert data as a new document

# Function to read from MongoDB
def read_from_mongodb():
    client = MongoClient('localhost', 27017)
    db = client['xkcd_database']
    collection = db['comics']
    comics = collection.find()
    for comic in comics:
        print(comic)

# DAG definition
dag = DAG(
    'xkcd_comics_etl',
    description='Fetches XKCD data, stores it in MongoDB, and then reads it back',
    schedule_interval=None,  # No scheduling, manual trigger only
    start_date=datetime(2024, 11, 21),  # Adjust to your start date
    catchup=False,  # Only run for the latest start date, no historical runs
)

# Task to fetch API data
fetch_comics_task = PythonOperator(
    task_id='fetch_comics_data',
    python_callable=fetch_comics_data,
    dag=dag,
)

# Task to write data to MongoDB
write_to_mongodb_task = PythonOperator(
    task_id='write_to_mongodb',
    python_callable=write_to_mongodb,
    op_args=['{{ task_instance.xcom_pull(task_ids="fetch_comics_data") }}'],  # Pull the data from fetch_comics_data
    dag=dag,
)

# Task to read from MongoDB
read_from_mongodb_task = PythonOperator(
    task_id='read_from_mongodb',
    python_callable=read_from_mongodb,
    dag=dag,
)

# Set task dependencies
fetch_comics_task >> write_to_mongodb_task >> read_from_mongodb_task