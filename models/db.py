from pymongo import MongoClient

def get_db():
    client = MongoClient("here you database connection string")
    db = client["pizza_app"]
    return db
