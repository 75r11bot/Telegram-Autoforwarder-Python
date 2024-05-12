import os
import asyncio
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon import events

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API credentials and other parameters from environment variables
api_id = os.environ.get('APP_API_ID')
api_hash = os.environ.get('APP_API_HASH')
phone_number = os.environ.get('APP_YOUR_PHONE')
source_channel_id = os.environ.get('SOURCE_CHANNEL_ID')
destination_channel_id = os.environ.get('DESTINATION_CHANNEL_ID')

class MessageForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)

    async def list_chats(self):
        await self.client.connect()

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
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))

        # Resolve the source chat entity
        try:
            source_entity = await self.client.get_entity(int(source_channel_id))
        except ValueError:
            print(f"Cannot find any entity corresponding to {source_channel_id}")
            return

        # Define event handler for processing new messages in the source chat
        @self.client.on(events.NewMessage(chats=source_entity))
        async def message_handler(event):
            print("Received new message:", event.message.text)

            # Forward the message to the destination channel
            await self.client.forward_messages(destination_channel_id, event.message)

        # Start the event loop
        await self.client.run_until_disconnected()

async def main():
    forwarder = MessageForwarder(api_id, api_hash, phone_number)

    print("Choose an option:")
    print("1. List Chats")
    print("2. Forward New Messages")

    choice = input("Enter your choice: ")

    if choice == "1":
        await forwarder.list_chats()
    elif choice == "2":
        await forwarder.forward_new_messages()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())
