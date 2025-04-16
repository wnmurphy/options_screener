#!/usr/bin/env python3

import json
import os
import re

import requests
import shlex
import time

from api_keys import (
    CURL_STRING,
    PUSHOVER_APP_TOKEN,
    PUSHOVER_USER_KEY,
)

TESTING = False

mock_response = {
    "responseTime": "April 13, 2025 17:04:34 PM EDT",
    "errorMessage": {
        "errorCode": "",
        "errorMessage": "",
        "detailedErrorMessage": ""
    },
    "ScreenData": {
        "screenid": 1,
        "underliercount": 149,
        "optionscount": 1000,
        "symbollist": [
            "CMPX",
            "CHPT"
        ],
        "underlierSortColumn": "iv30",
        "underlierSortDir": "DESC",
        "optionSortColumn": "tvalx",
        "optionSortDirection": "DESC",
        "underlierLimitReached": "N",
        "securityType": "EQ",
        "underliers": [
            {
                "symbol": "CMPX",
                "price": "1.695",
                "vol": "574,697",
                "avovol": "10,246.433",
                "iv30": "216.194",
                "underlying.trade.price": "1.695",
                "underlying.trade.time": "1744401600180",
                "options": [
                    {
                        "symbol": "CMPX--250417C00004000",
                        "displaySymbol": "CMPX Apr 17 '25 $4 Call",
                        "trade.price": "0.05",
                        "trade.time": "1744378206672",
                        "ovol": "120",
                        "ooi": "18,046",
                        "otype": "CALL",
                        "ask": "0.05",
                        "bid": "0",
                        "strp": "4",
                        "strm": "2.381",
                        "tvalx": "100",
                        "exp": "3"
                    }
                ]
            },
            {
                "symbol": "CHPT",
                "price": "0.60",
                "vol": "8,264,233",
                "avovol": "4,166.342",
                "iv30": "199.651",
                "underlying.trade.price": "0.6057",
                "underlying.trade.time": "1744412400001",
                "options": [
                    {
                        "symbol": "CHPT--250509C00001000",
                        "displaySymbol": "CHPT May 09 '25 $1 Call",
                        "trade.price": "0.01",
                        "trade.time": "1744380198521",
                        "ovol": "249",
                        "ooi": "611",
                        "otype": "CALL",
                        "ask": "0.05",
                        "bid": "0",
                        "strp": "1",
                        "strm": "1.664",
                        "tvalx": "100",
                        "exp": "25"
                    }
                ]
            }
        ]
    }
}


def parse_curl_string_to_dict(curl_string):
    lines = shlex.split(curl_string)
    lines = [" ".join(lines[i:i+2]) for i in range(0, len(lines), 2)]

    url = None
    query_params = {}
    headers = {}
    cookies = {}

    # Extract the URL, headers, cookies, and query parameters
    for line in lines:
        if line.startswith("curl"):
            url_and_query_params = line.split(" ")[1].strip("'")
            url, query_string = url_and_query_params.split("?")
            for param in query_string.split("&"):
                key, value = param.split("=")
                query_params[key] = value.strip("'")
        elif line.startswith("-H"):
            header = line[3:].split(": ")
            headers[header[0]] = header[1].strip("'")
        elif line.startswith("-b"):
            cookie_string = line[3:].split(";")
            for cookie in cookie_string:
                if "=" in cookie:
                    key, value = cookie.split("=", 1)
                    cookies[key.strip()] = value.strip("'")

    headers["action"] = "retrieveScreenPrefillData"

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "query_params": query_params
    }

def clean_int(val):
    val = str(val).strip()
    if not val or val in ['--', 'NaN']:
        return 0
    try:
        return int(re.sub(r'[^\d]', '', val))  # removes commas and non-digits
    except ValueError:
        return 0

def clean_float(val):
    val = str(val).strip()
    if not val or val in ['--', 'NaN']:
        return 0.0
    try:
        return float(re.sub(r'[^\d.\-]', '', val))
    except ValueError:
        return 0.0

