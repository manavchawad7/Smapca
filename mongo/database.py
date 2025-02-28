import pymongo

class Database:
    def __init__(self, db_name, collection_name):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def find_one(self, query):
        return self.collection.find_one(query)