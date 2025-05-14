from typing import Any, Dict, List, Text
import re
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, FollowupAction, ActionExecuted, EventType
from rasa_sdk.executor import CollectingDispatcher
from pymongo import MongoClient
import requests
import google.generativeai as genai
import os

isOneTime = False

class ActionExtractMultipleSlots(Action):
    def name(self) -> Text:
        return "action_new_extract_multiple_slots"

    def run(self, dispatcher, tracker, domain):
        entities = tracker.latest_message.get("entities", [])
        slot_updates = []

        for ent in entities:
              
            if ent["entity"] == "name":
                slot_updates.append(SlotSet("name", ent["value"]))
            elif ent["entity"] == "location":
                slot_updates.append(SlotSet("location", ent["value"]))
            elif ent["entity"] == "email":
                slot_updates.append(SlotSet("email", ent["value"]))
            elif ent["entity"] == "phone_number":
                slot_updates.append(SlotSet("phone_number", ent["value"]))

        return slot_updates

# To update the slots with new slot values provided
class ActionUpdateUserInfo(Action):
    def name(self) -> str:
        return "action_update_user_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        last_user_message = tracker.latest_message.get("text", "").lower()

        name_match = re.search(r"change.*name.*to\s+(\w+)", last_user_message)
        email_match = re.search(r"change.*email.*to\s+([\w\.-]+@[\w\.-]+)", last_user_message)

        events = []
        if name_match:
            print("action_update_user_info - name")
            new_name = name_match.group(1).capitalize()
            events.append(SlotSet("name", new_name))
            dispatcher.utter_message(text=f"Sure, I've updated your name to {new_name}.")
        elif email_match:
            print("action_update_user_info - email")
            new_email = email_match.group(1)
            events.append(SlotSet("email", new_email))
            dispatcher.utter_message(text=f"Sure, I've updated your email to {new_email}.")
        else:
            print("action_update_user_info - ")
            dispatcher.utter_message(text="I didn't catch what you wanted to change.")

        return events
    
# To check if any of the slots is missing or not
class ActionCheckAllUserInfoSlotsFilled(Action):
    def name(self) -> Text:
        return "action_check_all_user_info_slots_filled"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        required_slots = ["name", "location", "phone_number", "email"]
        missing_slots = [slot for slot in required_slots if not tracker.get_slot(slot)]

        if missing_slots:
            print("action_check_all_user_info_slots_filled running")
            dispatcher.utter_message(
                text=f"It seems like some details are still missing. Let's complete them before moving ahead."
            )
        else:
            print("action_check_all_user_info_slots_filled running")
            dispatcher.utter_message(response="utter_user_info_received")
        
        return []
    
# Triggered when any location related information is given to the rasa
class ActionCheckLocationAndTriggerFlow(Action):
    def name(self):
        return "action_check_location_and_trigger_flow"

    def run(self, dispatcher, tracker, domain):
        location = tracker.get_slot("location")
        last_intent = tracker.latest_message["intent"].get("name")
        global isOneTime

        if location and isOneTime is False:
            isOneTime = True
            print("action_check_location_and_trigger_flow  - if - running")
            return [FollowupAction("action_rephrased_license_info")]
            
        else: 
            print("action_check_location_and_trigger_flow - else - running")
            return [FollowupAction("action_listen")]
        

# To handle the user input for multiple slot details at the same time
class ActionExtractMultipleSlots(Action):
    def name(self) -> Text:
        return "action_extract_multiple_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        latest_message = tracker.latest_message.get('text', '')
        
        events = []
        
        if not tracker.get_slot("name"):
            name_patterns = [
                r"(?:my name is|I am|I'm|call me)[^\w]+([A-Za-z\s]+)",
                r"([A-Za-z]+)[^\w]+(?:here|this side)"
            ]
            
            for pattern in name_patterns:
                matches = re.search(pattern, latest_message, re.IGNORECASE)
                if matches:
                    print("action_extract_multiple_slots - name running")
                    name = matches.group(1).strip()
                    events.append(SlotSet("name", name))
                    break
        
        if not tracker.get_slot("location"):
            location_patterns = [
                r"(?:live|stay|based|reside|from)[^\w]+(in|at)[^\w]+([A-Za-z\s]+)",
                r"(?:I'm from|I am from|my city is|my location is)[^\w]+([A-Za-z\s]+)"
            ]
            
            for pattern in location_patterns:
                matches = re.search(pattern, latest_message, re.IGNORECASE)
                if matches:
                    print("action_extract_multiple_slots - location running")
                    if len(matches.groups()) > 1:
                        location = matches.group(2).strip()
                    else:
                        location = matches.group(1).strip()
                    events.append(SlotSet("location", location))
                    break
        
        if not tracker.get_slot("phone_number"):
            phone_regex = r"\b\d{10,15}\b"
            phone_match = re.search(phone_regex, latest_message)

            if phone_match:
                print("action_extract_multiple_slots - phone_number running")
                events.append(SlotSet("phone_number", phone_match.group(0)))

        if not tracker.get_slot("email"):
            email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            email_matches = re.search(email_regex, latest_message)
            if email_matches:
                print("action_extract_multiple_slots - email running")
                events.append(SlotSet("email", email_matches.group(0)))    
        
        return events