# Returns a boolean of whether this qualifying option meets additional criteria.
def is_high_quality_hit(opt, underlying_price):
    # Parse values
    trade_price = clean_float(opt['trade.price'])
    ask_price = clean_float(opt['ask'])
    strike = clean_float(opt['strp'])
    volume = clean_int(opt['ovol'])
    open_interest = clean_int(opt['ooi']) if 'ooi' in opt else 0
    dte = clean_int(opt['exp'])

    # Total price paid for the position.
    opt['total_premium'] = trade_price * clean_int(opt['ovol']) * 100
    # Format as currency
    opt['total_premium'] = f"${opt['total_premium']:.2f}"

    # Derived metrics
    oi_ratio = volume / open_interest if open_interest > 0 else 0

    # How "out of the money" is this option?
    if opt['otype'] == "CALL":
        otm_percent = (strike - underlying_price) / underlying_price # calls
    else:
        otm_percent = (underlying_price - strike) / underlying_price # puts
    opt['otm_percent'] = f"{otm_percent:.2%}"

    ask_fill = trade_price >= 0.90 * ask_price  # near ask = aggressive buy

    return (
        oi_ratio >= 1.5 if oi_ratio else True and
        trade_price < 1.00 and
        otm_percent <= 0.05 and
        dte <= 8 and
        ask_fill
    )


# Parses the dict for a hit into a short string message for notification.
def format_msg_from_hit(hit):
    return f"{hit['opt']}\ncurrent_share_price: {hit['sh_pr']}\notm_percentage: {hit['otm_perc']}\ndays_to_exp: {hit['exp']}\ntrade_price: {hit['trade_price']}\ntotal_cost: {hit['t_prm']}\ntotal_size: {hit['ovol']}\nhq_hit: {hit['hq_hit']}"


# Sends a push notification for a given message.
def send_sms_notification(msg):
    print(f"Sending notification for: {msg}")
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_APP_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": msg,
        "priority": 1,
    }
    response = requests.post(url, data=data)
    status_code_to_message = {
        200: "Notification sent successfully.",
        401: "Invalid access token.",
        403: "Invalid device ID.",
        429: "Rate limit exceeded.",
    }
    if response.status_code in status_code_to_message:
        print(status_code_to_message[response.status_code])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def send_notifications_for_hits(list_of_hits):
    print(f"Sending notifications for {len(list_of_hits)} hits...")
    print(list_of_hits)
    for hit in list_of_hits:
        msg = format_msg_from_hit(hit)
        send_sms_notification(msg)
        time.sleep(5)


def main():
    parsed_curl_dict = parse_curl_string_to_dict(CURL_STRING)
    cookies = parsed_curl_dict.pop("cookies")
    headers = parsed_curl_dict.pop("headers")
    url = parsed_curl_dict.pop("url")
    query_params = parsed_curl_dict.pop("query_params")

    while True:
        if not TESTING:
            response = requests.get(url, headers=headers, cookies=cookies, params=query_params)

            if response.status_code == 401:
                print(f"Error: {response.status_code}")
                os.system('say "Re-authentication required."')
                break

            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                os.system(f'say "Error occurred. Got status code {response.status_code}"')
                break

            cookies.update(response.cookies.get_dict())

        try:
            data = mock_response if TESTING else response.json()
        except json.JSONDecodeError:
            print("Invalid JSON response")
            break

        print(f"Checking for hits at: {data['responseTime']}")

        if "ScreenData" not in data:
            os.system('say "No hits found."')

        if "ScreenData" in data:
            os.system('say "Unusual options trading activity found."')
            print(data)

            list_of_hits = data.get("ScreenData", {}).get("underliers", [])

            parsed_hits = []
            for hit in list_of_hits:
                underlying_price = clean_float(hit.get("price"))
                for option in hit.get("options", []):

                    # Filter out options in the chain with no volume; irrelevant.
                    if not clean_int(option["ovol"]):
                        continue

                    # Filter out anything that isn't "buying to open"; irrelevant.
                    trade_price_higher_than_ask = clean_float(option["trade.price"]) >= clean_float(option["ask"])
                    trade_volume_higher_than_oi = clean_int(option["ovol"]) > clean_int(option["ooi"])
                    if not trade_price_higher_than_ask and not trade_volume_higher_than_oi:
                        continue

                    parsed_hits.append({
                        "opt": option["displaySymbol"],
                        "ovol": option["ovol"],
                        "sh_pr": hit.get("price"),
                        "exp": option.get("exp"),
                        "hq_hit": is_high_quality_hit(option, underlying_price),
                        "t_prm": option.get("total_premium", 0),
                        "trade_price": option.get("trade.price", 0),
                        "otm_perc": option.get("otm_percent", 0),
                    })

            send_notifications_for_hits(parsed_hits)

        # Wait 5 minutes
        time.sleep(300)


if __name__ == "__main__":
    main()
