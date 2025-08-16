from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb+srv://harshop732:8Iki4hwm3WQ8P7m5@cluster0.jwv48iz.mongodb.net/")
    db = client["pizza_app"]
    return db
