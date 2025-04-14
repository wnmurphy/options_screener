# Options screener

A script that takes a cURL string that executes an options screener you define in ETRADE, and then runs it every 5 minutes to fetch results.

## Setup

1. Have an existing ETRADE account.
1. Create a custom [Options Screener](https://us.etrade.com/e/t/optionanalytics/optionsscreener) in ETRADE or use an existing one.
1. Create `api_keys.py` in the same directory as this script.
1. Download [Pushover](https://pushover.net/) and create an account.
1. Register your device with Pushover (one-time $5 charge for a license).
1. Add your user key to `api_keys.py` as `PUSHOVER_USER_KEY`.
1. Register a new application with Pushover, and add the API key to `api_keys.py` as `PUSHOVER_API_KEY`.
1. Run `chmod +x options_screener.py` to make the script executable.
1. Create a new virtual environment and install the required packages:
   ```bash
   virtualenv .
   source bin/activate
   pip install -r requirements.txt
   ```

## Usage

1. Log in to ETRADE.
2. Go to [options screeners](https://us.etrade.com/e/t/optionanalytics/optionsscreener).
3. Open Dev Tools (CMD + i).
4. Click Scan.
5. Right-click the resulting call in the Network tab and select Copy > Copy as cURL (bash).
6. Paste the cURL string into the `CURL_STRING` variable in `api_keys.py`.
7. Run `./options_screener.py` to start the script.

The script will run your options screener and refresh your local session cookie every 5 minutes.

## Testing

Set the `TESTING` variable in `api_keys.py` to `True` to run the script in testing mode.

This will use a mock response to simulate the ETRADE API response and send push notifications.

## Example response structures

Screener returns results:

```json
{
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
```

Screener returned no results:

```json
{
    "responseTime": "April 13, 2025 00:54:12 AM EDT",
    "errorMessage": {
        "errorCode": "no_data_found",
        "errorMessage": "No data found. Please try again.",
        "detailedErrorMessage": "6916425938198937834"
    }
}
```

## References

* [ETRADE Options Screener](https://us.etrade.com/e/t/optionanalytics/optionsscreener)
* [Pushover](https://pushover.net/)
* [Pushover API documentation](https://pushover.net/api)
* [Options Profit Calculator](https://www.optionsprofitcalculator.com/calculator/long-call.html)
