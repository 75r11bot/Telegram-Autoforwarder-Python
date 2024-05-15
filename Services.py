import aiohttp
import os
import re
import asyncio
import uuid
import random
import string
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def generate_site_identifiers():
    def generate_uuid():
        return str(uuid.uuid4())

    def generate_site_code(length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    return {
        'siteId': generate_uuid(),
        'siteCode': generate_site_code()
    }

async def send_next_request(data_array, token, api_endpoint, headers):
    async def sleep(ms):
        await asyncio.sleep(ms / 1000)

    async with aiohttp.ClientSession() as session:
        site_identifiers = generate_site_identifiers()
        print("site_identifiers : {site_identifiers}")
        for card_no in data_array:
            form_data = {
                'platformType': os.environ.get('PLATFORM_TYPE', '1'),
                'isCancelDiscount': 'F',
                'siteId': site_identifiers['siteId'],
                'siteCode': site_identifiers['siteCode'], 
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
                            await sleep(50)
                            continue  # Retry the request without incrementing i
                        elif response_data.get('code') == 10003:
                            print("Rate limit exceeded. Retrying after delay...")
                            await sleep(1000)  # Wait 1 second before retrying
                            continue  # Retry the request without incrementing i
                    except aiohttp.ContentTypeError:
                        text_response = await response.text()
                        print("Unexpected response content:", text_response)
                        print("Headers:", response.headers)
                        # Handle non-JSON response here
            except aiohttp.ClientError as error:
                print("Error sending request to API:", error)
                # Implement error handling logic here

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
            'Referer': source_domain + "/",
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
        await send_next_request(data_array, h25_token, endpoint, headers)
    except Exception as error:
        print("Error:", error)

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
