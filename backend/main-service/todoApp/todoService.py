import boto3
import json
import os
import logging
from collections import defaultdict
from boto3.dynamodb.conditions import Key
import re
import uuid
from datetime import datetime

dynamo = boto3.client('dynamodb', region_name='ca-central-1')
s3 = boto3.resource('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bucket = s3.Bucket(os.environ['TODOFILES_BUCKET'])
bucketCDN = os.environ['TODOFILES_BUCKET_CDN']
todotable = os.environ['TODO_TABLE']
filestable = os.environ['TODOFILES_TABLE']

#getTodos
def getTodosJson(items):
    # loop through the returned todos and add their attributes to a new dict
    # that matches the JSON response structure expected by the frontend.
    todoList = defaultdict(list)

    for item in items:
        todo = {}
        todo["todoID"] = item["todoID"]["S"]
        todo["userID"] = item["userID"]["S"]
        todo["dateCreated"] = item["dateCreated"]["S"]
        todo["title"] = item["title"]["S"]
        todo["description"] = item["description"]["S"]
        todo["notes"] = item["notes"]["S"]
        todo["dateDue"] = item["dateDue"]["S"]
        todo["completed"] = item["completed"]["BOOL"]
        todoList["todos"].append(todo)
    return todoList
 
def getTodos(userID):
    # Use the DynamoDB API Query to retrieve todos from the table that belong
    # to the specified userID.
    filter = "userID"
    response = dynamo.query(
        TableName=todotable,
        IndexName=filter+'Index',
        KeyConditions={
            filter: {
                'AttributeValueList': [
                    {
                        'S': userID
                    }
                ],
                'ComparisonOperator': "EQ"
            }
        }
    )
    logging.info(response["Items"])
    todoList = getTodosJson(response["Items"])
    items = json.dumps(todoList)
    data = json.loads(items)
    response = defaultdict(list)
    sortedData1 = sorted(data["todos"], key = lambda i: i["dateCreated"], reverse=True)
    sortedData2 = sorted(sortedData1, key = lambda i: i["dateDue"])
    sortedData3 = sorted(sortedData2, key = lambda i: i["completed"])
    response = defaultdict(list)

    for item in sortedData3:
        todo = {}
        todo["todoID"] = item["todoID"]
        todo["userID"] = item["userID"]
        todo["dateCreated"] = item["dateCreated"]
        todo["title"] = item ["title"]
        todo["description"] = item["description"]
        todo["notes"] = item["notes"]
        todo["dateDue"] = item["dateDue"]
        todo["completed"] = item["completed"]

        response["todos"].append(todo)
    logger.info(response)
    return response

def getSearchedTodos(userID, filter):
    items = getTodos(userID)
    data = items
    response = defaultdict(list)
    
    for item in data["todos"]:
        todo = {}
        if re.search(filter, item["title"], re.IGNORECASE): 
            todo["todoID"] = item["todoID"]
            todo["userID"] = item["userID"]
            todo["dateCreated"] = item["dateCreated"]
            todo["title"] = item ["title"]
            todo["description"] = item["description"]
            todo["notes"] = item["notes"]
            todo["dateDue"] = item["dateDue"]
            todo["completed"] = item["completed"]
            response["todos"].append(todo)
    
    logging.info(response)
    return response

#getTodo
def getTodoJson(item):
    todo = {}
    todo["todoID"] = item["todoID"]["S"]
    todo["userID"] = item["userID"]["S"]
    todo["dateCreated"] = item["dateCreated"]["S"]
    todo["title"] = item["title"]["S"]
    todo["description"] = item["description"]["S"]
    todo["notes"] = item["notes"]["S"]
    todo["dateDue"] = item["dateDue"]["S"]
    todo["completed"] = item["completed"]["BOOL"]

    return todo

def getTodo(todoID):
    response = dynamo.get_item(
        TableName=todotable,
        Key={
            'todoID': {
                'S': todoID
            }
        }
    )
    response = getTodoJson(response["Item"])
    return json.dumps(response)

#deleteTodo
def getFilesJson(items):
    # loop through the returned todos and add their attributes to a new dict
    # that matches the JSON response structure expected by the frontend.
    fileList = defaultdict(list)

    for item in items:
        file = {}
        file["fileID"] = item["fileID"]["S"]
        file["todoID"] = item["todoID"]["S"]
        file["fileName"] = item["fileName"]["S"]
        file["filePath"] = item["filePath"]["S"]
        fileList["files"].append(file)
    return fileList
 
def getTodosFiles(todoID):
    # Use the DynamoDB API Query to retrieve todo files from the table that belong
    # to the specified todoID.
    filter = "todoID"
    response = dynamo.query(
        TableName=filestable,
        IndexName=filter+'Index',
        KeyConditions={
            filter: {
                'AttributeValueList': [
                    {
                        'S': todoID
                    }
                ],
                'ComparisonOperator': "EQ"
            }
        }
    )
    logging.info(response["Items"])
    fileList = getFilesJson(response["Items"])
    return json.dumps(fileList)


def deleteTodo(todoID):
    response = dynamo.delete_item(
        TableName=todotable,
        Key={
            'todoID': {
                'S': todoID
            }
        }
    )
    logging.info(f"{todoID} deleted")
    return response

def deleteTodoFilesS3(userID, todoID):
    prefix = userID + "/" + todoID + "/"
    for key in bucket.objects.filter(Prefix=prefix):
        key.delete()
        logging.info(f"{key} deleted")
    return (f"{todoID} files deleted from s3")

def deleteTodoFilesDynamo(todoID):
    data = json.loads(getTodosFiles(todoID))
    if data :
        files = data["files"]
        for file in files:
            fileID = file["fileID"]
            dynamo.delete_item(
                TableName=filestable,
                Key={
                    'fileID': {
                        'S': fileID
                    }
                }
            )
            logging.info(f"{fileID} deleted")
        return (f"{todoID} files deleted from dynamoDB")
    else:
        logging.info(f"{todoID}: no files to delete")
        return (f"{todoID}: no files to delete")

#addTodo
def addTodo(userID, eventBody):
    dateTimeObj = datetime.now()
    todo = {}
    todo["todoID"] = {
        "S": str(uuid.uuid4())
        }
    todo["userID"] = {
        "S": userID
        }
    todo["dateCreated"] = {
        "S": str(dateTimeObj)
        }
    todo["title"] = {
        "S": eventBody["title"]
        }    
    todo["description"] = {
        "S": eventBody["description"]
        }
    todo["notes"] = {
        "S": ""
        }
    todo["dateDue"] = {
        "S": eventBody["dateDue"]
        }
    todo["completed"] = {
        "BOOL": False
        }

    response = dynamo.put_item(
        TableName=todotable,
        Item=todo
        ) 
    logger.info(response)   
    responseBody = {}
    responseBody["status"] = "success"

    return {
        'statusCode': 200,
        'body': json.dumps(responseBody)  
    }

#completeTodo
def completeTodo(todoID):
    response = dynamo.update_item(
        TableName=todotable,
        Key={
            'todoID': {
                'S': todoID
            }
        },
        UpdateExpression="SET completed = :b",
        ExpressionAttributeValues={':b': {'BOOL': True}}
    )
    response = {}
    response["Update"] = "Success"

    return json.dumps(response)

#addTodoNotes
def addTodoNotes(todoID, notes):
    response = dynamo.update_item(
        TableName=todotable,
        Key={
            'todoID': {
                'S': todoID
            }
        },
        UpdateExpression="SET notes = :b",
        ExpressionAttributeValues={':b': {'S': notes}}
    )
    response = {}
    response["Update"] = "Success";

    return json.dumps(response)