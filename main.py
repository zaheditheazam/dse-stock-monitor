import os
import re
import requests
import pdfplumber
from bs4 import BeautifulSoup
from datetime import datetime


PDF_FILE = "portfolio.pdf"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")



# =====================================
# READ STOCK + AVERAGE COST FROM PDF
# =====================================

def extract_portfolio():

    portfolio = []


    with pdfplumber.open(PDF_FILE) as pdf:

        full_text = ""

        for page in pdf.pages:

            txt = page.extract_text()

            if txt:
                full_text += txt + "\n"



    lines = full_text.split("\n")



    for line in lines:


        # Example:
        # FORTUNE 5700 16.44

        match = re.search(
            r"([A-Z0-9]+)\s+[\d,]+\s+([\d]+\.[\d]+)",
            line
        )


        if match:


            stock = match.group(1).upper()


            avg = float(
                match.group(2)
            )


            portfolio.append(
                {
                    "stock": stock,
                    "average": avg
                }
            )



    return portfolio





# =====================================
# GET LATEST DSE PRICE
# =====================================

def get_dse_price(stock):


    try:


        url = (
            "https://www.dsebd.org/"
            "latest_share_price_scroll_l.php"
        )


        response = requests.get(

            url,

            headers={
                "User-Agent":
                "Mozilla/5.0"
            },

            timeout=30
        )



        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )



        tables = soup.find_all("table")



        for table in tables:


            rows = table.find_all("tr")



            for row in rows:


                columns = [

                    c.get_text(
                        " ",
                        strip=True
                    )

                    for c in row.find_all("td")

                ]



                if len(columns) > 3:


                    code = columns[1].strip().upper()



                    if code == stock.upper():


                        price = (
                            columns[2]
                            .replace(",","")
                        )


                        return float(price)



    except Exception as e:


        print(
            "Price Error:",
            stock,
            e
        )



    return None






# =====================================
# DSE NEWS
# =====================================

def get_news(stock_list):


    result = {}



    try:


        url = (
            "https://www.dsebd.org/"
            "display_news.php"
        )



        r = requests.get(

            url,

            headers={
                "User-Agent":
                "Mozilla/5.0"
            },

            timeout=30

        )



        soup = BeautifulSoup(

            r.text,

            "html.parser"

        )



        text = soup.get_text("\n")



        for stock in stock_list:


            for line in text.split("\n"):


                if stock in line.upper():

                    result.setdefault(
                        stock,
                        []
                    ).append(
                        line.strip()
                    )



    except Exception as e:


        print(
            "News Error:",
            e
        )



    return result





# =====================================
# TELEGRAM
# =====================================

def send_telegram(message):


    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )


    requests.post(

        url,

        data={

            "chat_id":
            TELEGRAM_CHAT_ID,

            "text":
            message

        }

    )





# =====================================
# MAIN
# =====================================

def main():


    print(
        "Loading Portfolio..."
    )



    portfolio = extract_portfolio()



    print(
        "Stocks Loaded:",
        len(portfolio)
    )



    gain_stocks = []



    for item in portfolio:


        price = get_dse_price(

            item["stock"]

        )



        print(
            item["stock"],
            price
        )



        if price:


            gain = (

                (
                    price
                    -
                    item["average"]
                )

                /

                item["average"]

            ) * 100



            if gain >= 5:


                gain_stocks.append(

                    {

                    "stock":
                    item["stock"],

                    "average":
                    item["average"],

                    "price":
                    price,

                    "gain":
                    gain

                    }

                )




    message = (

        "📊 DSE Portfolio Monitor\n"

        +

        datetime.now()
        .strftime(
            "%d-%b-%Y %I:%M %p"
        )

        +

        "\n\n"

    )



    message += (
        "📈 Stocks Gain More Than 5%\n\n"
    )



    if gain_stocks:


        for x in sorted(

            gain_stocks,

            key=lambda y:y["gain"],

            reverse=True

        ):


            message += (

                f"{x['stock']}\n"

                f"Average Cost: {x['average']}\n"

                f"Current Price: {x['price']}\n"

                f"Gain: +{x['gain']:.2f}%\n\n"

            )



    else:


        message += (

            "No portfolio stock gained more than 5%."

        )




    send_telegram(message)



    print(
        "Telegram Sent"
    )




if __name__ == "__main__":

    main()
