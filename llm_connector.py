import os
import json
import re  # Used for simple regex in simulation
from dotenv import load_dotenv

# Optional imports for real API only
try:
    from google import genai
    from google.genai import types
except ImportError:
    # Allows the script to run in simulation mode even if the SDK isn't installed
    pass

load_dotenv()
LLM_API_KEY = os.getenv("LLM_API_KEY")


class LLMConnector:
    """
    Manages all communication and logic for calling the LLM API.
    Handles switching between real and simulated modes and manages the LLM client state.
    """

    def __init__(self, use_real_llm=False, available_tools=None):
        # 1. State Configuration
        self.use_real_llm = use_real_llm
        self.available_tools = available_tools if available_tools is not None else []
        self._api_key = LLM_API_KEY
        self._client = None

        # 2. Initialize Real Client if running in real mode
        if self.use_real_llm:
            self._initialize_client()

    def _initialize_client(self):
        """Creates and stores the LLM client object once for efficiency."""
        if not self._api_key:
            print("🚨 Error: LLM_API_KEY is not set for real mode.")
            return

        try:
            # Note: The genai module must be imported successfully to proceed
            self._client = genai.Client(api_key=self._api_key)
            print("✅ LLM Client initialized successfully.")
        except Exception as e:
            print(f"🚨 Error initializing LLM Client: {e}")
            self._client = None

    # --- Private Method: Simulation Logic ---
    def _simulate_tool_call(self, user_query):
        """Handles the simulated logic path based on keyword matching."""
        print("🤖 **MODE: SIMULATED LLM** - Extracting arguments based on keyword matching.")

        query_lower = user_query.lower()

        # Check for 'search_kroger_products' intent
        if "price" in query_lower and ("zip" in query_lower or "area" in query_lower):

            # Simple parameter extraction for simulation
            search_term = next((word for word in ["milk", "bread", "coffee", "salmon"] if word in query_lower), "item")
            zip_match = re.search(r'\b\d{5}\b', user_query)
            zip_code = zip_match.group(0) if zip_match else "45040"

            print(f"SIMULATED LLM decided to call search_kroger_products (Term: {search_term}, Zip: {zip_code}).")
            return {
                "function_name": "search_kroger_products",
                "args": {
                    "search_term": search_term,
                    "zip_code": zip_code
                }
            }

        # Check for 'schedule_reminder' intent
        elif "reminder" in query_lower or "schedule" in query_lower:
            print("   SIMULATED LLM decided to call schedule_reminder.")
            return {
                "function_name": "schedule_reminder",
                "args": {
                    "task": "check flight",
                    "time": "tomorrow at 9 AM"
                }
            }

        return None

    # --- Private Method: Real API Logic ---
    def _call_real_llm(self, user_query):
        """Communicates with the actual LLM API for function calling."""
        print("🌐 **MODE: LLM API** - Sending query to Gemini...")

        if not self._client:
            print("🛑 Cannot call real LLM: Client is not initialized.")
            return None

            # Define the System Instruction (Grounding the Model)
        system_instruction = (
            "You are a helpful and versatile **Shopping Assistant**. "
            "Your primary goal is to **identify user intent** and respond appropriately. "
            "1. **Tool Use Priority:** If the user's request involves searching for a product price or scheduling a reminder, you MUST use the available tool functions. "
            "2. **General Knowledge Fallback:** If the user asks a general question (e.g., 'What is the capital of France?', 'How are you?'), answer the question directly, briefly, and politely using your general knowledge. "
            "3. **Concision:** Always be concise and directly address the user's query."
        )

        try:
            # Use the stored client and available_tools state
            tools = [{"function_declarations": self.available_tools}]

            response = self._client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=user_query,
                config=types.GenerateContentConfig(
                    tools=tools,
                    system_instruction=system_instruction
                )
            )
            #print(response)

            if response.function_calls:
                call = response.function_calls[0]
                print(f"   LLM decided to call {call.name}.")
                return {
                    "type": "tool_call",
                    "function_name": call.name,
                    "args": dict(call.args)
                }
            elif response.text:
                #print("   REAL LLM generated a text response.")
                return {
                    "type": "text_response",
                    "text": response.text
                }

            else:

                return None

        except Exception as e:
            print(f"🚨 Error communicating with REAL LLM API: {e}")
            return None

    def get_tool_call(self, user_query):
        """
        The main public interface to the LLM connector, acting as a router.
        """
        if self.use_real_llm:
            return self._call_real_llm(user_query)
        else:
            return self._simulate_tool_call(user_query)