# To check if the slots are already filled or not
class ActionCheckSlotFilled(Action):
    def name(self) -> Text:
        return "action_check_slot_filled"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        active_flow = tracker.active_loop.get('name') if tracker.active_loop else None

        if not active_flow:
            print("action_check_slot_filled running")
            return []

        step_to_slot = {
            "name": "name",
            "location": "location",
            "phone_number": "phone_number",
            "email": "email"
        }

        current_slot = step_to_slot.get(active_flow)

        if current_slot:
            slot_value = tracker.get_slot(current_slot)
            print(f"active_flow: {active_flow}, slot: {current_slot}, value: {slot_value}")

            if current_slot == "location" and slot_value and not tracker.get_slot("location_acknowledged"):

                print("Location filled for the first time, calling action_rephrased_license_info")
                return [
                    SlotSet("location_acknowledged", True),
                    FollowupAction("action_rephrased_license_info")
                ]

            if slot_value:
                dispatcher.utter_message(f"I already have your {current_slot}: {slot_value}.")
                return []

        return []

# Method to fetch user details(slots) form the MongoDB
class ActionFetchUserDetails(Action):
    def name(self) -> Text:
        return "action_fetch_user_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mongo_uri = "mongodb+srv://kashishsaxena:kgyHvfPT03F4lc1I@conversations.mxvtpaa.mongodb.net/?retryWrites=true&w=majority&appName=Conversations"
        db_name = "CreateEvent"
        collection_name = "conversations"

        sender_id = tracker.sender_id

        try:
            client = MongoClient(mongo_uri)
            db = client[db_name]
            collection = db[collection_name]

            tracker_data = collection.find_one({"sender_id": sender_id})

            if not tracker_data:
                dispatcher.utter_message(text="No user data found.")
                return []

            slots = tracker_data.get("slots", {})
            name = slots.get("name", "not provided")
            email = slots.get("email", "not provided")
            location = slots.get("location", "not provided")
            phone = slots.get("phone_number", "not provided")

            msg = (
                f"Here are your stored details:\n"
                f"Name: {name}\n"
                f"Location: {location}\n"
                f"Email: {email}\n"
                f"Phone Number: {phone}"
            )

            dispatcher.utter_message(text=msg)

        except Exception as e:
            dispatcher.utter_message(text=f"Error fetching details: {str(e)}")

        return []

# Method to search using Gemini about licencing information
class ActionRephrasedLicenseInfo(Action):
    def name(self) -> Text:
        return "action_rephrased_license_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            genai.configure(api_key="AIzaSyCujg5NiB3vSIn3qxbs7zjLeLKxInfvSi4")
        except KeyError:
            print("Please set the GEMINI_API_KEY environment variable.")

        name = tracker.get_slot("name") or "the user"
        location = tracker.get_slot("location") or "an unknown location"
        
        print("action_rephrased_license_info-running")

        prompt = f"""
        You are an AI assistant that helps users understand licensing procedures.
        The user is {name} from {location}. 
        Based on this, guide them through the common steps required to apply for a license in their location.
        Keep the response clear, helpful, and friendly.
        """

        print("Prompt to Ollama:", prompt)
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest') 
            response = model.generate_content(prompt)
            
            answer = response.text
            print("Gemini API response text:", answer)
            dispatcher.utter_message(text=answer)

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            
        # ollama model

        # try:
        #     response = requests.post(
        #         "http://127.0.0.1:11435/api/generate", 
        #         json={
        #             # "model": "llama3", 
        #             "model": "gemini-2.0-flash-exp",
        #             "prompt": prompt,
        #             "stream": False
                    
        #         },
        #         headers={
        #             "Authorization": f"Bearer AIzaSyCujg5NiB3vSIn3qxbs7zjLeLKxInfvSi4",
        #             "Content-Type": "application/json"
        #         },
        #     )

        #     if response.status_code == 200:
        #         data = response.json()
               
        #         answer = data.get("response", "I'm sorry, I couldn't generate a response.")
        #         print("Ollama response JSON:", answer)
        #         dispatcher.utter_message(text=answer)
        #     else:
        #         answer = "There was an issue reaching the AI model. Please try again later."
        #         dispatcher.utter_message(response="utter_license_info_with_ollama")
        # except Exception as e:
        #     print("Error calling Ollama:", e)
        #     answer = "Oops, something went wrong while generating your license info."

        #     dispatcher.utter_message(response="utter_license_info_with_ollama")

        return []



# # After the interrupted flow completes then resuming the last flow
# class ActionCompleteNewFlowAndResume(Action):
#     def name(self) -> Text:
#         return "action_complete_new_flow_and_resume"
    
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
#         interrupted_flow = tracker.get_slot("interrupted_flow")
        
#         events = [SlotSet("interrupted_flow", None)]
        
#         events.append(ActionExecuted("action_deactivate_loop"))
        
#         if interrupted_flow:
#             print("action_complete_new_flow_and_resume running")
#             events.append(ActionExecuted("action_activate_flow", {"flow": interrupted_flow}))
#             dispatcher.utter_message(f"Resuming the previous flow: {interrupted_flow}")
        
#         return events

# # To handle off the flow conversations
# class ActionInterruptAndStartNewFlow(Action):
#     def name(self) -> Text:
#         return "action_interrupt_and_start_new_flow"
    
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         print("action_interrupt_and_start_new_flow running")
#         current_flow = tracker.active_loop.get("name")
        
#         events = [SlotSet("interrupted_flow", current_flow)]
        
#         events.append(ActionExecuted("action_interrupt_flow"))
        
#         events.append(FollowupAction("action_activate_new_flow"))
        
#         return events

# # To activate new flow
# class ActionActivateNewFlow(Action):
#     def name(self) -> Text:
#         return "action_activate_new_flow"
    
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         print("action_activate_new_flow running")
#         return [ActionExecuted("action_activate_flow", {"flow": "new_flow_name"})]
    
