import json
import requests
from bs4 import BeautifulSoup
from validator_collection import checkers
import boto3
import os
s3 = boto3.client('s3')


def title(event, context):
    url = event['url']

    # s3 bucket and dynamo table info
    bucket = os.environ.get('S3BUCKET')
    table = os.environ.get('DYNAMO_TABLE')

    # validate url
    if checkers.is_url(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        page_title = soup.title.string

        key = str(hash(url))

        # s3 operations
        # s3 = boto3.client('s3')
        # s3bucket = s3.Bucket(bucket)
        s3.put_object(Body=response.content, Bucket=bucket, Key=key)
        s3_url = 'https://%s.s3.amazonaws.com/%s' % (bucket, key)

        # dynamo operations
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(table)
        table.put_item(Item={'id': key, 'title': page_title})

        if not page_title:
            return {
                'statusCode': 400,
                'body': {"error": "Title not found in url"},
                'headers': {
                    'Content-Type': 'application/json',
                }
            }

        return {
            'statusCode': 200,
            'body': json.dumps({"page_title": page_title}),
            's3_url': s3_url,
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
