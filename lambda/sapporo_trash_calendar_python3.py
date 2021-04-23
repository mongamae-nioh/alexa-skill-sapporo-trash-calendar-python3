# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the decorators approach in skill builder.
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('SapporoTrashCalendar')

from ask_sdk.standard import StandardSkillBuilder
sb = StandardSkillBuilder(table_name="SapporoTrash", auto_create_table=False)

from ward_calendarnumber import ComfirmWard,CalendarNoInWard

import trashinfo
import dayoftheweek_to_youbi

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import json
json_open = open('./messages/messages.json', 'r')
msg = json.load(json_open)

from speech_builder import generate_speech

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    # type: (HandlerInput) -> Response
    attr = handler_input.attributes_manager.persistent_attributes
    if not attr:
        text = msg['text']['1']
        card_title = msg['card_title']['1']
        card_body =  msg['card_body']['1']
    else:
        text = msg['text']['2']
        card_title = msg['card_title']['2']
        card_body = msg['card_body']['2']
    
    # set current values to sesssion attributes
    #handler_input.attributes_manager.session_attributes = attr

#    return generate_speech(handler_input, text, card_title, card_body, 'no')

    return (
        handler_input.response_builder.speak(text)
        .set_card(SimpleCard(card_title, card_body))
        .set_should_end_session(False)
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

    if not attr:
        speech_text = "msg['text']['1']"
        card_title = msg['card_title']['1']
        card_body = msg['card_body']['1']
            
        handler_input.response_builder.speak(speech_text).ask(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False)
        return handler_input.response_builder.response

    if attr['ward_calno'] is not None:
        response = table.query(
            KeyConditionExpression=Key('Date').eq(date) & Key('WardCalNo').eq(attr['ward_calno'])
        )

        TrashNo = response['Items'][0]['TrashNo']
        trashname = trashinfo.return_trash_type(TrashNo)        
        speech_text = f"{trashname}の日です。"

        handler_input.response_builder.speak(speech_text).set_card(SimpleCard(monthday, trashname)).set_should_end_session(True)
        return handler_input.response_builder.response

@sb.request_handler(can_handle_func=is_intent_name("NextWhenTrashDayIntent"))
def help_intent_handler(handler_input):
    """Handler for next when trash day Intent."""
    slots = handler_input.request_envelope.request.intent.slots
    trashname = slots['trash'].value
    attr = handler_input.attributes_manager.persistent_attributes

    if not attr:
        speech_text = "msg['text']['1']"
        card_title = msg['card_title']['1']
        card_body = msg['card_body']['1']
            
        handler_input.response_builder.speak(speech_text).ask(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False)
        return handler_input.response_builder.response

    if attr['ward_calno'] is not None:
        trashnumber = trashinfo.return_trash_number(trashname)
        
        response = table.query(
            KeyConditionExpression=Key('WardCalNo').eq(attr['ward_calno']),
            FilterExpression=Attr('TrashNo').eq(trashnumber))
        
        when = response['Items'][0]['Date']
        month = when[5:7]
        day = when[8:10]
        monthday = str(month) + "月" + str(day) + "日"

        date = datetime.datetime.strptime(when, '%Y-%m-%d')
        dayoftheweek = date.strftime("%A")
        youbi = dayoftheweek_to_youbi.convert(dayoftheweek)
        official_trash_name = trashinfo.search_trash_type_from_utterance(trashinfo.return_trash_number, trashname)

        speech_text = f"次の{official_trash_name}は、{monthday}、{youbi}です。"

        handler_input.response_builder.speak(speech_text).set_card(SimpleCard(monthday, official_trash_name)).set_should_end_session(True)
        return handler_input.response_builder.response

@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = msg['help']['1']
    card_title = msg['card_title']['2']
    card_body = msg['card_body']['2']

    return handler_input.response_builder.speak(speech_text).ask(
        speech_text).set_card(SimpleCard(
            card_title, card_body)).response


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

    speech = msg['err']['2']
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


handler = sb.lambda_handler()