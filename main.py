import os
import aiohttp
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
import re
import sys
from Services import process_bonus_code

load_dotenv()

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
source_channel_id = int(os.getenv('SOURCE_CHANNEL_ID'))
destination_channel_id = int(os.getenv('DESTINATION_CHANNEL_ID'))
phone_number = os.getenv('APP_YOUR_PHONE')
user_password = os.getenv('APP_YOUR_PWD')
telegram_channel_id = int(os.getenv('TELEGRAM_CHANNEL_ID'))
default_choice = os.getenv("USER_CHOICE", "2")

apiEndpoints = []

def is_interactive():
    return sys.stdin.isatty()

async def get_input(prompt, default=None, timeout=30):
    if not is_interactive():
        return default
    try:
        return await asyncio.wait_for(asyncio.to_thread(input, prompt), timeout)
    except asyncio.TimeoutError:
        return default

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
    def __init__(self, api_id, api_hash, phone_number, source_channel_id, destination_channel_id, user_password):
        session_dir = 'sessions'
        os.makedirs(session_dir, exist_ok=True)

        self.session_name = f"{session_dir}/session_{phone_number}"
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.source_channel_id = source_channel_id
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
        if os.path.exists(self.session_name + '.session'):
            if not await self.check_session_validity():
                try:
                    os.remove(self.session_name + '.session')
                except PermissionError:
                    print("Unable to remove session file. Retrying...")
                    await asyncio.sleep(1)
                    try:
                        os.remove(self.session_name + '.session')
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
            code = await get_input('Enter the code: ', default=await get_login_code(telegram_channel_id), timeout=30)
            try:
                await self.client.sign_in(self.phone_number, code)
            except SessionPasswordNeededError:
                password = await get_input("Two-step verification is enabled. Please enter your password: ", default=self.user_password, timeout=30)
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
                    source_entity = await self.client.get_entity(self.source_channel_id)

                    @self.client.on(events.NewMessage(chats=source_entity.id))
                    async def message_handler(event):
                        try:
                            print(f"New message received: {event.message.text}")
                            await self.client.forward_messages(self.destination_channel_id, event.message)
                            print(f"Message forwarded to {self.destination_channel_id}")
                            await process_bonus_code(apiEndpoints, event.message.text)
                            print("process_bonus_code called successfully")
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

async def main():
    forwarder = MessageForwarder(api_id, api_hash, phone_number, source_channel_id, destination_channel_id, user_password)
    api_endpoints = [
        os.getenv('API_ENDPOINT_1'),
        os.getenv('API_ENDPOINT_2'),
        os.getenv('API_ENDPOINT_3')
    ]

    tasks = [ping_endpoint(endpoint) for endpoint in api_endpoints if endpoint]
    await asyncio.gather(*tasks)

    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="H25, Telegram New Message forwarded to Bonus Code Gruup And Sending Request to called Api"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

    print("======= Serving on http://0.0.0.0:8000/ ======")

    while True:
        await asyncio.sleep(1500)
        choice = await get_input("Please enter the choice (1 to list chats, 2 to forward messages): ", default=default_choice, timeout=30)

        if choice == "1":
            await forwarder.list_chats()
        elif choice == "2":
            try:
                await forwarder.forward_new_messages()
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("Invalid choice, please enter 1 or 2.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught, exiting...")
