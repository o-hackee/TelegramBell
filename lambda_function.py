# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import os

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractRequestInterceptor, \
    AbstractResponseInterceptor
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
import ask_sdk_core.utils as ask_utils
from ask_sdk_model import Slot, Intent, Response
from ask_sdk_model.dialog import ElicitSlotDirective
from pyrogram.errors import PhoneNumberUnoccupied, PhoneCodeInvalid, PhoneCodeExpired

from AlexaStorageHandler import AlexaStorageHandler
from PyrogramClient import PyrogramClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # DEBUG for interceptors


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        pyrogram_client = PyrogramClient(AlexaStorageHandler(handler_input.attributes_manager))

        if not pyrogram_client.get_is_authorized():
            handler_input.attributes_manager.session_attributes["proposed_step"] = "setup"
            speak_output = f"Hi from Telegram Bell. Let's setup your account. Are you ready?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )

        speak_output = f"Hi from Telegram Bell!"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class YesIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
            and ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attributes = handler_input.attributes_manager.session_attributes
        if session_attributes.get("proposed_step") == "setup":
            del session_attributes["proposed_step"]
            slots = {"phoneNumber": Slot(name="phoneNumber")}
            intent = Intent(name="PhoneNumberIntent", slots=slots)
            speak_output = "What is your phone number?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                .add_directive(ElicitSlotDirective(updated_intent=intent, slot_to_elicit="phoneNumber"))
                    .response
            )

        return handler_input.response_builder.speak("Something went wrong. Please start a new session").response


class PhoneNumberIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
            and ask_utils.is_intent_name("PhoneNumberIntent")(handler_input)
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        phone_number = handler_input.request_envelope.request.intent.slots.get("phoneNumber").value

        pyrogram_client = PyrogramClient(AlexaStorageHandler(handler_input.attributes_manager))
        try:
            phone_code_hash = pyrogram_client.send_code(phone_number)
        except PhoneNumberUnoccupied:
            return handler_input.response_builder.speak("This phone number is not registered in telegram").response

        handler_input.attributes_manager.session_attributes["phone_number"] = phone_number
        handler_input.attributes_manager.session_attributes["phone_code_hash"] = phone_code_hash
        slots = {"code": Slot(name="code")}
        intent = Intent(name="CodeIntent", slots=slots)
        speak_output = "Please provide a code sent to your phone"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .add_directive(ElicitSlotDirective(updated_intent=intent, slot_to_elicit="code"))
                .response
        )


class CodeIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
            and ask_utils.is_intent_name("CodeIntent")(handler_input)
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        code = handler_input.request_envelope.request.intent.slots.get("code").value
        session_attributes = handler_input.attributes_manager.session_attributes

        pyrogram_client = PyrogramClient(AlexaStorageHandler(handler_input.attributes_manager))
        try:
            pyrogram_client.sign_in(session_attributes["phone_number"], session_attributes["phone_code_hash"], code)
        except PhoneCodeInvalid:
            speak_output = "code is invalid"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .add_directive(ElicitSlotDirective(slot_to_elicit="code"))
                    .response
            )
        except PhoneCodeExpired:
            return handler_input.response_builder.speak("code expired").response
        except Exception:
            return CatchAllExceptionHandler().handle(handler_input, Exception("Exception during sign-in"))
        return handler_input.response_builder.speak("all set up!").ask("what do you want to send?").response


class LunchReadyIntentHandler(AbstractRequestHandler):
    """Handler for Lunch Ready Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("LunchReadyIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        pyrogram_client = PyrogramClient(AlexaStorageHandler(handler_input.attributes_manager))
        send_ret = pyrogram_client.send_message("обед готов")
        speak_output = "message is sent" if send_ret else "there was a problm sending a message"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .set_should_end_session(True)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class LoggingRequestInterceptor(AbstractRequestInterceptor):
    """Log the alexa requests."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug('----- REQUEST -----')
        logger.debug("{}".format(
            handler_input.request_envelope.request))


class LoggingResponseInterceptor(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug('----- RESPONSE -----')
        logger.debug("{}".format(response))


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = StandardSkillBuilder(
    table_name=os.environ.get("DYNAMODB_PERSISTENCE_TABLE_NAME"), auto_create_table=False)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(PhoneNumberIntentHandler())
sb.add_request_handler(CodeIntentHandler())
sb.add_request_handler(LunchReadyIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

#sb.add_global_request_interceptor(LoggingRequestInterceptor())
#sb.add_global_response_interceptor(LoggingResponseInterceptor())

lambda_handler = sb.lambda_handler()