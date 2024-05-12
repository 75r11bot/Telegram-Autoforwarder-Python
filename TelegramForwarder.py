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
auth_code = os.environ.get('AUTH_CODE')

class MessageForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)

    async def forward_messages_to_channel(self, source_chat_id, destination_channel_id, keywords):
        async def message_handler(event):
            # Check if the message is from the source chat
            if event.chat_id == source_chat_id:
                # Forward the message to the destination channel
                await self.client.forward_messages(destination_channel_id, event.message)

        # Add event handler for new messages in the source chat
        self.client.add_event_handler(message_handler, events.NewMessage)

        # Start the client
        await self.client.start()

async def main():
    forwarder = MessageForwarder(api_id, api_hash, phone_number)

    # Source and destination chat IDs
    source_chat_id = -1001836737719  # H25 THAILAND
    destination_channel_id = -4111321247  # H25-Bonus-Code

    # Forward messages from the source to the destination
    await forwarder.forward_messages_to_channel(source_chat_id, destination_channel_id, [])

if __name__ == "__main__":
    asyncio.run(main())
