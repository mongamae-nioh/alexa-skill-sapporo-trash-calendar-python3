# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the decorators approach in skill builder.
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import datetime
from ward_calendarnumber import ComfirmWard,CalendarNoInWard
import trashinfo
import dayoftheweek_to_youbi
import json
import pytz

import trashcollection

# for reminder
from ask_sdk_model.services import ServiceException
from ask_sdk_model.services.reminder_management import (
    ReminderRequest, Trigger, TriggerType, AlertInfo, PushNotification,
    PushNotificationStatus, ReminderResponse, AlertInfoSpokenInfo, SpokenText)
from ask_sdk_model.ui import SimpleCard, AskForPermissionsConsentCard

import boto3
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('SapporoTrashCalendar')

from ask_sdk.standard import StandardSkillBuilder
sb = StandardSkillBuilder(table_name="SapporoTrash", auto_create_table=False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# for speak message
json_open = open('./messages/messages.json', 'r')
msg = json.load(json_open)

# variable
## for reminder
REQUIRED_PERMISSIONS = ["alexa::alerts:reminders:skill:readwrite"]
TIME_ZONE_ID = 'Asia/Tokyo'
LOCALE = 'ja-JP'

## date
today = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).date()

# garbagecollection time limit
time_limit = datetime.time(8,30) # 札幌市はAM8:30までにごみを出す

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    # type: (HandlerInput) -> Response

    attr = handler_input.attributes_manager.persistent_attributes
    # 初期設定が終わっていない場合
    if not attr:
        speech_text = msg['text']['1']
        card_title = msg['card_title']['1']
        card_body =  msg['card_body']['1']

        return (
            handler_input.response_builder.speak(speech_text)
            .set_card(SimpleCard(card_title, card_body))
            .set_should_end_session(False)
            .response
        )
    else:
        str_today = str(today)
        area = attr['ward_calno']
        trash_name = trashcollection.what_day(str_today, area)
        speech_text = f'今日は、{trash_name}、の収集日です。'

        return (
            handler_input.response_builder.speak(speech_text)
            .set_card(SimpleCard("今日のごみ", trash_name))
            .response
        )


@sb.request_handler(can_handle_func=is_intent_name("SelectWardIntent"))
def select_ward_intent_handler(handler_input):
    """Handler for select ward Intent."""
    # type: (HandlerInput) -> Response
    slots = handler_input.request_envelope.request.intent.slots
    ward_is = slots['ward'].value
#    synonyms = slots['ward']['resolutions']['resolutionsPerAuthority']['values']['value'].name
#    synonyms = slots['ward'].resolutions['resolutionsPerAuthority']
#    synonyms2 = synonyms['resolutions_per_authority']
    attr = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    if 'ward_calno' in attr:
        text = msg['text']['2']
        card_title = msg['card_title']['2']
        card_body = msg['card_body']['2']
            
        return (
            handler_input.response_builder
            .speak(text)
            .set_card(SimpleCard(card_title, card_body))
            .set_should_end_session(False)
            .response
        )

    input_ward = ComfirmWard(str(ward_is))

    if input_ward.is_not_exist:
        text = msg['text']['3']
        card_title = msg['card_title']['1']

        return (
            handler_input.response_builder
            .speak(text)
            .set_card(SimpleCard(card_title, text))
            .set_should_end_session(False)
            .response
        )
    else:
        session_attr['ward'] = ward_is
        session_attr['ward_name_alpha'] = input_ward.alpha_name
        text = msg['text']['4']

        return (
            handler_input.response_builder
            .speak(text)
            .ask(text)
            .set_should_end_session(False)
            .response
        )


