import json
import requests
from bs4 import BeautifulSoup
from validator_collection import checkers
import boto3
import os
import logging

s3 = boto3.client('s3')
region = 'us-east-1'


def process_record(bucket, table, id, url):

    logging.info('Retrieved bucket: %s and Table: %s', bucket, table)

    # dynamo operations
    dynamo = boto3.resource('dynamodb', region_name=region)
    table = dynamo.Table(table)

    logging.info('Retrieved url %s', url)

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    page_title = soup.title.string

    # s3 operations
    s3.put_object(Body=response.content, Bucket=bucket, Key=id)
    s3_url = 'https://%s.s3.amazonaws.com/%s' % (bucket, id)

    # dynamo operations
    table.update_item(Item={'id': id}, AttributeUpdates={'title': page_title, 's3url': s3_url, 'status': 'PROCESSED'})
    logging.info('Table updated')

    return {
        'statusCode': 200,
        'body': json.dumps({"page_title": page_title}),
        's3_url': s3_url,
        'status': 'PROCESSED',
        'headers': {
            'Content-Type': 'application/json',
        }
    }


def title_commit(event, context):
    bucket = os.environ.get('S3BUCKET')
    table = os.environ.get('DYNAMO_TABLE')

    # Process records from db stream
    try:
        for record in event['Records']:
            if record['dynamodb']['NewImage']['status']['S'] == 'PENDING':
                item = record['dynamodb']['NewImage']
                result = process_record(bucket, table, item['id']['S'], item['url']['S'])
                print(result)
    except Exception as e:
        print(e)


def input_title(event, context):
    url = event['url']

    # dynamo table info
    table = os.environ.get('DYNAMO_TABLE')

    # validate url
    if checkers.is_url(url):

        key = str(hash(url))

        # dynamo operations
        dynamo = boto3.resource('dynamodb', region_name=region)
        table = dynamo.Table(table)
        table.put_item(Item={'id': key, 'url': url, 'status': 'PENDING'})

        return {
            'statusCode': 200,
            'body': json.dumps({"id": key}),
            'headers': {
                'Content-Type': 'application/json',
            }
        }
    else:
        return {
            'statusCode': 400,
            'body': {"error": "invalid url"},
            'headers': {
                'Content-Type': 'application/json',
            }
        }


def get_title(event, context):
    key = event['id']

    # dynamo table info
    table = os.environ.get('DYNAMO_TABLE')

    # dynamo operations
    dynamo = boto3.resource('dynamodb', region_name=region)
    table = dynamo.Table(table)
    response = table.get_item(Key={'id': key})
    return {
        'statusCode': 200,
        'body': json.dumps({"item": response['Item']}),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
