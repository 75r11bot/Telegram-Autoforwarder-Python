import os
import aiohttp
import asyncio
from dotenv import load_dotenv
import re
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Constants
RETRY_INTERVAL_MS = 10  # Retry interval for specific response codes in milliseconds
RATE_LIMIT_INTERVAL_MS = 500  # Interval to wait if rate limit is exceeded in milliseconds

# async def get_input(prompt, default=None):
#     if default is not None:
#         return default
#     else:
#         return input(prompt).strip()



# class MessageForwarder:
#     def __init__(self, api_id, api_hash, phone_number, source_channel_ids, destination_channel_id, user_password):
#         # Create the session directory if it doesn't exist
#         session_dir = 'sessions'
#         if not os.path.exists(session_dir):
#             os.makedirs(session_dir)

#         # Use a unique session name
#         unique_session_name = f"{session_dir}/session_{phone_number}_{uuid.uuid4()}"
#         session_path = os.path.join(session_dir, unique_session_name + '.session')
        
#         if os.path.exists(session_path):
#             os.remove(session_path)  # Remove old session file if it exists

#         self.api_id = api_id
#         self.api_hash = api_hash
#         self.phone_number = phone_number
#         self.source_channel_ids = source_channel_ids
#         self.destination_channel_id = destination_channel_id
#         self.user_password = user_password

#         self.client = TelegramClient(unique_session_name, api_id, api_hash)
#         self.connected = False

#     async def connect(self):
#         await self.client.connect()
#         self.connected = True

#     async def disconnect(self):
#         await self.client.disconnect()
#         self.connected = False

#     async def list_chats(self):
#         if not self.connected:
#             await self.connect()

#         if not await self.client.is_user_authorized():
#             await self.client.send_code_request(self.phone_number)
#             code = get_input('Enter the code: ').strip()
#             await self.client.sign_in(self.phone_number, code)

#         dialogs = await self.client.get_dialogs()
#         for dialog in dialogs:
#             print(f"Chat ID: {dialog.id}, Title: {dialog.title}")

#     async def forward_new_messages(self):
#         while True:
#             try:
#                 if not self.connected:
#                     await self.connect()

#                 async with self.client:
#                     source_entities = await asyncio.gather(*[self.client.get_entity(channel_id) for channel_id in self.source_channel_ids])
#                     source_channel_ids = [entity.id for entity in source_entities]

#                     @self.client.on(events.NewMessage(chats=source_channel_ids))
#                     async def message_handler(event):
#                         try:
#                             print(f"New message received: {event.message.text}")  # Debug statement
#                             await self.client.forward_messages(self.destination_channel_id, event.message)
#                             print(f"Message forwarded to {self.destination_channel_id}")  # Debug statement
#                             await process_bonus_code(apiEndpoints, event.message.text)
#                             print("process_bonus_code called successfully")  # Debug statement
#                         except Exception as e:
#                             print(f"An error occurred while processing the message: {e}")

#                     await self.client.run_until_disconnected()

#             except SessionPasswordNeededError:
#                 await self.client.sign_in(password=self.user_password)
#             except asyncio.CancelledError:
#                 print("CancelledError caught, disconnecting...")
#                 await self.disconnect()
#                 break
#             except Exception as e:
#                 print(f"An error occurred: {e}")
#                 print("Attempting to reconnect...")
#                 await asyncio.sleep(5)

# async def ping_endpoint(endpoint):
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(endpoint) as response:
#                 if response.status == 200:
#                     print(f"Endpoint {endpoint} is reachable.")
#                 else:
#                     print(f"Endpoint {endpoint} is not reachable. Status code: {response.status}")
#     except aiohttp.ClientError as e:
#         print(f"Error connecting to {endpoint}: {e}")

async def send_next_request(data_array, api_endpoint, headers):
    async def sleep(ms):
        await asyncio.sleep(ms / 1000)  # Convert milliseconds to seconds

    async with aiohttp.ClientSession() as session:
        for card_no in data_array:
            form_data = {
                'platformType': os.environ.get('PLATFORM_TYPE', '1'),
                'isCancelDiscount': 'F',
                'siteId': "1451470260579512322",
                'siteCode': "ybaxcf-4",
                'cardNo': card_no
            }

            headers['Token'] = os.environ.get('H25_TOKEN')

            try:
                async with session.post(
                    f"{api_endpoint}/cash/v/pay/generatePayCardV2",
                    data=form_data,
                    headers=headers
                ) as response:
                    try:
                        response_data = await response.json()
                        print("Response Body:", response_data)
                        if response_data.get('code') == 9999:
                            print("Response code is 9999. Retrying request...")
                            await sleep(RETRY_INTERVAL_MS)
                            continue  # Retry the request without incrementing card_no
                        elif response_data.get('code') == 10003:
                            print("Rate limit exceeded. Retrying after delay...")
                            await sleep(RATE_LIMIT_INTERVAL_MS)
                            continue  # Retry the request without incrementing card_no
                    except aiohttp.ContentTypeError:
                        text_response = await response.text()
                        print("Unexpected response content:", text_response)
                        print("Headers:", response.headers)
                        # Handle non-JSON response here
            except aiohttp.ClientError as error:
                print(f"Error sending request to API: {error}")
                # Implement additional error handling logic here if needed

async def mock_send_requests(endpoint, data_array):
    try:
        device_code = os.environ.get('DEVICE_CODE')
        source_domain = endpoint.replace("/api", "")
        h25_token = os.environ.get('H25_TOKEN')
        sign = os.environ.get('SIGN')

        headers = {
            'Accept': "application/json, text/plain, */*",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'Accept-Language': "th, en-US;q=0.9, en;q=0.8",
            'Cache-Control': "no-cache",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cookie': device_code,
            'Endpoint': source_domain,
            'Lang': "th-TH",
            'Language': "th-TH",
            'Origin': source_domain,
            'Pragma': "no-cache",
            'Referer': f"{source_domain}/",
            'Sec-Ch-Ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'Sec-Ch-Ua-Mobile': "?0",
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': "empty",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Site': "same-origin",
            'token': h25_token,
            'Sign': sign,
            'Timestamp': datetime.now().isoformat(),
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
        # Call the send_next_request function with the appropriate parameters
        await send_next_request(data_array, endpoint, headers)
    except Exception as error:
        print(f"Error: {error}")

# Define function to process bonus codes
async def process_bonus_code(apiEndpoints, text):
    codes = parse_message(text)
    numerical_regex = re.compile(r'^\d+$')
    filtered_codes = [code for code in codes if numerical_regex.match(code) and len(code) > 10]

    if filtered_codes:
        print("bonusCodeArray", filtered_codes)
        for endpoint in apiEndpoints:
            try:
                await mock_send_requests(endpoint, filtered_codes)
            except Exception as e:
                print(f"An error occurred: {e}")
    else:
        print("No valid bonus codes found:", filtered_codes)

# Define function to parse message
def parse_message(message):
    lines = message.strip().split("\n")
    codes = []

    for line in lines:
        numbers = line.strip().split()
        codes.extend(numbers)

    return codes