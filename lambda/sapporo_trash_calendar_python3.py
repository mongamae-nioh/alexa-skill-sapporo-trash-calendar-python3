# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the decorators approach in skill builder.
import logging
from typing import Collection

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# リマインダー用
from ask_sdk_model.services import ServiceException
from ask_sdk_model.services.reminder_management import (
    ReminderRequest, Trigger, TriggerType, AlertInfo, PushNotification,
    PushNotificationStatus, ReminderResponse, AlertInfoSpokenInfo, SpokenText)
from ask_sdk_model.ui import SimpleCard, AskForPermissionsConsentCard

# リマインダーのパーミッション（Alexaの仕様）
REQUIRED_PERMISSIONS = ["alexa::alerts:reminders:skill:readwrite"]

# リマインダーする時間
# 札幌市はAM8:30までにごみを出すルールのため8時にリマインドする
# ユーザが時間指定できる機能は複雑になるので実装しない
remind_time = 'T08:00:00' # AM8:00

# 発話内容は直に書くと見づらくなるので別ファイルとした
# コードを見れば何を発話するかわかりやすいようにしたつもり
import json
json_open = open('./messages/messages.json', 'r')
msg = json.load(json_open)

# タイムゾーンとロケールの設定（デフォルトはUTC）
import datetime
import pytz
TIME_ZONE_ID = 'Asia/Tokyo'
LOCALE = 'ja-JP'
today = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).date()

# ごみ収集時間
time_limit = datetime.time(8,30) # 札幌市はAM8:30までにごみを出す

# ごみに関する情報を処理するクラス
from ward_calendarnumber import ComfirmWard,CalendarNumberInWard
from trashinfo import TrashInfo
trash_info = TrashInfo()

from ask_sdk.standard import StandardSkillBuilder
sb = StandardSkillBuilder(table_name="SapporoTrash", auto_create_table=False)

# 各インテントの処理
@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """スキル起動時"""
    """初期設定済の場合は今日のごみを教えてくれる（定型アクション向け）"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder
    user_info = handler_input.attributes_manager.persistent_attributes

    # 初期設定が終わっていないなら設定してもらう
    if not user_info:
        return (
            rb.speak(msg['guidance']).ask(msg['ward_you_live'])
            .set_card(SimpleCard(msg['initial_setting'], msg['ward_you_live']))
            .set_should_end_session(False).response
        )
    # （定型アクションで使えるように）初期設定済なら今日のごみを伝える
    else:
        today_str = str(today)
        collection_area = user_info['ward_calno']
        trash_name = trash_info.what_day(today_str, collection_area)

        if trash_name == '収集なし':
            speech_text = '今日は、ごみの収集はありません。'
        else:
            speech_text = f'今日は、{trash_name}、の収集日です。'

        return (
            rb.speak(speech_text)
            .set_card(SimpleCard("今日のごみ", trash_name))
            .response
        )


@sb.request_handler(can_handle_func=is_intent_name("SelectWardIntent"))
def select_ward_intent_handler(handler_input):
    """初期設定時に区を設定するためのインテント"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder
    slots = handler_input.request_envelope.request.intent.slots
    ward_is = slots['ward'].value
    user_info = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    # 初期設定済の場合は使い方のガイダンスを流す
    if 'ward_calno' in user_info:
        return (
            rb.speak(msg['what_or_when'])
            .set_card(SimpleCard(msg['talk_like_this'], msg['info']))
            .set_should_end_session(False).response
        )

    # 区の設定を保存しカレンダー番号の設定を促す
    # 区の存在チェック
    input_ward = ComfirmWard(str(ward_is))
    if input_ward.is_not_exist:
        return (
            rb.speak(msg['ward_you_live'])
            .set_card(SimpleCard(msg['initial_setting'], msg['ward_you_live']))
            .set_should_end_session(False).response
        )
    else:
        if ward_is == "白石区" or ward_is == "白石":
            # しらいし区と発話してしまうため
            session_attr['ward'] = 'しろ石区'
        else:
            session_attr['ward'] = ward_is

        session_attr['ward_name_alpha'] = input_ward.alpha_name

        return (
            rb.speak(msg['calendar_no']).ask(msg['ask_calendar_no'])
            .set_card(SimpleCard(msg['initial_setting'], msg['calendar_no']))
            .set_should_end_session(False).response
        )


