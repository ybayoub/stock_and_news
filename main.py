import os
import requests
from datetime import date, timedelta
from twilio.rest import Client

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

increase = 0


def get_days(today):
    yesterday_ = today - timedelta(days=1)
    day_before_ = today - timedelta(days=2)
    yesterday_date = yesterday_.strftime("%Y-%m-%d")
    day_before_date = day_before_.strftime("%Y-%m-%d")
    return yesterday_date, day_before_date


def is_worth_news(list_value: list) -> bool:
    global increase
    final_value, initial_value = float(list_value[1]), float(list_value[0])
    increase = 100 * (final_value - initial_value) / initial_value
    if abs(increase) > 5:
        return True
    else:
        return False


stock_api_key = os.environ.get("STOCK_API_KEY")
stock_api_parameters = dict(function="TIME_SERIES_DAILY",
                            symbol=STOCK,
                            apikey=stock_api_key,
                            outputsize="",
                            datatype="")
response_stock = requests.get("https://www.alphavantage.co/query", params=stock_api_parameters)
response_stock.raise_for_status()
data_stock = response_stock.json()

# Date of today isn't available in the Stock API ➡️ (Yesterday/Day before)
days = get_days(date.today())

market_info = []
for day in days:
    market_info.append(data_stock["Time Series (Daily)"][day]["4. close"])

if is_worth_news(market_info):
    news_api_key = os.environ.get("NEWS_API_KEY")

    news_api_parameters = {
        "qInTitle": COMPANY_NAME,
        "sortBy": "popularity",
        "apiKey": news_api_key
    }

    response_news = requests.get("https://newsapi.org/v2/everything", params=news_api_parameters)
    response_news.raise_for_status()

    articles = response_news.json()["articles"]
    three_articles = articles[:3]

    print(f"{increase:.4f} %")
    # Send a separate message with the percentage change and each article's title and description to your phone number.
    twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(twilio_account_sid, auth_token)

    for article in three_articles:
        if increase > 0:
            message = client.messages.create(
                body=f"{STOCK}: 🔺{increase:.4f}%\n"
                     f"Headline: {article['title']}\n"
                     f"Brief: {article['description']}",
                from_=os.environ.get("TWILIO_NUMB"),
                to=os.environ.get("USER_NUMB")
            )
        elif increase < 0:
            message = client.messages.create(
                body=f"{STOCK}: 🔻{increase:.4f}%\n"
                     f"Headline: {article['title']}\n"
                     f"Brief: {article['description']}",
                from_=os.environ.get("TWILIO_NUMB"),
                to=os.environ.get("USER_NUMB")
            )
