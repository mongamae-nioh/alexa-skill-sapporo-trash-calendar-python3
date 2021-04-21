# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the decorators approach in skill builder.
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

import data
import boto3
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('SapporoTrashCalendar')

from ask_sdk.standard import StandardSkillBuilder
sb = StandardSkillBuilder(table_name="SapporoTrash", auto_create_table=False)

from ward_calendarnumber import ComfirmWard,CalendarNoInWard

from trashtype import check

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    # type: (HandlerInput) -> Response
    attr = handler_input.attributes_manager.persistent_attributes
    if not attr:
        speech_text = "札幌市のゴミ収集情報をお知らせします。はじめに、収集エリアの設定を行います。おすまいの区を教えてください"
        card_title = "初期設定"
        card_body = "お住いの区を教えてください"
        reprompt = "おすまいの区を教えてください"
    else:
        speech_text = "今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        reprompt = "今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        card_title = "こんな風に話かけてください"
        card_body = "・今日のゴミはなに？\n・燃えないゴミは次いつ？"
    
    # set current values to sesssion attributes
    #handler_input.attributes_manager.session_attributes = attr

    return (
        handler_input.response_builder
        .speak(speech_text)
        .ask(reprompt)
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
        speech_text = "今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        card_title = "こんな風に話かけてください"
        card_body = "・今日のゴミはなに？\n・燃えないゴミは次いつ？"
            
        handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False)
        return handler_input.response_builder.response

    input_ward = ComfirmWard(str(ward_is))

    if input_ward.is_not_exist:
        speech_text = "お住まいの、区を教えてください"
        
        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard("initial setting", speech_text)).set_should_end_session(False).response
    else:
        session_attr['ward'] = ward_is
        session_attr['ward_name_alpha'] = input_ward.alpha_name
        speech_text = "つづいてカレンダー番号を教えてください。カレンダー番号は札幌市から配布された家庭ごみ収集日のカレンダーか、札幌市のウェブサイトで確認できます"

        return (
            handler_input.response_builder
            .speak(speech_text)
            .ask(speech_text)
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
        speech_text = "今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        card_title = "こんな風に話かけてください"
        card_body = "・今日のゴミはなに？\n・燃えないゴミは次いつ？"
            
        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response

    ward_calendar_number = CalendarNoInWard(ward_alpha)
    
    if ward_calendar_number.is_not_exist(number_is):
        speech_text = "そのカレンダー番号はありませんでした。ただしい番号を教えてください"

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard("initial setting", speech_text)).set_should_end_session(False).response
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
        speech_text = "今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        card_title = "こんな風に話かけてください"
        card_body = "・今日のゴミはなに？\n・燃えないゴミは次いつ？"
            
        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response
    if session_attr['ward_calno']:
        speech_text = "初期設定が完了しました。今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        card_title = "こんな風に話かけてください"
        card_body = "・今日のゴミはなに？\n・燃えないゴミは次いつ？"
            
        # セッション情報をpersistentへ書き込み
        handler_input.attributes_manager.persistent_attributes = session_attr
        handler_input.attributes_manager.save_persistent_attributes()

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response
    else:
        speech_text = "初期設定を行います。お住いの区を教えてください"
        card_title = "初期設定"
        card_body = "お住いの区を教えてください"

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.NoIntent"))
def yes_intent_handler(handler_input):
    """Handler for No Intent."""
    # type: (HandlerInput) -> Response
    attr = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    if session_attr['ward_calno'] in attr:
        speech_text = "今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        card_title = "こんな風に話かけてください"
        card_body = "・今日のゴミはなに？\n・燃えないゴミは次いつ？"

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response

    if not attr:
        session_attr['ward'] = ''
        session_attr['ward_name_alpha'] = ''
        session_attr['ward_calno'] = ''
        speech_text = "初期設定を行います。お住いの区を教えてください"
        card_title = "初期設定"
        card_body = "お住いの区を教えてください"
        reprompt = "おすまいの区を教えてください"

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False).response
    else:
        speech_text = "今日以降で何のゴミか知りたい日、または、出したいゴミの種類、どちらかを教えてください"
        return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response


@sb.request_handler(can_handle_func=is_intent_name("WhatTrashDayIntent"))
def help_intent_handler(handler_input):
    """Handler for what trash day Intent."""
    slots = handler_input.request_envelope.request.intent.slots
    date = slots['when'].value
    attr = handler_input.attributes_manager.persistent_attributes
    slicemonth = date[5:7]
    sliceday = date[8:10]
    monthday = str(slicemonth) + "月" + str(sliceday) + "日"    

    if not attr:
        speech_text = "はじめに、収集エリアの設定を行います。おすまいの区を教えてください"
        card_title = "初期設定"
        card_body = "お住いの区を教えてください"
        reprompt = "おすまいの区を教えてください"
            
        handler_input.response_builder.speak(speech_text).ask(reprompt).set_card(SimpleCard(card_title, card_body)).set_should_end_session(False)
        return handler_input.response_builder.response

    if attr['ward_calno'] is not None:
        response = table.query(
            KeyConditionExpression=Key('Date').eq(date) & Key('WardCalNo').eq(attr['ward_calno'])
        )

        TrashNo = response['Items'][0]['TrashNo']
        trashname = check(TrashNo)        
        speech_text = f"{trashname}の日です。"

        handler_input.response_builder.speak(speech_text).ask(speech_text).set_card(SimpleCard(monthday, trashname)).set_should_end_session(True)
        return handler_input.response_builder.response

@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "お住まいの地域の、ゴミの収集情報をお知らせします。たとえば、今日のゴミはなに？もしくは、次の燃えないゴミはいつ？と聞いてください"
    card_title = "こんな風に話かけてください"
    card_body = "・今日のゴミはなに？\n・燃えないゴミは次いつ？"

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

    speech = "すみません、わかりませんでした。もう一度言ってください。"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


handler = sb.lambda_handler()