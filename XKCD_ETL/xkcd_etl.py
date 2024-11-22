import requests
import pandas as pd
import os
import json
import pymongo
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
XKCD_URL = "https://xkcd.com/{}/info.0.json"
BASE_URL = "https://xkcd.com/"
ENDPOINT = "/info.0.json"
START_COMIC = 1
END_COMIC = 10
RAW_DATA_DIR = "raw_data"
ENHANCED_DATA_FILE = "enhanced_data.json"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = "xkcdDB"
COLLECTION_NAME = "comics"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_xkcd_comic(comic_id):
    try:
        response = requests.get(XKCD_URL.format(comic_id))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching comic {comic_id}: {e}")
        return None

def fetch_and_store_comics(start, end):
    comics = []
    for comic_id in range(start, end + 1):
        comic_data = fetch_xkcd_comic(comic_id)
        if comic_data:
            comics.append({
                'id': comic_data['num'],
                'title': comic_data['title'],
                'image_url': comic_data['img'],
                'alt_text': comic_data['alt']
            })
    return pd.DataFrame(comics)

def save_to_csv(df, file_path):
    df.to_csv(file_path, index=False)
    logging.info(f"Data saved to {file_path}")

def fetch_xkcd_data(start, end):
    comics = []
    for comic_id in range(start, end + 1):
        data = fetch_xkcd_comic(comic_id)
        if data:
            comics.append(data)
    return comics

def save_raw_data(data, year):
    raw_data_dir = f"{RAW_DATA_DIR}/{year}"
    os.makedirs(raw_data_dir, exist_ok=True)
    raw_file_path = os.path.join(raw_data_dir, "xkcd_data.json")
    with open(raw_file_path, "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Raw data saved successfully at {raw_file_path}")

def extract_keywords(entry):
    text = f"{entry['title']} {entry['alt_text']} {entry['transcript']}".lower()
    keywords = list(set(text.split()))
    entry["keywords"] = keywords
    return entry

def enhance_data(input_file, output_file):
    with open(input_file, 'r') as infile:
        data = json.load(infile)
    for comic in data:
        comic['keywords'] = [keyword.lower() for keyword in comic.get('keywords', [])]
        comic['year'] = int(comic['year'])
    with open(output_file, 'w') as outfile:
        json.dump(data, outfile, indent=4)
    logging.info(f"Enhanced data saved to {output_file}")

def transfer_to_mongodb(json_file_path):
    client = pymongo.MongoClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    result = collection.insert_many(data)
    logging.info(f"Inserted {len(result.inserted_ids)} documents into the '{COLLECTION_NAME}' collection.")

def main():
    start_comic = START_COMIC
    end_comic = END_COMIC
    comics_df = fetch_and_store_comics(start_comic, end_comic)
    save_to_csv(comics_df, 'xkcd_comics.csv')
    raw_data = fetch_xkcd_data(start_comic, end_comic)
    save_raw_data(raw_data, 2024)
    enhanced_data = [extract_keywords(entry) for entry in raw_data]
    with open(ENHANCED_DATA_FILE, "w") as file:
        json.dump(enhanced_data, file, indent=4)
    enhance_data(ENHANCED_DATA_FILE, ENHANCED_DATA_FILE)
    transfer_to_mongodb(ENHANCED_DATA_FILE)

if __name__ == '__main__':
    main()