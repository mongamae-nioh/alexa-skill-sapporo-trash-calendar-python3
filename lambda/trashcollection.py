#from ask_sdk_core.handler_input import HandlerInput
#from ask_sdk_model import Response

import datetime
import dayoftheweek_to_youbi
import pytz
import trashinfo
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('SapporoTrashCalendar')

# variable
## for reminder
REQUIRED_PERMISSIONS = ["alexa::alerts:reminders:skill:readwrite"]
TIME_ZONE_ID = 'Asia/Tokyo'
LOCALE = 'ja-JP'

## date
today = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).date()

# garbagecollection time limit
time_limit = datetime.time(8,30) # AM8:30


def what_day(day: str, area: str ) -> str:
    """その日収集されるごみを教えてくれる"""
    response = table.query(
        KeyConditionExpression=Key('Date').eq(day) & Key('WardCalNo').eq(area)
    )

    trash_number = response['Items'][0]['TrashNo']
    trash_name = trashinfo.return_trash_type(trash_number)

    return trash_name

def next_day(trash_name: str, area: str) -> str:
    """問い合わせたごみの次の収集日を教えてくれる"""
    trash_number = trashinfo.return_trash_number(trash_name)

    response = table.query(
        KeyConditionExpression=Key('WardCalNo').eq(area),
        FilterExpression=Attr('TrashNo').eq(trash_number))

    day_obj = response['Items'][0]['Date']
    next_trash_day = datetime.datetime.strptime(day_obj, '%Y-%m-%d').date()
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()

    # 今日が収集日で収集時間を過ぎている場合は次回の収集日を教える
    if today == next_trash_day and now > time_limit:
        when = response['Items'][1]['Date'] # next time
    else:
        when = response['Items'][0]['Date'] # this time

    return when


def next_day_japanese(func) -> str:
    monthday = func
    month = monthday[5:7]
    day = monthday[8:10]
    return str(month) + "月" + str(day) + "日"


def next_trash_day(trash_name: str, area: str) -> str:
    """問い合わせたごみの次の収集日を教えてくれる"""
    trash_number = trashinfo.return_trash_number(trash_name)

    response = table.query(
        KeyConditionExpression=Key('WardCalNo').eq(area),
        FilterExpression=Attr('TrashNo').eq(trash_number))

    day_obj = response['Items'][0]['Date']
    next_trash_day = datetime.datetime.strptime(day_obj, '%Y-%m-%d').date()
    official_trash_name = trashinfo.search_trash_type_from_utterance(trashinfo.return_trash_number, trash_name)
#    session_attr['trash_name'] = official_trash_name
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()

    # 今日が収集日で収集時間を過ぎている場合は次回の収集日を教える
    if today == next_trash_day and now > time_limit:
        when = response['Items'][1]['Date'] # next time
#        session_attr['next_time'] = when
        speech_text = f"{official_trash_name}は、今日ですが、収集時間を過ぎています。次は"
    else:
        when = response['Items'][0]['Date'] # this time
#        session_attr['next_time'] = when
        speech_text = f"{official_trash_name}は、"

    month = when[5:7]
    day = when[8:10]
    monthday = str(month) + "月" + str(day) + "日"
    date = datetime.datetime.strptime(when, '%Y-%m-%d')
    dayoftheweek = date.strftime("%A")
    youbi = dayoftheweek_to_youbi.convert(dayoftheweek)
    speech_text += f"{monthday}、{youbi}です。"

    return speech_text