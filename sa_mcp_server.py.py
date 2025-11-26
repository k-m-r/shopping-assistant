import os
import json
import requests
from dotenv import load_dotenv
from llm_connector import LLMConnector
from kroger_api_connector import KrogerResourceClient


def display_results(results):
    """
    Formats and displays the final output to the user.
    """
    if not results:
        return

    print("\n--- 🛒 **Compare and Select** Assistant Results ---")
    # Simple table formatting for clear output
    for i, item in enumerate(results):
        # Check if a promotional price was found
        if item.get('PromoPrice') != 'N/A':
            price_output = f"PROMO: {item['PromoPrice']} (Reg: {item['Price']})"
        else:
            price_output = f"Price: {item['Price']}"

        print(f"**{i + 1}. {item['Name']}**")
        print(f"   {price_output:<30} | UPC: {item['UPC']}")
    print("----------------------------------------------------------")


def load_tool_schemas(filename="tools.json"):
    """
    Loads all tool schemas from a specified JSON file.
    This replaces the hardcoded schema list.
    """
    try:
        with open(filename, 'r') as f:
            schemas = json.load(f)
            print(f"✅ Loaded {len(schemas)} tool schemas from {filename}.")
            return schemas
    except FileNotFoundError:
        print(f"Error: Schema file '{filename}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON in '{filename}'. Check file format.")
        return []


if __name__ == "__main__":

    # Initial Configuration
    USE_REAL_LLM_FLAG = os.getenv("USE_REAL_LLM", "False").lower() == "true"
    ALL_AVAILABLE_TOOLS = load_tool_schemas()

    if not ALL_AVAILABLE_TOOLS:
        print("❌ MCP startup failed: Cannot load tools. Exiting.")
        exit()

    llm_connector = LLMConnector(
        use_real_llm=USE_REAL_LLM_FLAG,
        available_tools=ALL_AVAILABLE_TOOLS
    )

    kroger_client = KrogerResourceClient()

    print("\n--- ✅ MCP Server Ready ---")
    print(f"Mode: {'REAL LLM' if llm_connector.use_real_llm else 'SIMULATED LLM'}")
    print("Type 'exit' or 'quit' or 'bye' to close the application.")
    print("-----------------------------------")

    # --- 2. Interactive Input Loop (Runs Continuously) ---
    while True:
        try:
            # Get input from the user
            user_input = input("USER> ")

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nShutting down MCP server. Goodbye!")
                break

            if not user_input.strip():
                continue  # Skip if input is just whitespace

            print(f"**Query Received:** {user_input}")

            # Call the LLM Connector to determine intent
            function_call_info = llm_connector.get_tool_call(user_input)

            if function_call_info:
                function_name = function_call_info['function_name']
                args = function_call_info['args']

                print(f"\n🧠 MCP Dispatcher routing to function: **{function_name}**")
                print(f"Arguments extracted: {args}")

                # --- Dispatch Logic ---
                if function_name == "search_kroger_products":

                    search_term = args.get('search_term')
                    zip_code = args.get('zip_code')

                    if not search_term or not zip_code:
                        print("Missing required search parameters.")
                        continue

                    # get the nearest store
                    location_id = kroger_client.find_nearest_store(zip_code)

                    if kroger_client._access_token and location_id:
                        product_results = kroger_client.search_products(location_id, search_term)

                        print("\n--- Context Snippet for LLM (Model Context) ---")
                        display_results(product_results)
                    else:
                        print("❌ Resource Error: Failed to retrieve Kroger data.")

                elif function_name == "schedule_reminder":
                    print(f"📅 **MCP Action:** Scheduling reminder for '{args.get('task')}' at '{args.get('time')}'...")
                    print("   (This action would integrate with an external calendar/reminder service.)")

                else:
                    print(
                        f"⚠️ Error: Function '{function_name}' is defined in schema but not implemented in dispatcher.")

            else:
                print("🤖 LLM determined a general response is sufficient (No tool needed).")
                # In a real system, the LLM's text response would be printed here.

            print("\n-----------------------------------")

        except Exception as e:
            print(f"\n🚨 An unexpected error occurred: {e}")
            print("-----------------------------------")