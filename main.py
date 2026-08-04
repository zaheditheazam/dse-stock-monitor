
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
            text += page.extract_text() + "\n"


    lines = text.split("\n")


    for line in lines:

        # stock format example:
        # APEXFOOT A 420 420 210.27

        match = re.search(
            r"([A-Z0-9]+)\s+[A-Z]\s+([\d,]+)\s+[\d,]+\s+([\d.]+)",
            line
        )

        if match:

            symbol = match.group(1)

            qty = int(
                match.group(2).replace(",","")
            )

            avg = float(match.group(3))


            stocks.append(
                {
                    "symbol":symbol,
                    "quantity":qty,
                    "avg":avg
                }
            )


    return stocks



# -----------------------------
# DSE Price
# -----------------------------

def get_dse_price(symbol):

    try:

        url = f"https://www.dsebd.org/latest_share_price_scroll_l.php"

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


        text=soup.get_text(" ")

        pattern = rf"{symbol}\s+([\d.]+)"

        result=re.search(
            pattern,
            text
        )


        if result:
            return float(result.group(1))


    except Exception as e:
        print(e)


    return None



# -----------------------------
# DSE News
# -----------------------------

def get_dse_news(stock_list):

    news={}

    try:

        url="https://www.dsebd.org/display_news.php"

        r=requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":"Mozilla/5.0"
            }
        )


        soup=BeautifulSoup(
            r.text,
            "html.parser"
        )


        text=soup.get_text("\n")


        for stock in stock_list:

            matches=[]

            for line in text.split("\n"):

                if stock in line.upper():

                    matches.append(
                        line.strip()
                    )


            if matches:

                news[stock]=matches


    except Exception as e:

        print(e)


    return news




# -----------------------------
# Telegram
# -----------------------------

def send_telegram(message):

    url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"


    requests.post(
        url,
        data={
            "chat_id":TELEGRAM_CHAT_ID,
            "text":message
        }
    )





# -----------------------------
# Main
# -----------------------------


def main():


    print("Loading Portfolio...")


    portfolio=extract_portfolio()


    print(
        "Stocks Loaded:",
        len(portfolio)
    )


    symbols=[
        x["symbol"]
        for x in portfolio
    ]


    news=get_dse_news(symbols)



    message="📊 DSE Portfolio Monitor\n"
    message+=datetime.now().strftime(
        "%d-%b-%Y %I:%M %p"
    )
    message+="\n\n"



    gainers=[]
    losers=[]



    for stock in portfolio:


        price=get_dse_price(
            stock["symbol"]
        )


        if price:


            current=price

            investment=(
                stock["quantity"]
                *
                stock["avg"]
            )


            value=(
                stock["quantity"]
                *
                current
            )


            profit=value-investment


            percent=(
                profit/investment*100
            )



            if percent>=0:
                gainers.append(
                    (
                    stock["symbol"],
                    percent
                    )
                )

            else:
                losers.append(
                    (
                    stock["symbol"],
                    percent
                    )
                )


            message+=(
                f"{stock['symbol']}\n"
                f"Qty: {stock['quantity']}\n"
                f"Buy: {stock['avg']}\n"
                f"Current: {current}\n"
                f"P/L: {profit:,.2f} "
                f"({percent:.2f}%)\n\n"
            )




    message+="\n📰 Portfolio News\n"


    found=False


    for stock,items in news.items():

        found=True

        message+=f"\n{stock}\n"

        for n in items[:3]:

            message+=f"- {n}\n"


    if not found:

        message+="No portfolio stock news today.\n"



    message+="\n📈 Top Gainers\n"

    for x in sorted(
        gainers,
        key=lambda a:a[1],
        reverse=True
    )[:5]:

        message+=f"{x[0]} +{x[1]:.2f}%\n"



    message+="\n📉 Biggest Decliners\n"

    for x in sorted(
        losers,
        key=lambda a:a[1]
    )[:5]:

        message+=f"{x[0]} {x[1]:.2f}%\n"



    send_telegram(message)



    print("Telegram Sent")



if __name__=="__main__":

    main()
