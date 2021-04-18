# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the decorators approach in skill builder.
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

import boto3
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('SapporoTrashCalendar')

from ask_sdk.standard import StandardSkillBuilder
sb = StandardSkillBuilder(table_name="SapporoTrash", auto_create_table=False)

from ward_calendarnumber import ComfirmWard,CalendarNoInWard

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
    ward_is = session_attr['ward']
    ward = session_attr['ward_name_alpha']

    ward_calendar_number = CalendarNoInWard(ward)
    
    if ward_calendar_number.is_not_exist(number_is):
        speech_text = "そのカレンダー番号はありませんでした。ただしい番号を教えてください"

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard("initial setting", speech_text)).set_should_end_session(False).response
    else:
        speech_text = f"おすまいは{ward_is}、カレンダー番号は{number_is}番です。よろしいですか?"

        return (
            handler_input.response_builder
            .speak(speech_text)
            .ask(speech_text)
            .response
        )

@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "You can say hello to me!"

    return handler_input.response_builder.speak(speech_text).ask(
        speech_text).set_card(SimpleCard(
            "Hello World", speech_text)).response


@sb.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "Goodbye!"

    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Hello World", speech_text)).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    # type: (HandlerInput) -> Response
    speech = (
        "The Hello World skill can't help you with that.  "
        "You can say hello!!")
    reprompt = "You can say hello!!"
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


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

    speech = "Sorry, there was some problem. Please try again!!"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


handler = sb.lambda_handler()