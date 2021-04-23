from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response


def generate_speech(handler_input, text, card_title, card_body, sessionend):
    if sessionend == 'no':
        return (
            handler_input.response_builder
            .speak(text)
            .set_card(SimpleCard(card_title, card_body))
            .set_should_end_session(False)
            .response
        )
    else:
        return (
            handler_input.response_builder
            .speak(text)
            .set_card(SimpleCard(card_title, card_body))
            .response
        )

if __name__ == '__main__':
    generate_speech()