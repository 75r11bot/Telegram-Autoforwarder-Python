import os
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API credentials and other parameters from environment variables
api_id = os.environ.get('APP_API_ID')
api_hash = os.environ.get('APP_API_HASH')
phone_number = os.environ.get('APP_YOUR_PHONE')
source_channel_id = os.environ.get('SOURCE_CHANNEL_ID')
destination_channel_id = os.environ.get('DESTINATION_CHANNEL_ID')
user_password = os.environ.get('APP_YOUR_PWD')

class MessageForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session/session_' + phone_number, api_id, api_hash)
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
            await self.client.sign_in(self.phone_number, input('Enter the code: '))

        # Get a list of all the dialogs (chats)
        dialogs = await self.client.get_dialogs()

        # Print information about each chat
        for dialog in dialogs:
            print(f"Chat ID: {dialog.id}, Title: {dialog.title}")

    async def forward_new_messages(self):
        # Connect if not already connected
        if not self.connected:
            await self.connect()

        # Ensure you're authorized
        try:
            if not await self.client.is_user_authorized():
                await self.client.send_code_request(self.phone_number)
                # Get code from user input
                code = input('Enter the code: ')
                # Log in with code
                await self.client.sign_in(self.phone_number, code)
        except SessionPasswordNeededError:
            # The session requires a password for authorization
            password = user_password
            try:
                # Try logging in with password
                await self.client.sign_in(password=password)
            except SessionPasswordNeededError:
                # Handle incorrect password
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

            # Forward the message to the destination channel
            await self.client.forward_messages(destination_channel_id, event.message)

        # Start the event loop
        await self.client.run_until_disconnected()

async def main():
    forwarder = MessageForwarder(api_id, api_hash, phone_number)

    while True:
        print("Choose an option:")
        print("1. List Chats")
        print("2. Forward New Messages")
        choice = input("Enter your choice: ")

        if choice == "1":
            await forwarder.list_chats()
        elif choice == "2":
            try:
                await forwarder.forward_new_messages()
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Attempting to reconnect...")
                await forwarder.disconnect()
        else:
            print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())
