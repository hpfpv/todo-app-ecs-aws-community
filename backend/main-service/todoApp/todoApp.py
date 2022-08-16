from flask import Flask, jsonify, json, Response, request
from flask_cors import CORS
import logging
import todoService


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

@app.route('/<userID>/todos', methods=['GET'])
def getTodos(userID):
    if (request.args.get('search')):
        print(f"Getting filtered for user {userID}")
        filter = request.args.get('search')
        response = todoService.getSearchedTodos(userID, filter)
        logger.info(response)
    else:
        print(f"Getting all todos for user {userID}")
        response = todoService.getTodos(userID)
        logger.info(response)

    flaskResponse = Response(json.dumps(response))
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse

@app.route('/<userID>/todos/<todoID>', methods=['GET'])
def getTodo(userID, todoID):
    print(f'Getting todo: {todoID}')
    response = todoService.getTodo(todoID)

    logger.info(response)

    flaskResponse = Response(response)
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse
    
@app.route('/<userID>/todos/<todoID>/delete', methods=['GET', 'DELETE' , 'POST'])
def deleteTodo(userID, todoID):
    print(f"deleting todo {todoID}")
    todoService.deleteTodoFilesS3(userID, todoID)
    todoService.deleteTodoFilesDynamo(todoID)
    todoService.deleteTodo(todoID)
    
    response = {}
    response["status"] = "success"  

    flaskResponse = Response(json.dumps(response))
    flaskResponse.status_code = 200
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse

@app.route('/<userID>/todos/add', methods=['GET', 'POST'])
def addTodo(userID):
    eventBody = request.json
    responseDB = todoService.addTodo(userID, eventBody)

    logger.info(responseDB)

    response = {}
    response["status"] = "success"  

    flaskResponse = Response(json.dumps(response))
    flaskResponse.status_code = 200
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse

@app.route('/<userID>/todos/<todoID>/complete', methods=['GET', 'POST'])
def completeTodo(userID, todoID):
    response = todoService.completeTodo(todoID)

    logger.info(response)

    flaskResponse = Response(response)
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse

@app.route('/<userID>/todos/<todoID>/addnotes', methods=['GET', 'POST'])
def addTodoNotes(userID, todoID):

    notes = request.json["notes"]
    
    logger.info(f'adding notes for : {todoID}')
    response = todoService.addTodoNotes(todoID, notes)

    logger.info(response)

    flaskResponse = Response(response)
    flaskResponse.headers["Content-Type"] = "application/json"
    flaskResponse.headers["Access-Control-Allow-Origin"] = "https://REPLACE_ME_APP_URL"
    flaskResponse.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

    return flaskResponse



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

    