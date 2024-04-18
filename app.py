"""
This Flask application sets up a RESTful API to interact with a MongoDB database containing data related to Lok Sabha elections.

The API provides the following endpoints:

1. /get-all-lokshaba-data:
   - GET: Retrieve all Lok Sabha data from the database.
   - POST: Filter Lok Sabha data based on parameters such as year, PC name, and state name.

2. /get-all-winner-lokshaba-data:
   - GET: Retrieve data of winning candidates in Lok Sabha elections.
   - POST: Filter winner data based on parameters such as year, PC name, and state name.
            -> It can be used for pie Chart if you add the query parameter pieChart=1 
            -> i.e: /get-all-winner-lokshaba-data?pieChart=1 (it ignores the statename in output)
            -> Applicable only for Year filter

3. /get-filter-data:
   - GET: Retrieve unique years and state names available in the dataset.

4. /get-pc-names:
   - POST: Retrieve the list of PC (Parliamentary Constituency) names for a given state name.

5. /get-logo/<string:PartyAbberivationName>:
    - GET: Retrieve the logo of thegiven Party. eg: /get-logo/DMDK

The MongoDB connection is established, and the necessary API resources are defined using Flask-Restful.

Usage:
1. Run the Flask application, and access the API endpoints using appropriate HTTP requests.
2. Use GET requests to retrieve data and POST requests to filter data based on parameters.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_restful import Api, Resource
from pymongo import MongoClient
from flask_cors import CORS
import os
import glob

app = Flask(__name__)
api = Api(app)
CORS(app)

# MongoDB connection
#client = MongoClient('mongodb://localhost:27017/')
connection_string = "mongodb+srv://scriptuser:gx21SgYInMgLmgN2@cluster.nf36z1t.mongodb.net/"
# Connect to MongoDB Atlas
client = MongoClient(connection_string)
db = client['Lokshaba']
collection = db['Lokshaba']

class Home(Resource):
    def get(self):
        return jsonify({"message":"ok"})
class Image(Resource):
    """
        Retrieve an image file with the given filename from the 'static/logo' directory.

        Args:
            filename (str): The name of the image file to retrieve.

        Returns:
            flask.Response: A response containing the requested image file.

        Raises:
            NotFound: If the specified image file does not exist in the 'static/logo' directory.

        Note:
            This method assumes that the image files are stored in the 'static/logo' directory.
            Ensure that the filename provided includes the appropriate file extension (e.g., '.png').
    """
    def get(self):
        filename = request.args.get('partyName',None)
        if filename is not None:
            filename = filename + ".png"
            filepath = os.path.join('static/logo', filename)
            
            if os.path.exists(filepath):
                return send_from_directory('static/logo', filename)
            else:
                error_message = {"error": "Image not found"}
                return error_message, 404
        else:
            data = list(collection.find({}, {'_id': 0,'logo_url':1,'PARTY NAME':1}))
            return jsonify(data)

        
class CompleteLokshabaData(Resource):
    """
    Represents an API resource for retrieving complete Lok Sabha data.

    Methods:
        - get: Retrieve all Lok Sabha data from the database.
        - post: Filter Lok Sabha data based on parameters such as year, PC name, and state name.
    """
    def get(self):
        """
        Retrieve all Lok Sabha data from the database.

        Returns:
            JSON: JSON response containing all Lok Sabha data.
        """
        # Retrieve all documents in the collection
        data = list(collection.find({}, {'_id': 0}))
        return jsonify(data)

    def post(self):
        """
        Filter Lok Sabha data based on parameters such as year, PC name, and state name.

        Returns:
            JSON: JSON response containing filtered Lok Sabha data.
        """
        # Parse POST parameters
        year = request.json.get('year', None)
        pc_name = request.json.get('PC_name', None)
        state_name = request.json.get('state_name', None)

        # Build query based on parameters
        query = {}
        if year:
            query['year'] = year
        if pc_name:
            query['PC NAME'] = pc_name
        if state_name:
            query['STATE NAME'] = state_name

        # Fetch filtered data from MongoDB excluding _id field
        data = list(collection.find(query, {'_id': 0}))
        return jsonify(data)


class CompleteWinnerLokshabaData(Resource):
    """
    Represents an API resource for retrieving complete data of winning candidates in Lok Sabha elections.

    Methods:
        - get: Retrieve data of winning candidates in Lok Sabha elections.
        - post: Filter winner data based on parameters such as year, PC name, and state name.
    """
    def get(self):
        """
        Retrieve data of winning candidates in Lok Sabha elections.

        Returns:
            JSON: JSON response containing data of winning candidates.
        """
        query = {'is_winner': 1}
        # Retrieve all documents in the collection
        data = list(collection.find(query, {'_id': 0}))
        return jsonify(data)

    def post(self):
        """
        Filter winner data based on parameters such as year, PC name, and state name.

        Returns:
            JSON: JSON response containing filtered winner data.
        """
        # Parse POST parameters
        year = request.json.get('year', None)
        pc_name = request.json.get('PC_name', None)
        state_name = request.json.get('state_name', None)

        if year is None and state_name is None:
            return jsonify({"error": "Atleast one parameter is required"})
        
        piechart = request.args.get('pieChart',None)
        # Build query based on parameters
        if pc_name is None and state_name is None:

            """
            If neither PC name nor state name is provided, 
            aggregate data based on year and return party-wise seat distribution.
            """
            pipeline = [
                {"$match": {"year": year}},
                {"$group": {"_id": {"Party": "$PARTY NAME", "State": "$STATE NAME","Alliance": "$Alliance"}, "totalSeats": {"$sum": 1}}},
                {"$project": {
                                "_id": 0,
                                "Party": "$_id.Party",
                                "State": "$_id.State",
                                "Alliance": "$_id.Alliance",
                                "totalSeats": 1
                            }}
            ]
            # Execute the aggregation pipeline
            result = collection.aggregate(pipeline)
            # Convert the result into a dictionary
            if piechart:
                #data_pool = [{"party_name":entry['_id']['Party'], "seat": entry['totalSeats'], "logo_url": entry['Logo']} for entry in result]
                # Initialize dictionaries to store the total seats for each party
                data = {}
                # Iterate through the data
                for entry in result:
                    # Extract party name and seat count from each entry
                    party_name = entry['Party']
                    alliance_name = entry['Alliance']
                    seat_count = entry['totalSeats']                    
                    # Check if the party name already exists in the dictionary
                    if party_name in data:
                        # If yes, add the seat count to the existing total
                        data[party_name]['alliance'] = alliance_name
                        data[party_name]['seat']+= seat_count
                    else:
                        # If no, create a new entry with the seat count
                        data[party_name] ={}
                        data[party_name]['seat'] = seat_count
                data = [{"party_name":partyname,"seat":details['seat']} for partyname,details in data.items()]            
            else:
                data = {}
                # Iterate through the data
                for entry in result:
                    # Extract party name and seat count from each entry
                    party_name = entry['Party']
                    alliance_name = entry['Alliance']
                    seat_count = entry['totalSeats']    
                    state_name = entry['State']                
                    # Check if the party name already exists in the dictionary
                    if party_name in data:
                        # If yes, add the seat count to the existing total
                        data[party_name]['seat']+= seat_count
                    else:
                        # If no, create a new entry with the seat count
                        data[party_name] ={}
                        data[party_name]['alliance'] = alliance_name
                        data[party_name]['seat'] = seat_count
                        data[party_name]['state'] = state_name
                data = [{"party_name":partyname, "state_name":details['state'],"seat": details['seat'],"alliance":details['alliance']} for partyname,details in data.items()]
            return jsonify(data)
        
        elif pc_name is None and state_name is not None:

            pipeline = [
                {"$match": {"year": year, "STATE NAME": state_name}},
                {"$group": {"_id": {"Party": "$PARTY NAME", "State": "$STATE NAME","Alliance": "$Alliance"}, "totalSeats": {"$sum": 1}}},
                {"$project": {
                                "_id": 0,
                                "Party": "$_id.Party",
                                "State": "$_id.State",
                                "Alliance": "$_id.Alliance",
                                "totalSeats": 1
                            }}
            ]
            # Execute the aggregation pipeline
            result = collection.aggregate(pipeline)
            # Convert the result into a dictionary
            data = [{"party_name": entry['Party'], "state_name": entry['State'], "seat": entry['totalSeats'], "alliance": entry['Alliance']} for entry in result]
            return jsonify(data)

        else:
            """
            If PC name or state name (or both) are provided, 
            filter data based on year, PC name, and/or state name and return winner data.
            """
            query = {}
            if year:
                query['year'] = year
            if pc_name:
                query['PC NAME'] = pc_name
            if state_name:
                query['STATE NAME'] = state_name

            query['is_winner'] = 1
            # Fetch filtered data from MongoDB excluding _id field
            data = list(collection.find(query, {'_id': 0}))
            return jsonify(data)


class GetPcName(Resource):
    """
    Represents an API resource for retrieving PC (Parliamentary Constituency) names for a given state.

    Methods:
        - post: Retrieve the list of PC names for a given state name.
    """

    def post(self):
        """
        Retrieve the list of PC names for a given state name.

        Returns:
            JSON: JSON response containing the list of PC names.
        """
        state_name = request.json.get('state_name', None)
        if state_name:
            documents = collection.find({"STATE NAME": state_name})
            # Extract unique PC names from the filtered documents
            data = sorted(list(set(document["PC NAME"]
                          for document in documents)))
            return jsonify(data)
        else:
            return jsonify([])


class GetFilterData(Resource):
    """
    Represents an API resource for retrieving unique years and state names available in the dataset.

    Methods:
        - get: Retrieve unique years and state names available in the dataset.
    """
    def get(self):
        """
        Retrieve unique years and state names available in the dataset.

        Returns:
            JSON: JSON response containing unique years and state names.
        """
        unique_years = sorted(collection.distinct("year"))
        unique_statename = sorted(collection.distinct("STATE NAME"))
        data = {"years": unique_years, "state_name": unique_statename}
        return jsonify(data)


# Add resource to the API
api.add_resource(CompleteLokshabaData, '/get-all-lokshaba-data')
api.add_resource(CompleteWinnerLokshabaData, '/get-all-winner-lokshaba-data')
api.add_resource(GetFilterData, '/get-filter-data')
api.add_resource(GetPcName, '/get-pc-names')
api.add_resource(Image, '/static/logo')
api.add_resource(Home, '/')

if __name__ == '__main__':
    app.run(debug=True)
