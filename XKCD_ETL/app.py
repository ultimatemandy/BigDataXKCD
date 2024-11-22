from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://mongodb:27017")
db = client["xkcd_database"]
collection = db["comics"]

@app.route("/", methods=["GET"])
def index():
    # Test MongoDB connection
    try:
        client.admin.command('ismaster')  # Check if the connection is successful
        print("MongoDB connection successful.")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
    
    query = request.args.get('query', '')  # Get the search query from the request parameters
    results = []

    if query:
        print(f"Query being sent to MongoDB: {{ '$or': [ {{'title': {{'$regex': '{query}', '$options': 'i'}}}}, {{'alt_text': {{'$regex': '{query}', '$options': 'i'}}}} ] }}")
        # Perform case-insensitive search
        results = list(collection.find({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"alt_text": {"$regex": query, "$options": "i"}}
            ]
        }))
    
    print(f"Search results: {results}")
    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)