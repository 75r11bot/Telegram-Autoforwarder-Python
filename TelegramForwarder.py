import os
import asyncio
import random
from telethon.sync import TelegramClient

api_id = os.environ.get('APP_API_ID')
api_hash= os.environ.get('APP_API_HASH')
phone_number= os.environ.get('APP_YOUR_PHONE')
destination_channel_id = os.environ.get('DESTINATION_CHANNEL_ID')

class RandomNumberForwarder:
    def __init__(self, api_id, api_hash, phone_number, destination_channel_id):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.destination_channel_id = destination_channel_id
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)

    async def generate_and_forward(self):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))

        while True:
            # Generate a random number
            random_number = random.randint(1, 100)
            message = f"Random number generated: {random_number}"

            # Forward the random number to the destination channel
            await self.client.send_message(self.destination_channel_id, message)
            print("Random number forwarded:", random_number)

            # Add a delay before generating the next random number
            await asyncio.sleep(10)  # Adjust the delay time as needed

async def main():
    forwarder = RandomNumberForwarder(api_id, api_hash, phone_number, destination_channel_id)
    await forwarder.generate_and_forward()

# Start the event loop and run the main function
if __name__ == "__main__":
    asyncio.run(main())
