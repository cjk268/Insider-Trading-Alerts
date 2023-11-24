import requests
from bs4 import BeautifulSoup
import smtplib
import os
from dotenv import load_dotenv
import datetime

# Loading email account information
load_dotenv()
my_email = os.getenv("my_email")
password = os.getenv("password")
send_address = os.getenv("send_address")

"""RECENT is a constant representing the maximum number of days considered recent for insider trades.
MIN_TRADE_SIZE is a constant representing the minimum trade size desired by the user.
Trades are filed in brackets, example 1K-5K
USE_MIN_RANGE is a 0/1 variable indicating whether the user wants to use the min or max in the range size"""

RECENT = 45  # Adjust the value as needed (in Days)
MIN_TRADE_SIZE = 5000  # Adjust the value as needed (in USD)
MIN_OR_MAX_RANGE = 1  # Set to 0 if the user wants to use min range, 1 if max range is wanted.

URL = "https://www.capitoltrades.com/trades"
HEADER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6"
}
TRADES_CHECKED_FILE = "trades_checked.txt"
filtered_trades = []


def extract_text(element, tag, class_name):
    found_element = element.find(tag, class_=class_name)
    return found_element.text if found_element else None


def convert_trade_size(size_range):
    if size_range is None:
        return "Returned None"
    # The first trade size option is <1K
    elif '<' in size_range:
        return [0, 1000]
    else:
        trade_size_list = []
        parts = size_range.split('–')
        suffix_to_multiplier = {'K': 1000, 'M': 1000000}
        for part in parts:
            # Extract the numeric part and suffix
            numeric_value = int(''.join(c for c in part if c.isdigit()))
            suffix = ''.join(c for c in part if c.isalpha())
            numeric_value *= suffix_to_multiplier[suffix]

            trade_size_list.append(numeric_value)
        return trade_size_list


def log_date(run_log, response):
    with open(run_log, mode="a") as log_file:
        log_file.write(f"Date ran: {datetime.datetime.now()}, Response: {response}\n")


def compose_email(trades):
    subject = "Alert: Insider trading criteria fit"
    # Construct the email body
    email_body = ""
    for i, trade in enumerate(trades):
        email_body += f"Trade #{i + 1}\n"
        email_body += f"Name: {trade['politician']}\n"
        email_body += f"Party: {trade['party']}\n"
        email_body += f"Trade issue: {trade['trade_issue']}\n"
        email_body += f"Ticker: {trade['trade_ticker']}\n"
        email_body += f"Filed after: {trade['filed_after']} days\n"
        email_body += f"Trade size: ${trade['trade_size'][0]} - ${trade['trade_size'][1]} USD\n"
        email_body += f"Trade link: {trade['trade_link']}\n\n"
    return 'Subject: {}\n\n{}'.format(subject, email_body)


response = requests.get(url=URL, headers=HEADER)
response.raise_for_status()
soup = BeautifulSoup(response.content, "html.parser")
trades_table = soup.find_all("tr", class_="q-tr")

# Logging times ran, for task scheduler
log_date("date_log.txt", response)

for trade in trades_table:
    # Getting trade ID
    trade_ID_find = trade.find("a", class_="entity-link entity-transaction more-link")
    if trade_ID_find:
        trade_ID_href = trade_ID_find.get('href')
        trade_ID = [c for c in trade_ID_href if c.isdigit()]
        trade_ID = ''.join(trade_ID)
        print(f"Evaluating trade: {trade_ID}")
        trade_link = f"https://www.capitoltrades.com{trade_ID_href}"
        with open(TRADES_CHECKED_FILE, mode="r") as file:
            ids_checked = file.read().splitlines()

            # Check if it has already been logged
            if trade_ID not in ids_checked:
                filed_after = extract_text(trade, "span", 'reporting-gap-tier--2')
                # Checking if value = None
                if filed_after:
                    # User input criteria for what trade they want alerted
                    trade_ticker = extract_text(trade, "span", "q-field issuer-ticker")
                    trade_size = extract_text(trade, "span", class_name="q-field trade-size")
                    trade_size = convert_trade_size(trade_size)

                    # User criteria checks
                    filed_after_criteria = int(filed_after) < RECENT
                    trade_size_criteria = trade_size[MIN_OR_MAX_RANGE] > MIN_TRADE_SIZE
                    trade_type_criteria = trade_ticker != "N/A"  # Only shows publicly traded stocks
                    if filed_after_criteria and trade_size_criteria and trade_type_criteria:
                        # Getting all other relevant information about trade
                        politician = extract_text(trade, "h3", "q-fieldset politician-name")
                        trade_issue = extract_text(trade, "h3", "q-fieldset issuer-name")
                        published = extract_text(trade, "div", "q-cell cell--pub-date")
                        transaction_type = extract_text(trade, "span", ["tx-type--buy", "tx-type--sell"])
                        party = extract_text(trade, "span", ["q-field party party--republican",
                                                             "q-field party party--democrat"])

                        with open(TRADES_CHECKED_FILE, mode="a") as file:
                            file.write(f"{trade_ID}\n")

                        filtered_trades.append({
                            'filed_after': filed_after,
                            'politician': politician,
                            'party': party,
                            'trade_issue': trade_issue,
                            'trade_ticker': trade_ticker,
                            'trade_size': trade_size,
                            'trade_ID': trade_ID,
                            'trade_link': trade_link
                        })
                    
# If there are filtered trades, send an email
if filtered_trades:
    message = compose_email(filtered_trades)
    connection = smtplib.SMTP("smtp.gmail.com", port=587)
    connection.starttls()  # Secures and encrypts message
    connection.login(user=my_email, password=password)
    connection.sendmail(from_addr=my_email, to_addrs=send_address, msg=message)
    print("Email sent")
    connection.close()
else:
    print("No trades today matched the criteria")