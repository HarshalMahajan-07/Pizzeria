from pymongo import MongoClient

def get_db():
    client = MongoClient("your mongodb connection string")
    db = client["pizza_app"]
    return db
