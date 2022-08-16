import boto3
import json
import os
import logging
import uuid
from collections import defaultdict
from botocore.exceptions import ClientError

dynamo = boto3.client('dynamodb', region_name='REPLACE_ME_AWS_REGION')
s3 = boto3.resource('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bucketName = os.environ['TODOFILES_BUCKET']
bucketCDN = os.environ['TODOFILES_BUCKET_CDN']
todotable = os.environ['TODO_TABLE']
filestable = os.environ['TODOFILES_TABLE']

# get todo files
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


# add todo files
def addTodoFiles(todoID, eventBody):
    logger.info(eventBody)
    
    fileName = eventBody["fileName"]
    fileID = str(uuid.uuid4())
    filePath = eventBody["filePath"]
    fileKey = str(filePath).replace(f'https://{bucketName}/.s3.amazonaws.com/','')
    filePathCDN = 'https://' + bucketCDN + '/' + filePath
    fileForDynamo = {}
    fileForDynamo["fileID"] =  {
        "S": fileID
    }
    fileForDynamo["todoID"] =  {
        "S": todoID
    }
    fileForDynamo["fileName"] =  {
        "S": fileName
    }
    fileForDynamo["filePath"] =  {
        "S": filePathCDN
    }

    logger.info(fileForDynamo)
    try:
        responseDB = dynamo.put_item(
        TableName=filestable,
        Item=fileForDynamo
        ) 

        logger.info(responseDB)
    except ClientError as err:
        logger.info(err)

    responseBody = {}
    responseBody["status"] = "success"

    return {
        'statusCode': 200,
        'body': json.dumps(responseBody)  
    }

# delete todo files
def deleteTodosFileS3(key):
    response = s3.delete_object(
        Bucket=bucketName,
        Key=key,
    )
    logging.info(f"{key} deleted from S3")
    return response
   
def deleteTodosFileDynamo(fileID):
    response = dynamo.delete_item(
        TableName=filestable,
        Key={
            'fileID': {
                'S': fileID
            }
        }
    )
    logging.info(f"{fileID} deleted from DynamoDB")
    return response
