import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('SapporoTrashCalendar')

response = table.query(
    KeyConditionExpression=Key('WardCalNo').eq('nishi-2'),
    FilterExpression=Attr('TrashNo').eq('1'))

print(response)