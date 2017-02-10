import v20
from datetime import datetime, timedelta


def getRate():
    OANDA_ACCESS_TOKEN = ""
    OANDA_ACCOUNT_ID = '001-001-1118573-002'  # put your access id here

    latest_price_time = (datetime.utcnow() -
                         timedelta(seconds=15)).isoformat('T') + 'Z'

    api = v20.Context(
        'api-fxtrade.oanda.com',
        '443',
        token=OANDA_ACCESS_TOKEN)

    response = api.pricing.get(
        OANDA_ACCOUNT_ID,
        instruments='GBP_JPY',
        since=latest_price_time,
        includeUnitsAvailable=False)
    prices = response.get("prices", 200)
    if len(prices):
        bidPrice = prices[0].bids[0].price
        askPrice = prices[0].asks[0].price
        print("Bid: ", bidPrice)
        print("Ask: ", askPrice)
    return ((bidPrice + askPrice) / 2, bidPrice, askPrice, latest_price_time)
