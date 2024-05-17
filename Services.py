import os
import aiohttp
import asyncio
from dotenv import load_dotenv
import re
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Constants
RETRY_INTERVAL_MS = 50  # Retry interval for specific response codes in milliseconds
RATE_LIMIT_INTERVAL_MS = 5000  # Interval to wait if rate limit is exceeded in milliseconds

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

            headers['Token'] = os.environ.get('H25_TOKEN1')

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
                            await asyncio.sleep(RATE_LIMIT_INTERVAL_MS / 1000) 
                            continue 
                        elif response_data.get('code') == 10003:
                            print("Rate limit exceeded. Retrying after delay...")
                            await asyncio.sleep(RATE_LIMIT_INTERVAL_MS / 1000) 
                            continue 
                        elif response_data.get('code') == 10140:
                            print("Token expired. Updating token and retrying request...")
                            headers['Token'] = os.environ.get('H25_TOKEN2')
                            await asyncio.sleep(RATE_LIMIT_INTERVAL_MS / 1000) 
                            continue 
                        else:
                            print("Request succeeded.")
                            # Handle successful request here if needed
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
        h25_token = os.environ.get('H25_TOKEN1')
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