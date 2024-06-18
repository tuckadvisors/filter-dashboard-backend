from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_cors import cross_origin
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import bcrypt
import os
from dotenv import load_dotenv
from FilterParser import FilterParser

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers="Content-Type", supports_credentials=True) 

# Setup for Mongo and pipeline filter parser
mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
collection_name = os.getenv("COLLECTION_NAME")
filter_parser = FilterParser(os.getenv("DRIVER_PATH"), os.getenv("EMAIL"), os.getenv("PASSWORD"))

# Setting up Mongo connection
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client[db_name]
collection = db[collection_name]

@app.route('/')
def home():
  return "API home"
'''
Validates password entered in on the dashboard
See README.md for password
'''
@app.route('/login', methods=['POST'])
@cross_origin()
def login():
  # get password from request and convert to bytes
  password = request.get_json().get('password').encode('utf-8')
  # get the password field from mongo
  pswd_field = collection.find_one({"password_store": "1"})
  # check password against encrypted password in db
  if bcrypt.checkpw(password.encode('utf-8'), pswd_field['login_password']):
    return jsonify({'response': 'Valid password'}), 200
  else:
    return jsonify({'response': 'Invalid password'}), 200

'''
Add one filter to the database
'''  
@app.route('/addFilter', methods=['POST'])
@cross_origin()
def add_filter():
  filter_link = request.get_json.get('link')
  filter_group = request.get_json.get('group')
  # for a new filter to be added, it has to be unique on url
  # if we can't find it in the db, scrape it
  if not collection.find({"group": filter_group, "link": filter_link}):
    document = filter_parser.scrape_filter_count({filter_link: filter_group})
    collection.insert_one(document)
    return jsonify({"response": "Successfully added filter to group"}), 200
  else:
    return jsonify({"response": "Name, link already exist as part of another group"}), 409
  
'''
Update all filters in the database
'''
@app.route('/updateAllFilters', methods=['POST'])
@cross_origin()
def update_allFilters():
  all_results = collection.find({})
  for result in all_results:
    # scrape the new information
    document = filter_parser.scrape_filter_count({result["link"]: result["group"]})
    # update counts for the existing entry
    update_operation = {"$set": {"count": document["count"]}}
    collection.update_one({"link": result["link"]}, update_operation)
    # check for any exceptions
    if collection.get({"status": result["status"]}) != 200:
      return jsonify({"response": result["status"]}), 409
  return jsonify({"response": "Successfully updated all filters"}), 200

'''
Delete one filter from the database
'''  
@app.route('/deleteFilter', methods=['POST'])
@cross_origin()
def delete_filter():
  filter_link = request.get_json.get('link')
  if collection.find({"link": filter_link}):
    collection.delete_one({"link": filter_link})
    return jsonify({"response": "Succesfully deleted filter"}), 200
  else:
    return jsonify({"response": "Unable to find link to delete"}), 409
  
'''
Bulk delete a group of filters from the database
'''  
@app.route('/bulkDeleteFilters', methods=['POST'])
@cross_origin()
def bulk_deleteFilters():
  filter_group = request.get_json.get('group')
  if collection.find({"group": filter_group}):
    collection.delete_many({"group": filter_group})
    return jsonify({"response": "Succesfully deleted all filters from group"}), 200
  else:
    return jsonify({"response": "Unable to find group"}), 409

# Run the server
if __name__ == '__main__':
   app.run()
