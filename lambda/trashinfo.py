#from ask_sdk_core.handler_input import HandlerInput
#from ask_sdk_model import Response

import datetime
import dayoftheweek_to_youbi
import pytz
#import trashinfo
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('SapporoTrashCalendar')

# data
import json
trash_json = open('./data/trashdata.json', 'r')
trash_data = json.load(trash_json)

dayoftheweek_json = open('./data/dayoftheweek.json', 'r')
dayoftheweek_data = json.load(dayoftheweek_json)

# variable
## for reminder
REQUIRED_PERMISSIONS = ["alexa::alerts:reminders:skill:readwrite"]
TIME_ZONE_ID = 'Asia/Tokyo'
LOCALE = 'ja-JP'

## date
today = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).date()

# garbagecollection time limit
time_limit = datetime.time(8,30) # AM8:30


class TrashInfo:
    def what_day(self, day: str, area: str) -> str:
        """その日収集されるごみを教えてくれる"""
        response = table.query(
            KeyConditionExpression=Key('Date').eq(day) & Key('WardCalNo').eq(area)
        )
        trash_number = response['Items'][0]['TrashNo']
        return trash_data['trash_type'][str(trash_number)]

    def number(self, trash_name: str) -> int:
        return trash_data['trash_number'][trash_name]

    def official_name(self, trash_name) -> str:
        trash_number = self.number(trash_name)
        return trash_data['trash_type'][str(trash_number)]

    def next_day(self, trash_name: str, area: str) -> str:
        """問い合わせたごみの次の収集日を教えてくれる"""
        trash_number = self.number(trash_name)

        response = table.query(
            KeyConditionExpression=Key('WardCalNo').eq(area),
            FilterExpression=Attr('TrashNo').eq(trash_number))

        day_obj = response['Items'][0]['Date']
        next_trash_day = datetime.datetime.strptime(day_obj, '%Y-%m-%d').date()
        now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()

        # 今日が収集日で収集時間を過ぎている場合は次回の収集日を教える
        if today == next_trash_day and now > time_limit:
            return response['Items'][1]['Date'] # next time(yyyy-mm-dd)
        else:
            return response['Items'][0]['Date'] # this time(yyyy-mm-dd)

    def japanese_date(self, date: datetime.date) -> str:
        month = date.month
        day = date.day
        return str(month) + "月" + str(day) + "日"

    def convert_to_youbi(self, engish: str) -> str:
        return dayoftheweek_data[engish]