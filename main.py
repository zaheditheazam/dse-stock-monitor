import os
import re
import requests
import pdfplumber
from bs4 import BeautifulSoup
from datetime import datetime


PDF_FILE = "portfolio.pdf"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")



# -----------------------------
# Extract Portfolio PDF
# -----------------------------

def extract_portfolio():

    stocks = []

    with pdfplumber.open(PDF_FILE) as pdf:

        text = ""

        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"


    lines = text.split("\n")


    for line in lines:

        match = re.search(
            r"([A-Z0-9]+)\s+[A-Z]\s+([\d,]+)\s+[\d,]+\s+([\d.]+)",
            line
        )


        if match:

            symbol = match.group(1)

            quantity = int(
                match.group(2).replace(",", "")
            )

            average = float(
                match.group(3)
            )


            stocks.append(
                {
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg": average
                }
            )


    return stocks




# -----------------------------
# DSE Current Price
# -----------------------------

def get_dse_price(symbol):

    try:

        url = (
            "https://www.dsebd.org/"
            "latest_share_price_scroll_l.php"
        )


        r = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":"Mozilla/5.0"
            }
        )


        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        text = soup.get_text(" ")


        pattern = (
            rf"{symbol}\s+([\d.]+)"
        )


        result = re.search(
            pattern,
            text
        )


        if result:

            return float(
                result.group(1)
            )


    except Exception as e:

        print(
            "Price error:",
            e
        )


    return None




# -----------------------------
# DSE News
# -----------------------------

def get_dse_news(stock_list):

    news = {}


    try:

        url = (
            "https://www.dsebd.org/"
            "display_news.php"
        )


        r = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":"Mozilla/5.0"
            }
        )


        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        text = soup.get_text("\n")


        for stock in stock_list:


            matches = []


            for line in text.split("\n"):


                if stock in line.upper():

                    if len(line.strip()) > 3:

                        matches.append(
                            line.strip()
                        )



            if matches:

                news[stock] = matches



    except Exception as e:

        print(
            "News error:",
            e
        )


    return news




# -----------------------------
# Telegram
# -----------------------------

def send_telegram(message):


    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )


    requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
    )





# -----------------------------
# Main
# -----------------------------

def main():


    print(
        "Loading Portfolio..."
    )


    portfolio = extract_portfolio()


    print(
        "Stocks Loaded:",
        len(portfolio)
    )


    symbols = [
        x["symbol"]
        for x in portfolio
    ]


    news = get_dse_news(
        symbols
    )



    message = (
        "📊 DSE Portfolio Monitor\n"
    )


    message += (
        datetime.now()
        .strftime("%d-%b-%Y %I:%M %p")
    )


    message += "\n\n"



    gain_more_than_5 = []



    for stock in portfolio:


        price = get_dse_price(
            stock["symbol"]
        )


        if price:


            investment = (
                stock["quantity"]
                *
                stock["avg"]
            )


            current_value = (
                stock["quantity"]
                *
                price
            )


            profit = (
                current_value
                -
                investment
            )


            gain_percent = (
                profit
                /
                investment
                *
                100
            )



            if gain_percent >= 5:


                gain_more_than_5.append(
                    {
                        "stock":stock["symbol"],
                        "avg":stock["avg"],
                        "current":price,
                        "gain":gain_percent
                    }
                )





    # Only show >5% gain stocks

    message += (
        "📈 Stocks Gain More Than 5%\n\n"
    )


    if gain_more_than_5:


        for x in sorted(
            gain_more_than_5,
            key=lambda a:a["gain"],
            reverse=True
        ):


            message += (
                f"{x['stock']}\n"
                f"Average: {x['avg']}\n"
                f"Current: {x['current']}\n"
                f"Gain: +{x['gain']:.2f}%\n\n"
            )


    else:


        message += (
            "No portfolio stock gained more than 5% today.\n"
        )




    # News

    message += (
        "\n📰 Portfolio News\n"
    )


    found = False


    for stock,items in news.items():


        found = True


        message += (
            f"\n{stock}\n"
        )


        for item in items[:3]:

            message += (
                "- "
                + item
                + "\n"
            )



    if not found:

        message += (
            "No portfolio stock news today.\n"
        )



    send_telegram(
        message
    )


    print(
        "Telegram Sent"
    )




if __name__ == "__main__":

    main()
