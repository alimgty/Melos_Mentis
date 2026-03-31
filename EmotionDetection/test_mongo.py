# test_mongo.py
from pymongo import MongoClient
from pprint import pprint

URI = "mongodb+srv://divyanshu:divyanshu123@cluster0.rdc0nfb.mongodb.net/?appName=Cluster0"

client = MongoClient(URI, serverSelectionTimeoutMS=5000)  # 5s timeout
try:
    # force connection check
    info = client.server_info()
    print("Connected to MongoDB Atlas. Server info snippet:")
    print(info.get("version"))

    # choose DB and collection explicitly
    db = client['test_db']                    # choose a DB name you want to use
    coll = db['test_collection']

    doc = {"test": "ok", "value": 123}
    res = coll.insert_one(doc)
    print("Inserted id:", res.inserted_id)

    # fetch back
    found = coll.find_one({"_id": res.inserted_id})
    pprint(found)

except Exception as e:
    print("Connection / insertion failed:")
    print(str(e))
finally:
    client.close()
