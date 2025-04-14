#!/usr/bin/env python3

import json
import os
import requests
import shlex
import time


CURL_STRING = """
PASTE_CURL_STRING_HERE
"""

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
                    key, value = cookie.split("=")
                    cookies[key.strip()] = value.strip("'")

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "query_params": query_params
    }


def main():
    parsed_curl_dict = parse_curl_string_to_dict(CURL_STRING)
    cookies = parsed_curl_dict.pop("cookies")
    headers = parsed_curl_dict.pop("headers")
    url = parsed_curl_dict.pop("url")
    query_params = parsed_curl_dict.pop("query_params")

    while True:
        response = requests.get(url, headers=headers, cookies=cookies, params=query_params)

        try:
            if response.status_code == 401:
                print(f"Error: {response.status_code}")
                os.system('say "Reauthentication required."')
                break

            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                os.system(f'say "Error occurred. Got status code {response.status_code}"')
                break

            cookies.update(response.cookies.get_dict())

            data = response.json()

            print(f"Checking at: {data['responseTime']}")

            if "ScreenData" not in data:
                os.system('say "No hits found."')

            if "ScreenData" in data:
                os.system('say "Hit. Unusual options trading activity found."')
                print(data)

            # Wait 5 minutes
            time.sleep(300)


        except json.JSONDecodeError:
            print("Invalid JSON response")


if __name__ == "__main__":
    main()