@sb.request_handler(can_handle_func=is_intent_name("SelectCalendarIntent"))
def select_calendarno_intent_handler(handler_input):
    """初期設定時にカレンダー番号を設定するためのインテント"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder
    slots = handler_input.request_envelope.request.intent.slots
    number_is = slots['calendar_number'].value
    user_info = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes
    ward_kanji = session_attr['ward']
    ward_alpha = session_attr['ward_name_alpha']
    print(number_is)

    # 初期設定済の場合は使い方のガイダンスを流す
    if 'ward_calno' in user_info:
        return (
            rb.speak(msg['what_or_when'])
            .set_card(SimpleCard(msg['talk_like_this'], msg['info']))
            .set_should_end_session(False).response
        )

    # カレンダー番号を保存して最終確認を促す
    # カレンダー番号の存在チェック
    input_calendar_number = CalendarNumberInWard(ward_alpha)
    if input_calendar_number.is_not_exist(number_is):
        return (
            rb.speak(msg['req_correct_number']).ask(msg['ask_calendar_no'])
            .set_card(SimpleCard(msg['initial_setting'], msg['req_correct_number']))
            .set_should_end_session(False).response
        )
    else:
        speech_text = f"おすまいは{ward_kanji}、カレンダー番号は{number_is}番です。よろしいですか?"
        session_attr['ward_calno'] = ward_alpha + "-" + number_is
        session_attr['reminder'] = 'no'

        return (
            rb.speak(speech_text).ask(speech_text)
            .set_card(SimpleCard(msg['initial_setting'], msg['confirm']))
            .response
        )


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.YesIntent"))
def yes_intent_handler(handler_input):
    """AMAZON.YesIntentの処理"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder
    user_info = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    # 聞いたごみの次の収集日をリマインドするかユーザへ聞く
    # Alexaアプリでリマインダーを許可していなければ案内する
    if session_attr['reminder'] == 'wanna set':
        request_envelope = handler_input.request_envelope
        permissions = request_envelope.context.system.user.permissions
        # 許可されていない場合
        if not (permissions and permissions.consent_token):
            return (
                rb.speak(msg['req_reminder_permission'])
                .set_card(AskForPermissionsConsentCard(permissions=REQUIRED_PERMISSIONS))
                .response
            )

        # 許可されている場合はセット
        reminder_client = handler_input.service_client_factory.get_reminder_management_service()
        try:
            request_time = session_attr['next_time'] + remind_time
            reminder_client.create_reminder(
                reminder_request=ReminderRequest(
                    # 絶対時刻でリマインダー設定（例：6月1日の午後7時）
                    trigger=Trigger(
                        object_type=TriggerType.SCHEDULED_ABSOLUTE,
                        scheduled_time=request_time,
                        time_zone_id=TIME_ZONE_ID
                    ),
                    alert_info=AlertInfo(
                        spoken_info=AlertInfoSpokenInfo(
                            content=[SpokenText(
                                locale=LOCALE,
                                text=session_attr['trash_name'] + "の収集日です。"
                                )
                            ]
                        )
                    ),
                    # プッシュ通知する
                    push_notification=PushNotification(
                        status=PushNotificationStatus.ENABLED
                        )
                    )
                )
            return (
                rb.speak(msg['set_reminder'])
                .set_card(SimpleCard(msg['setting_done'], msg['reminder_info']))
                .response
            )
        except ServiceException as e:
            return (
                rb.speak(msg['error_occurred'])
                .set_card(SimpleCard(msg['failed'], msg['error_occurred']))
                .response
            )

    # 初期設定済の場合は使い方のガイダンスを流す
    if 'ward_calno' in user_info:
        return (
            rb.speak(msg['what_or_when'])
            .set_card(SimpleCard(msg['talk_like_this'], msg['info']))
            .set_should_end_session(False).response
        )

    # 初期設定完了
    if session_attr['ward_calno']:          
        # セッション情報をpersistentへ書き込み
        handler_input.attributes_manager.persistent_attributes = session_attr
        handler_input.attributes_manager.save_persistent_attributes()

        return (
            rb.speak(msg['configured'])
            .set_card(SimpleCard(msg['talk_like_this'], msg['info']))
            .set_should_end_session(False).response
        )
    else:
        return (
            rb.speak(msg['guidance'])
            .set_card(SimpleCard(msg['initial_setting'], msg['ward_you_live']))
            .set_should_end_session(False).response
        )


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.NoIntent"))
def no_intent_handler(handler_input):
    """AMAZON.NoIntentの処理"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder
    user_info = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    # リマインドはいらないというリクエストの時
    if session_attr['reminder'] == 'wanna set':
        speech_text = msg['understood']
        return rb.speak(speech_text).response

    # 初期設定が済んでいない場合はアトリビュートをクリアして設定ガイダンスを流す
    if not user_info:        
        session_attr['ward'] = ''
        session_attr['ward_name_alpha'] = ''
        session_attr['ward_calno'] = ''

        return (
            rb.speak(msg['guidance'])
            .set_card(SimpleCard(msg['initial_setting'], msg['ward_you_live']))
            .set_should_end_session(False).response
        )
    # どこにもつながらない「No」をキャッチしたら使い方のガイダンスを流す
    else:
        return (
            rb.speak(msg['what_or_when'])
            .set_card(SimpleCard(msg['talk_like_this'], msg['info']))
            .set_should_end_session(False).response
        )


@sb.request_handler(can_handle_func=is_intent_name("WhatTrashDayIntent"))
def help_intent_handler(handler_input):
    """指定日のごみを教えるインテント"""
    rb = handler_input.response_builder
    slots = handler_input.request_envelope.request.intent.slots
    date = slots['when'].value
    user_info = handler_input.attributes_manager.persistent_attributes
    listen_day = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    monthday = trash_info.japanese_date(listen_day)

    # 初期設定が終わっていないなら設定してもらう
    if not user_info:
        return (
            rb.speak(msg['guidance'])
            .set_card(SimpleCard(msg['initial_setting'], msg['ward_you_live']))
            .set_should_end_session(False).response
        )
    else:
        collection_area = user_info['ward_calno']
        trash_name = trash_info.what_day(date, collection_area)
        
        if trash_name == '収集なし':
            speech_text = 'ごみの収集はありません。'
        else:
            speech_text = f"{trash_name}の日です。"

            # 当日の収集時間を超えていたら一言付け加える
            now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()
            if listen_day == today and now > time_limit:
                speech_text += 'なお、' + msg['time_limit']

        return (
            rb.speak(speech_text)
            .set_card(SimpleCard(monthday, trash_name))
            .set_should_end_session(True).response
        )


@sb.request_handler(can_handle_func=is_intent_name("NextWhenTrashDayIntent"))
def help_intent_handler(handler_input):
    """聞いたごみを次の収集日を教えるインテント"""
    rb = handler_input.response_builder
    slots = handler_input.request_envelope.request.intent.slots
    trash_name = slots['trash'].value
    user_info = handler_input.attributes_manager.persistent_attributes
    session_attr = handler_input.attributes_manager.session_attributes

    # 初期設定が終わっていないなら設定してもらう
    if not user_info:          
        return (
            rb.speak(msg['guidance'])
            .set_card(SimpleCard(msg['initial_setting'], msg['ward_you_live']))
            .set_should_end_session(False).response
        )
    else:
        collection_area = user_info['ward_calno']
        day_obj = trash_info.next_day(trash_name, collection_area)
        next_trash_day = datetime.datetime.strptime(day_obj, '%Y-%m-%d').date()
        now = datetime.datetime.now(pytz.timezone(TIME_ZONE_ID)).time()
        official_trash_name = trash_info.official_name(trash_name)
        monthday = trash_info.japanese_date(next_trash_day)
        youbi = trash_info.japanese_dayoftheweek(next_trash_day)

        # 収集日が今日かつ収集時間を超えている or それ以外
        if next_trash_day == today and now > time_limit:
            speech_text = f"{official_trash_name}の収集日は今日ですが、収集時間を過ぎています。次は、"
        else:
            speech_text = f"{official_trash_name}は、"

        speech_text += f"{monthday}、{youbi}です。"

        # 収集日当日の朝にリマインドするかユーザへ聞く
        session_attr['reminder'] = 'wanna set'
        speech_text += msg['wanna_set']

        # リマインダー設定時に使うためセッションアトリビュートへ保存
        session_attr['trash_name'] = official_trash_name
        session_attr['next_time'] = next_trash_day

        return (
            rb.speak(speech_text)
            .set_card(SimpleCard(monthday, official_trash_name))
            .set_should_end_session(False).response
        )


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """AMAZON.HelpIntentの処理"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder

    return (
        rb.speak(msg['how_to_use'])
        .set_card(SimpleCard(msg['talk_like_this'], msg['info']))
        .set_should_end_session(False).response
    )


@sb.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """キャンセル処理"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder

    return rb.speak(msg['understood']).response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """セッション終了処理"""
    # type: (HandlerInput) -> Response
    rb = handler_input.response_builder

    return rb.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """例外処理"""
    # type: (HandlerInput, Exception) -> Response
    rb = handler_input.response_builder
    logger.error(exception, exc_info=True)
    rb.speak(msg['pardon']).ask(msg['pardon'])

    return handler_input.response_builder.response


handler = sb.lambda_handler()