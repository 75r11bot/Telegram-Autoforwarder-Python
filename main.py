import os
import aiohttp
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
import re
from Services import process_bonus_code

load_dotenv()

api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')
source_channel_ids = [
    int(os.environ.get('SOURCE_CHANNEL_ID')),
    int(os.environ.get('TELEGRAM_CHANNEL_ID')),
    int(os.environ.get('TEST_CHANNEL_ID'))
]
destination_channel_id = int(os.environ.get('DESTINATION_CHANNEL_ID'))
phone_number = os.environ.get('APP_YOUR_PHONE')
user_password = os.environ.get('APP_YOUR_PWD')
telegram_channel_id = int(os.environ.get('TELEGRAM_CHANNEL_ID'))


async def get_input(prompt, default=None):
    return default if default is not None else input(prompt).strip()

async def get_login_code(telegram_channel_id):
    async with TelegramClient('anon', api_id, api_hash) as client:
        async for message in client.iter_messages(telegram_channel_id, limit=1):
            text = message.text
            match = re.search(r"Login code: (\d+)", text)
            if match:
                return match.group(1)
            else:
                return None


class MessageForwarder:
    def __init__(self, api_id, api_hash, phone_number, source_channel_ids, destination_channel_id, user_password):
        # Create the session directory if it doesn't exist
        session_dir = 'sessions'
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)

        # Use a unique session name
        self.session_name = f"{session_dir}/session_{phone_number}"
        self.session_path = self.session_name + '.session'
        
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.source_channel_ids = source_channel_ids
        self.destination_channel_id = destination_channel_id
        self.user_password = user_password

        self.client = TelegramClient(self.session_name, api_id, api_hash)
        self.connected = False

    async def check_session_validity(self):
        try:
            if not self.client.is_connected():
                await self.client.connect()
            return await self.client.is_user_authorized()
        except Exception as e:
            print(f"An error occurred while checking session validity: {e}")
            return False

    async def connect(self):
        if os.path.exists(self.session_path):
            if not await self.check_session_validity():
                try:
                    os.remove(self.session_path)
                except PermissionError:
                    print("Unable to remove session file. Waiting for a moment and retrying...")
                    await asyncio.sleep(1)  # Wait for a short duration
                    try:
                        os.remove(self.session_path)  # Retry removing the file
                    except PermissionError:
                        print("Unable to remove session file even after retrying.")
                self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
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
            code = await get_login_code(telegram_channel_id) or await get_input('Enter the code: ')
            try:
                await self.client.sign_in(self.phone_number, code)
            except SessionPasswordNeededError:
                password = self.user_password or await get_input('Two-step verification is enabled. Please enter your password: ')
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
                            print(f"New message received: {event.message.text}")  
                            await self.client.forward_messages(self.destination_channel_id, event.message)
                            print(f"Message forwarded to {self.destination_channel_id}") 
                            await process_bonus_code(apiEndpoints, event.message.text)
                            print("process_bonus_code called successfully")  # Debug statement
                            # Call function to process bonus code here
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
                else:
                    print(f"Endpoint {endpoint} is not reachable. Status code: {response.status}")
    except aiohttp.ClientError as e:
        print(f"Error connecting to {endpoint}: {e}")

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
        choice = await get_input("Please enter the choice: ")
        if choice == "1":
            await forwarder.list_chats()
        elif choice == "2":
            try:
                await forwarder.forward_new_messages()
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("Invalid choice")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught, exiting...")