@sb.request_handler(can_handle_func=is_intent_name("SelectCalendarIntent"))
def select_calendarno_intent_handler(handler_input):
    """Handler for select calendar number Intent."""
    # type: (HandlerInput) -> Response
    slots = handler_input.request_envelope.request.intent.slots
    number_is = slots['calendar_number'].value
    attr = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes
    ward_kanji = session_attr['ward']
    ward_alpha = session_attr['ward_name_alpha']

    if 'ward_calno' in attr:
        text = msg['text']['2']
        card_title = msg['card_title']['2']
        card_body = msg['card_body']['2']
            
        return (
            handler_input.response_builder
            .speak(text)
            .ask(text)
            .set_should_end_session(False)
            .response
        )

    ward_calendar_number = CalendarNoInWard(ward_alpha)
    
    if ward_calendar_number.is_not_exist(number_is):
        text = msg['err']['1']
        card_title = msg['card_title']['1']

        return (
            handler_input.response_builder
            .speak(text)
            .set_card(SimpleCard(card_title, text))
            .set_should_end_session(False)
            .response
        )
    else:
        speech_text = f"おすまいは{ward_kanji}、カレンダー番号は{number_is}番です。よろしいですか?"
        session_attr['ward_calno'] = ward_alpha + "-" + number_is
        session_attr['reminder'] = 'no'

        return (
            handler_input.response_builder
            .speak(speech_text)
            .ask(speech_text)
            .response
        )


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.YesIntent"))
def yes_intent_handler(handler_input):
    """Handler for Yes Intent."""
    # type: (HandlerInput) -> Response
    attr = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    # set reminder
    if session_attr['reminder'] == 'can set':
        request_envelope = handler_input.request_envelope
        permissions = request_envelope.context.system.user.permissions

        # no permission
        if not (permissions and permissions.consent_token):
            logger.info("リマインダーをセットできる権限がありません")
            
            return (
                handler_input.response_builder
                .speak("お知らせをセットできませんでした。アレクサアプリを起動して、札幌ごみなげカレンダーのスキルから設定を押し、リマインダーを許可してください。")
                .set_card(AskForPermissionsConsentCard(permissions=REQUIRED_PERMISSIONS))
                .response
            )

        reminder_client = handler_input.service_client_factory.get_reminder_management_service()

        try:
            request_time = session_attr['next_time'] + 'T08:00:00' # AM8:00 on the day
            reminder_response = reminder_client.create_reminder(
                reminder_request=ReminderRequest(
                    trigger=Trigger(
                        object_type=TriggerType.SCHEDULED_ABSOLUTE,
                        scheduled_time=request_time,
                        time_zone_id=TIME_ZONE_ID
                        ),
                    alert_info=AlertInfo(
                        spoken_info=AlertInfoSpokenInfo(
                            content=[SpokenText(locale=LOCALE, text=session_attr['trash_name'] + "の収集日です")])),
                    push_notification=PushNotification(
                        status=PushNotificationStatus.ENABLED))) # type: ReminderResponse
            speech_text = "当日の午前8時にリマインダーを設定しました。"

            logger.info(f"Created reminder : {reminder_response}")
            return handler_input.response_builder.speak(speech_text).set_card(
                SimpleCard(
                    "設定完了", "当日の朝8時にお知らせします")).response

        except ServiceException as e:
            logger.info(f"Exception encountered : {e.body}")
            speech_text = "申し訳ありません。エラーが発生しました。"
            return handler_input.response_builder.speak(speech_text).set_card(
                SimpleCard(
                    "Reminder not created",str(e.body))).response

    if 'ward_calno' in attr:
        speech_text = msg['text']['2']
        card_title = msg['card_title']['2']
        card_body = msg['card_body']['2']
            
        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response

    if session_attr['ward_calno']:
        speech_text = msg['text']['5']
        card_title = msg['card_title']['2']
        card_body = msg['card_body']['2']
            
        # セッション情報をpersistentへ書き込み
        handler_input.attributes_manager.persistent_attributes = session_attr
        handler_input.attributes_manager.save_persistent_attributes()

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response
    else:
        speech_text = msg['text']['1']
        card_title = msg['card_title']['1']
        card_body = msg['card_body']['1']

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.NoIntent"))
def yes_intent_handler(handler_input):
    """Handler for No Intent."""
    # type: (HandlerInput) -> Response
    attr = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    if session_attr['reminder'] == 'can set':
        speech_text = 'わかりました'
        return handler_input.response_builder.speak(speech_text).response

    if session_attr['ward_calno'] in attr:
        speech_text = msg['text']['2']
        card_title = msg['card_title']['2']
        card_body = msg['card_body']['2']

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response

    if not attr:
        session_attr['ward'] = ''
        session_attr['ward_name_alpha'] = ''
        session_attr['ward_calno'] = ''
        speech_text = msg['text']['1']
        card_title = msg['card_title']['1']
        card_body = msg['card_body']['1']

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response
    else:
        speech_text = msg['text']['2']
        return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response


