# CapitolTrades Scraper

CapitolTrades Scraper is a Python script that scrapes insider trading information from [CapitolTrades](https://www.capitoltrades.com/) and sends email alerts based on specified criteria.

## Features

- Fetches insider trades data from CapitolTrades website.
- Checks specified criteria (recent days, trade size, etc.) to filter relevant trades.
- Sends email alerts when insider trades meet the criteria.

## Prerequisites

- Python 3
- Required Python packages (install using `pip install -r requirements.txt`)
  - requests
  - beautifulsoup4
  - smtplib (standard library)
  - dotenv

## Setup

1. Clone the repository:
   git clone https://github.com/cjk268/Insider-Trading-Alerts.git

2. Navigate to the project directory:

    cd Insider-Trading-Alerts

3. Install the required packages:
    pip install -r requirements.txt

4. Set up your environment variables:
    Create a .env file in the project directory and add the following:
    my_email=your_email@gmail.com
    password=your_email_password
    send_address=desired_send_email_address

5. Run the script:
    python main.py

## Configuration
Adjust the constants in the script to customize the criteria for insider trades:

RECENT: Maximum number of days considered recent for insider trades.
MIN_TRADE_SIZE: Minimum trade size desired by the user (in USD).
MIN_OR_MAX_RANGE: 0/1 variable indicating whether to use the min or max in the range size.
