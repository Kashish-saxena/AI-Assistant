from typing import Any, Dict, List, Text
import re
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.executor import CollectingDispatcher
import logging

from pymongo import MongoClient

# client = MongoClient("mongodb+srv://kashishsaxena:kgyHvfPT03F4lc1I@conversations.mxvtpaa.mongodb.net/?retryWrites=true&w=majority&appName=Conversations") 
# db = client["CreateEvent"]
# collection = db["conversations"]

EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$)")
PHONE_REGEX = re.compile(r"(^\d{10}$)")

class ActionValidateEmailFormat(Action):
    def name(self) -> Text:
        return "action_validate_email_format"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        email = tracker.get_slot("email")
        newEmail = tracker.get_slot("newEmail")
        print(f"[Action] Received email: {email}")

        if email and EMAIL_REGEX.match(email):
            print(f"[Action] ✅ Valid email provided: {email}")
            # if(newEmail==None):
            #     SlotSet("email", newEmail)
            return [SlotSet("email", newEmail),SlotSet("email_validated", True)]
        else:
            SlotSet("newEmail", None)
            return [SlotSet("email_validated", False),SlotSet("email", None)]
        
class ActionValidatePhoneNumberFormat(Action):
    def name(self) -> Text:
        return "action_validate_phone_number_format"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        phone_number = tracker.get_slot("phone_number")
        print(f"[Action] Received phone_number: {phone_number}")

        if phone_number and PHONE_REGEX.match(phone_number):
            print(f"[Action] ✅ Valid phone_number provided: {phone_number}")

            return [SlotSet("phone_number", phone_number),SlotSet("phone_number_validated", True)]
        else:
            dispatcher.utter_message(text="❌ Invalid phone number. Please provide a valid phone number.")
            return [SlotSet("phone_number", None),SlotSet("phone_number_validated", False)]
        
# def get_user_history(sender_id: str):
#     return collection.find_one({"sender_id": sender_id})


# class ActionGreetUser(Action):
#     def name(self) -> Text:
#         return "action_greet_user"

#     async def run(self, dispatcher, tracker, domain):
#         sender_id = tracker.sender_id
#         user_data = get_user_history(sender_id)
#         name = user_data.get("slots", {}).get("first_name", "there")

#         dispatcher.utter_message(text=f"Welcome back, {name}! How can I help you today?")
#         return []
    

# class ActionRestoreUserData(Action):
#     def name(self) -> Text:
#         return "action_restore_user_data"

#     async def run(self, dispatcher, tracker, domain):
#         sender_id = tracker.sender_id
#         user_data = get_user_history(sender_id)

#         slots = user_data.get("slots", {})
#         return [SlotSet(key, value) for key, value in slots.items() if value is not None]