@sb.request_handler(can_handle_func=is_intent_name("WhatTrashDayIntent"))
def help_intent_handler(handler_input):
    """Handler for what trash day Intent."""
    slots = handler_input.request_envelope.request.intent.slots
    date = slots['when'].value
    attr = handler_input.attributes_manager.persistent_attributes
    month = date[5:7]
    day = date[8:10]
    monthday = str(month) + "月" + str(day) + "日"    
    #today = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).date()
    listen_day = datetime.datetime.strptime(date, '%Y-%m-%d').date()

    # 初期設定が終わっていない場合
    if not attr:
        speech_text = msg['text']['1']
        card_title = msg['card_title']['1']
        card_body = msg['card_body']['1']
            
        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response
    else:
        area = attr['ward_calno']
        trash_name = trashcollection.what_day(date, area)

        if trash_name == '収集なし':
            speech_text = '本日、収集はありません。'
        else:
            now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()
            speech_text = f"{trash_name}の日です。"

            if listen_day == today and now > time_limit:
                speech_text += 'なお、ごみを出せるのは当日の朝8時半までです。'

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(monthday, trash_name)).set_should_end_session(True).response

'''
        response = table.query(
            KeyConditionExpression=Key('Date').eq(date) & Key('WardCalNo').eq(attr['ward_calno'])
        )

        trashnumber = response['Items'][0]['TrashNo']
        trashname = trashinfo.return_trash_type(trashnumber)

        if trashnumber == 0:
            speech_text = '本日、収集はありません。'
        else:
            now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()
            #time_limit = datetime.time(8,30) # AM8:30

            if listen_day == today and now > time_limit:
                speech_text = f"{trashname}の日です。なお、ごみを出せるのは当日の朝8時半までです。"
            else:
                speech_text = f"{trashname}の日です。"
        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(monthday, trashname)).set_should_end_session(True).response
'''

@sb.request_handler(can_handle_func=is_intent_name("NextWhenTrashDayIntent"))
def help_intent_handler(handler_input):
    """Handler for next when trash day Intent."""
    slots = handler_input.request_envelope.request.intent.slots
    trashname = slots['trash'].value
    attr = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    if not attr:
        speech_text = msg['text']['1']
        card_title = msg['card_title']['1']
        card_body = msg['card_body']['1']
            
        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response

    if attr['ward_calno'] is not None:
        trashnumber = trashinfo.return_trash_number(trashname)

        response = table.query(
            KeyConditionExpression=Key('WardCalNo').eq(attr['ward_calno']),
            FilterExpression=Attr('TrashNo').eq(trashnumber))

        #today = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).date()
        day_obj = response['Items'][0]['Date']
        next_trash_day = datetime.datetime.strptime(day_obj, '%Y-%m-%d').date()
        official_trash_name = trashinfo.search_trash_type_from_utterance(trashinfo.return_trash_number, trashname)
        session_attr['trash_name'] = official_trash_name
        now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()
        #time_limit = datetime.time(8,30) # AM8:30

        if today == next_trash_day and now > time_limit:
            when = response['Items'][1]['Date'] # next time
            session_attr['next_time'] = when
            speech_text = f"{official_trash_name}は、今日ですが、収集時間を過ぎています。次は"
        else:
            when = response['Items'][0]['Date'] # this time
            session_attr['next_time'] = when
            speech_text = f"{official_trash_name}は、"

        month = when[5:7]
        day = when[8:10]
        monthday = str(month) + "月" + str(day) + "日"
        date = datetime.datetime.strptime(when, '%Y-%m-%d')
        dayoftheweek = date.strftime("%A")
        youbi = dayoftheweek_to_youbi.convert(dayoftheweek)
        speech_text += f"{monthday}、{youbi}です。"

        # set reminder 
        session_attr['reminder'] = 'can set'
        speech_text += f"その日の朝にお知らせしましょうか？"

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(monthday, official_trash_name)).set_should_end_session(False).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = msg['help']['1']
    card_title = msg['card_title']['2']
    card_body = msg['card_body']['2']

    return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).response


@sb.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "わかりました"

    return handler_input.response_builder.speak(speech_text).response

@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # type: (HandlerInput, Exception) -> Response
    logger.error(exception, exc_info=True)

    speech_text = msg['err']['2']
    handler_input.response_builder.speak(speech_text).ask(speech_text)

    return handler_input.response_builder.response


handler = sb.lambda_handler()