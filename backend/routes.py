from . import app
import os
import json
from flask import jsonify, request, make_response, abort, url_for
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys
from pymongo.errors import ServerSelectionTimeoutError


SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

mongodb_service = "mongodb/brew/mongodb-community"
mongodb_username = "almuhidat"
mongodb_password = "almuhidat"
mongodb_port = 27017

if mongodb_service == None:
  app.logger.error("Missing MongoDB server in the MONGODB_SERVICE variable")
  sys.exit(1)

if mongodb_username and mongodb_password:
  url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
  url = f"mongodb://{mongodb_service}"

print(f"connecting to url: {url}")

try:
    client = MongoClient(url, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # Check if MongoDB is accessible
    print("MongoDB connected successfully!")
except ServerSelectionTimeoutError as e:
    print(f"MongoDB connection failed: {e}")
    sys.exit(1)

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
  return json.loads(json_util.dumps(data))

@app.route("/health")
def health():
  return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
  """return length of data"""
  count = db.songs.count_documents({})

  return {"count": count}, 200

@app.route("/song", methods=["GET"])
def songs():
  """
  Get all songs in the list
  """
  documents = list(db.songs.find({}))
  print(documents[0])

  return {"songs": parse_json(documents)}, 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
  """
  Get a song by id
  """
  song = db.songs.find_one({"id": id})
  if not song:
    return {"message": f"song with id {id} not found"}, 404

  return parse_json(song), 200

@app.route("/song", methods=["POST"])
def create_song():
  """
  Create a new song
  """
  new_song = request.json

  song = db.songs.find_one({"id": new_song["id"]})

  if song:
    return {"Message": f"song with id {song['id']} already present"}, 302

  insert_id: InsertOneResult = db.songs.insert_one(new_song)

  return {"inserted id": parse_json(insert_id.inserted_id)}, 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
  song_in = request.json

  song = db.songs.find_one({"id": id})

  if song == None:
    return {"message": "song not found"}, 404

  updated_data = {"$set": song_in}

  result = db.songs.update_one({"id": id}, updated_data)

  if result.modified_count == 0:
    return {"message": "song found, but nothing updated"}, 200
  else:
    return parse_json(db.songs.find_one({"id": id})), 201

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
  result = db.songs.delete_one({"id": id})
  if result.deleted_count == 0:
    return {"message": "song not found"}, 404
  else:
    return "", 204