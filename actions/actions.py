from typing import Any, Dict, List, Text
import re
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.executor import CollectingDispatcher
import logging

from pymongo import MongoClient

client = MongoClient("mongodb+srv://kashishsaxena:kgyHvfPT03F4lc1I@conversations.mxvtpaa.mongodb.net/?retryWrites=true&w=majority&appName=Conversations") 
db = client["CreateEvent"]
collection = db["conversations"]

EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$)")

class ActionValidateEmailFormat(Action):
    def name(self) -> str:
        return "action_validate_email_format"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: dict) -> list:

        email = tracker.get_slot("email")
        if email and EMAIL_REGEX.match(email):
            dispatcher.utter_message(response="utter_user_info_received")
            return [SlotSet("email_validated", True)]
        else:
            dispatcher.utter_message(text="Hmm, that doesn't look like a valid email. Can you try again?")
            return [SlotSet("email_validated", False)]


def get_user_history(sender_id: str):
    return collection.find_one({"sender_id": sender_id})


class ActionGreetUser(Action):
    def name(self) -> Text:
        return "action_greet_user"

    async def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        user_data = get_user_history(sender_id)
        name = user_data.get("slots", {}).get("first_name", "there")

        dispatcher.utter_message(text=f"Welcome back, {name}! How can I help you today?")
        return []
    

class ActionRestoreUserData(Action):
    def name(self) -> Text:
        return "action_restore_user_data"

    async def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        user_data = get_user_history(sender_id)

        slots = user_data.get("slots", {})
        return [SlotSet(key, value) for key, value in slots.items() if value is not None]

# class ActionCheckSufficientFunds(Action):
#     def name(self) -> Text:
#         return "action_check_sufficient_funds"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         # hard-coded balance for tutorial purposes. in production this
#         # would be retrieved from a database or an API
#         balance = 1000
#         transfer_amount = tracker.get_slot("amount")
#         has_sufficient_funds = transfer_amount <= balance
#         return [SlotSet("has_sufficient_funds", has_sufficient_funds)]

# class ActionUpdateEventDetail(Action):
#     def name(self) -> Text:
#         return "action_update_event_detail"

#     async def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         attribute_to_change = tracker.get_slot("attribute_to_change")
#         new_time = tracker.get_slot("new_time")
#         new_venue = tracker.get_slot("new_venue")
#         new_date = tracker.get_slot("new_date")
#         new_name = tracker.get_slot("new_name")

#         updated_event = {}

#         if attribute_to_change == "time" and new_time:
#             updated_event["time"] = new_time
#             dispatcher.utter_message(text=f"Okay, I've changed the event time to {new_time}.")
#         elif attribute_to_change == "venue" and new_venue:
#             updated_event["venue"] = new_venue
#             dispatcher.utter_message(text=f"Alright, the event venue is now {new_venue}.")
#         elif attribute_to_change == "date" and new_date:
#             updated_event["date"] = new_date
#             dispatcher.utter_message(text=f"Got it, the event date is updated to {new_date}.")
#         elif attribute_to_change == "name" and new_name:
#             updated_event["name"] = new_name
#             dispatcher.utter_message(text=f"The event name has been changed to {new_name}.")
#         else:
#             dispatcher.utter_message(text="Sorry, I couldn't understand what you wanted to change.")
#             return []

#         # Here you would also update your stored event data (e.g., in a database)
#         print(f"Updated event details: {updated_event}")

#         return [SlotSet("attribute_to_change", None),  # Reset the attribute slot
#                 SlotSet("new_time", None),
#                 SlotSet("new_venue", None),
#                 SlotSet("new_date", None),
#                 SlotSet("new_name", None)]