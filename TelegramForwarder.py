import os
import asyncio
from telethon.sync import TelegramClient

api_id = os.environ.get('APP_API_ID')
api_hash = os.environ.get('APP_API_HASH')
phone_number = os.environ.get('APP_YOUR_PHONE')
source_channel_id = os.environ.get('SOURCE_CHANNEL_ID')
destination_channel_id = os.environ.get('DESTINATION_CHANNEL_ID')
auth_code = os.environ.get('AUTH_CODE')

class MessageForwarder:
    def __init__(self, api_id, api_hash, phone_number, source_channel_id, destination_channel_id):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.source_channel_id = source_channel_id
        self.destination_channel_id = destination_channel_id
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)

    async def forward_messages(self):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            if auth_code:
                # Sign in with provided auth_code
                await self.client.sign_in(phone_number, code=auth_code)
            else:
                # Send code request and sign in
                result = await self.client.sign_in(phone_number)
                phone_code_hash = result.phone_code_hash  # Get phone_code_hash from result

                # Prompt user for the verification code
                verification_code = input('Enter the verification code: ')
                await self.client.sign_in(phone_number, code=verification_code, phone_code_hash=phone_code_hash)

        # Forward messages from source channel to destination channel
        async for message in self.client.iter_messages(int(self.source_channel_id)):
            # Forward the message
            await self.client.forward_messages(int(self.destination_channel_id), message)

async def main():
    forwarder = MessageForwarder(api_id, api_hash, phone_number, source_channel_id, destination_channel_id)
    await forwarder.forward_messages()

# Start the event loop and run the main function
if __name__ == "__main__":
    asyncio.run(main())
