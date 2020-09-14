import json
import requests
from bs4 import BeautifulSoup
from validator_collection import checkers


def title(event, context):

    url = event['queryStringParameters']['url']

    # validate url
    if checkers.is_url(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        page_title = soup.title.string

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
