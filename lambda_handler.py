import json
import requests
from bs4 import BeautifulSoup
from validator_collection import checkers
import boto3
import os
import asyncio
import logging

s3 = boto3.client('s3')


async def title(key):
    # s3 bucket and dynamo table info
    bucket = os.environ.get('S3BUCKET')
    table = os.environ.get('DYNAMO_TABLE')
    logging.info('Retrieved bucket: %s and Table: %s', bucket, table)
    # dynamo operations
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(table)
    # get key and then url
    key = table.get_item(Key={'id': key})
    item = key['Item']
    url = item['url']
    logging.info('Retrieved url %s', url)

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    page_title = soup.title.string

    # s3 operations
    s3.put_object(Body=response.content, Bucket=bucket, Key=key)
    s3_url = 'https://%s.s3.amazonaws.com/%s' % (bucket, key)

    # dynamo operations
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(table)
    table.update_item(Item={'id': key}, AttributeUpdates={'title': page_title, 's3url': s3_url, 'status': 'PROCESSED'})
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


def input_title(event, context):
    url = event['url']

    # dynamo table info
    table = os.environ.get('DYNAMO_TABLE')

    # validate url
    if checkers.is_url(url):

        key = str(hash(url))

        # dynamo operations
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(table)
        table.put_item(Item={'id': key, 'url': url, 'status': 'PENDING'})

        asyncio.run(title(key))

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
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(table)
    response = table.get_item(Key={'id': key})
    return {
        'statusCode': 200,
        'body': json.dumps({"item": response['Item']}),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
