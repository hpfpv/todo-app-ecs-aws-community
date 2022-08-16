from flask import Flask, jsonify, json, Response, request
from flask_cors import CORS
import logging
import os
import todoFilesService


logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

#route for health checks only.
@app.route('/', methods=['GET'])
def healthCheck():
        
    response = {
        "info": "Nothing here. Health checks only!"
    }
    flaskResponse = Response(json.dumps(response))
    flaskResponse.status = "success"
    flaskResponse.status_code = 200
    flaskResponse.headers["Content-Type"] = "application/json"


    return flaskResponse

# route for get todo files
@app.route('/<todoID>/files', methods=['GET'])
def getTodoFiles(todoID):
    
    print(f"Getting all files for todo {todoID}")
    response = todoFilesService.getTodosFiles(todoID)

    logger.info(response)

    flaskResponse = Response(response)
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse

# route for add todo files
@app.route('/<todoID>/files/upload', methods=['GET', 'POST'])
def addTodoFiles(todoID):
    eventBody = request.json
    responseDB = todoFilesService.addTodoFiles(todoID, eventBody)

    logger.info(responseDB)

    response = {}
    response["status"] = "success"  

    flaskResponse = Response(json.dumps(response))
    flaskResponse.status_code = 200
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse


#route for delete todo files
@app.route('/<todoID>/files/<fileID>/delete', methods=['GET', 'DELETE', 'POST'])
def deleteTodoFile(todoID, fileID):
    eventBody = request.json
    bucketCDN = os.environ['TODOFILES_BUCKET_CDN']

    filePath = eventBody["filePath"]
    fileKey = str(filePath).replace(f'https://{bucketCDN}/', '').replace('%40','@')

    print(f"deleting file {fileID}")
    todoFilesService.deleteTodosFileS3(fileKey)
    todoFilesService.deleteTodosFileDynamo(fileID)
    
    response = {}
    response["status"] = "success"  

    flaskResponse = Response(json.dumps(response))
    flaskResponse.status_code = 200
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"


    return flaskResponse


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)

    