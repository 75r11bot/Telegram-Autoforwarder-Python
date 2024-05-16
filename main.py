import os
import aiohttp
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
from Services import process_bonus_code
import pytesseract
from PIL import ImageGrab
import re
import uuid

load_dotenv()

# Retrieve and validate API credentials and other parameters from environment variables
def get_env_variable(var_name, default=None):
    value = os.environ.get(var_name)
    if value is None:
        if default is None:
            raise ValueError(f"Environment variable {var_name} is not set")
        return default
    return value

api_id = int(get_env_variable('APP_API_ID'))
api_hash = get_env_variable('APP_API_HASH')
source_channel_ids = [
    int(get_env_variable('SOURCE_CHANNEL_ID')),
    int(get_env_variable('TEST_CHANNEL_ID')),
    int(get_env_variable('TELEGRAM_CHANNEL_ID'))
]
destination_channel_id = int(get_env_variable('DESTINATION_CHANNEL_ID'))
phone_number = get_env_variable('APP_YOUR_PHONE')
user_password = get_env_variable('APP_YOUR_PWD')

async def get_input(prompt, default=None):
    if default is not None:
        return default
    else:
        return input(prompt).strip()

async def get_login_code():
    # Take a screenshot
    screenshot = ImageGrab.grab()
    
    # Perform OCR on the screenshot
    text = pytesseract.image_to_string(screenshot)
    
    # Parse the text to find the login code
    pattern = r"Login code: (\d+)"
    match = re.search(pattern, text)
    if match:
        code = match.group(1)
        return code
    else:
        return None

class MessageForwarder:
    def __init__(self, api_id, api_hash, phone_number, source_channel_ids, destination_channel_id, user_password):
        # Create the session directory if it doesn't exist
        session_dir = 'sessions'
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)

        # Use a unique session name
        unique_session_name = f"{session_dir}/session_{phone_number}_{uuid.uuid4()}"
        session_path = os.path.join(session_dir, unique_session_name + '.session')
        
        if os.path.exists(session_path):
            os.remove(session_path)  # Remove old session file if it exists

        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.source_channel_ids = source_channel_ids
        self.destination_channel_id = destination_channel_id
        self.user_password = user_password

        self.client = TelegramClient(unique_session_name, api_id, api_hash)
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
            code = await get_input('Enter the code: ')
            try:
                await self.client.sign_in(self.phone_number, code)
            except SessionPasswordNeededError:
                password = await get_input('Two-step verification is enabled. Please enter your password: ')
                await self.client.sign_in(password=password)
            except Exception as e:
                print(f"An error occurred during sign-in: {e}")
                return

        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:
            print(f"Chat ID: {dialog.id}, Title: {dialog.title}")

    async def forward_new_messages(self):
        while True:
            try:
                if not self.connected:
                    await self.connect()

                async with self.client:
                    source_entities = await asyncio.gather(*[self.client.get_entity(channel_id) for channel_id in self.source_channel_ids])
                    source_channel_ids = [entity.id for entity in source_entities]

                    @self.client.on(events.NewMessage(chats=source_channel_ids))
                    async def message_handler(event):
                        try:
                            print(f"New message received: {event.message.text}")  # Debug statement
                            await self.client.forward_messages(self.destination_channel_id, event.message)
                            print(f"Message forwarded to {self.destination_channel_id}")  # Debug statement
                            await process_bonus_code(apiEndpoints, event.message.text)
                            print("process_bonus_code called successfully")  # Debug statement
                        except Exception as e:
                            print(f"An error occurred while processing the message: {e}")

                    await self.client.run_until_disconnected()

            except SessionPasswordNeededError:
                await self.client.sign_in(password=self.user_password)
            except asyncio.CancelledError:
                print("CancelledError caught, disconnecting...")
                await self.disconnect()
                break
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
        get_env_variable('API_ENDPOINT_1'),
        get_env_variable('API_ENDPOINT_2'),
        get_env_variable('API_ENDPOINT_3')
    ]

    tasks = [ping_endpoint(endpoint) for endpoint in api_endpoints]
    await asyncio.gather(*tasks)

    while True:
        print("Choose an option:")
        print("1. List Chats")
        print("2. Forward New Messages")
        choice = await get_input("Please enter the choice: ")
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught, exiting...")
