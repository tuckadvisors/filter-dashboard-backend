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
client = MongoClient(mongo_uri, server_api=ServerApi('1'),tls=True, tlsAllowInvalidCertificates=True)
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
  try:
    # get password from request and convert to bytes
    password = request.get_json().get('password').encode('utf-8')
    # get the password field from mongo
    pswd_field = collection.find_one({"password_store": "1"})
    # check password against encrypted password in db
    if bcrypt.checkpw(password, pswd_field['login_password'].encode('utf-8')):
      return jsonify({'response': 'Valid password'}), 200
    else:
      return jsonify({'response': 'Invalid password'}), 200
  # handle cases where POST is made without proper arguments
  except Exception as e:
    print(e)
    return jsonify({'response': 'Unable to access password from request body'}), 400
    
'''
Add one filter to the database
'''  
@app.route('/addFilter', methods=['POST'])
@cross_origin()
def add_filter():
  try:
    filter_link = request.get_json().get('link')
    filter_group = request.get_json().get('group')
    # for a new filter to be added, it has to be unique on url
    # if we can't find it in the db, scrape it
    if not collection.find_one({"link": filter_link}):
      document = filter_parser.scrape_filter_count({filter_link: filter_group})
      if document["status"] == 200:
        collection.insert_one(document)
        return jsonify({"response": "Successfully added filter to group"}), 200
      else:
        raise TimeoutError
    else:
      return jsonify({"response": "Filter has already been added to dashboard"}), 409
  except Exception as e:
    return jsonify({"response": "Error adding filter " + str(e)}), 400
  
'''
Update all filters in the database
'''
@app.route('/updateAllFilters', methods=['POST'])
@cross_origin()
def update_allFilters():
  try:
    all_results = list(collection.find({}))
    # make sure it doesn't update the password entry
    for result in all_results:
      if "login_password" in result:
        continue
      link = result.get("link")
      if link:
        # scrape the new information
        document = filter_parser.scrape_filter_count({result["link"]: result["group"]})
        if document["status"] == 200:
          # update counts for the existing entry
          update_operation = {"$set": {"count": document["count"]}}
          collection.update_one({"link": result["link"]}, update_operation)
          return jsonify({"response": "Successfully updated all filters"}), 200
        else:
          raise TimeoutError
  except Exception as e:
    print(e)
    return jsonify({"response": "Error updating all filters"}), 400
  
# '''
# Get all filters under a single group 
# '''
# @app.route('/getGroup', methods = ['GET'])
# @cross_origin
# def get_filtersFromGroup():
#   pass

# '''
# Get all filters
# '''
# @app.route('/getAllFilters', methods = ['GET'])
# @cross_origin
# def get_allFilters():
#   pass

'''
Delete one filter from the database
'''  
@app.route('/deleteFilter', methods=['POST'])
@cross_origin()
def delete_filter():
  try:
    filter_link = request.get_json().get('link')
    if collection.find({"link": filter_link}):
      collection.delete_one({"link": filter_link})
      return jsonify({"response": "Succesfully deleted filter"}), 200
    else:
      return jsonify({"response": "Unable to find link to delete"}), 409
  except:
    return jsonify({"response": "Unable to get link from request body"}), 400
  
'''
Bulk delete a group of filters from the database
'''  
@app.route('/bulkDeleteFilters', methods=['POST'])
@cross_origin()
def bulk_deleteFilters():
  try:
    filter_group = request.get_json().get('group')
    if collection.find({"group": filter_group}):
      collection.delete_many({"group": filter_group})
      return jsonify({"response": "Succesfully deleted all filters from group"}), 200
    else:
      return jsonify({"response": "Unable to find group"}), 409
  except:
    return jsonify({"response": "Unable to get group from request body"})

# Run the server
if __name__ == '__main__':
   app.run()
