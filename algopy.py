# main file and financial analysis
from lxml import html
import requests
import time
import threading
import sys


def run(f=5, interval=30, pair='GBP_JPY'):
    clearData()
    start = time.time()
    freq = f

    count = 1
    pointsPer = int(interval / f)
    while True:
        try:
            (price, bid, ask, now) = getRate(pair)
            print('price: %20f' % price)
            text_file = open("prices.txt", "a")
            text_file.write("%s %s %s %s\n" % (price, bid, ask, now))
            text_file.close()
        except:
            print('connection error')
            continue
        if count == pointsPer:
            print(count)
            PSAR(f, interval)
            RSI(f, interval)
            decide(simulation=False, pair=pair)
            count = 1
        else:
            count += 1

        time.sleep(freq)


def clearData():
    text_file = open("prices.txt", "w")
    text_file.close()
    text_file = open("psars.txt", "w")
    text_file.close()
    text_file = open("rsi.txt", "w")
    text_file.close()
    text_file = open("testAccount.txt", "w")
    text_file.close()


def PSAR(f=5, interval=30):  # calculation period in seconds
    # calculation period over data points per minute
    sensitivity = .02
    pointsPer = int(interval / f)

    data = open('prices.txt', 'r').read()
    data = [line.split(' ') for line in data.splitlines()]
    lastPoint = data[-1]
    rates = [line[0] for line in data]

    psars = open('psars.txt', 'r').read().splitlines()
    psars = [line.split(' ') for line in psars]  # psar EP AF start direction

    if psars == []:  # initial PSAR values
        AF = sensitivity
        EP = max(rates)
        newSAR = min(rates)
        trendDirection = '+'
    else:
        (lastSAR, EP, AF, trendDirection) = psars[-1]
        lastSAR = float(lastSAR)
        (newRate, lo, hi) = rateStats(rates, pointsPer)
        EP = float(EP)
        AF = float(AF)
        if (lo < lastSAR and trendDirection == '+'):
            trendDirection = '-'
            newSAR = EP
            EP = lo
            AF = sensitivity
        elif (lastSAR < hi and trendDirection == '-'):
            trendDirection = '+'
            newSAR = EP
            EP = hi
            AF = sensitivity

        elif trendDirection == '+':
            if hi > EP:
                EP = hi
                if AF < .185:
                    AF += sensitivity
            # The formula from wikipedia
            # if lastSAR > lo:
            #     newSAR = lo
            # else:
            newSAR = lastSAR + AF * (EP - lastSAR)

        elif trendDirection == '-':
            if lo < EP:
                EP = lo
                if AF < .185:
                    AF += sensitivity
            # The formula from wikipedia
            # if lastSAR > hi:
            #     newSAR = hi
            # else:
            newSAR = lastSAR + AF * (EP - lastSAR)

    psars.append([str(newSAR), str(EP), str(AF), str(trendDirection)])
    updateList(psars, 'psars.txt')
    print('\tPSAR: %20s EP: %10s AF: %10s Direction: %s' %
          (newSAR, EP, AF, trendDirection))


def RSI(f=5, interval=30):
    # calculation period over data points per minute
    pointsPer = int(interval / f)

    data = open('prices.txt', 'r').read()
    data = [line.split(' ') for line in data.splitlines()]
    lastPoint = data[-1]
    rates = list(map(float, [line[0] for line in data]))

    rsis = open('rsi.txt', 'r').read().splitlines()
    rsis = [line.split(' ') for line in rsis]  # psar EP AF start direction

    if len(rates) == pointsPer * 14:
        totalGain = 0
        totalLoss = 0
        for i in range(1, 15):
            period = rates[-pointsPer * i:len(rates) - pointsPer * (i - 1)]
            change = period[-1] - period[0]
            if change > 0:
                totalGain += change
            else:
                totalLoss += change
        avgGain = totalGain / 14
        avgLoss = totalLoss / 14
    elif len(rates) > pointsPer * 14:
        (lastRSI, lastAvgGain, lastAvgLoss) = rsis[-1]
        lastAvgGain = float(lastAvgGain)
        lastAvgLoss = float(lastAvgLoss)
        change = rates[-1] - rates[-pointsPer]
        if change > 0:
            avgGain = (lastAvgGain * 13 + change) / 14
            avgLoss = lastAvgLoss
        else:
            avgLoss = (lastAvgLoss * 13 + change) / 14
            avgGain = lastAvgGain
    else:
        return  # if there are not enough data points

    RS = avgGain / -avgLoss
    RSI = 100 - (100 / (1 + RS))  # from stockcharts.com

    rsis.append([str(RSI), str(avgGain), str(avgLoss)])
    updateList(rsis, 'rsi.txt')
    print('\tRSI: %20s' % RSI)


def rateStats(L, n):  # list of rates, number of points per calculation period
    total = 0
    for i in range(n):
        total += float(L[-n - 1])
    return (total / n, float(min(L[-n:])), float(max(L[-n:])))


def updateList(L, file='psars.txt'):
    row = L[-1]
    result = ''
    for item in row:
        result += str(item) + ' '
    textFile = open(file, 'a')
    textFile.write(result[:-1] + '\n')
    textFile.close()

import v20
from datetime import datetime, timedelta
OANDA_ACCESS_TOKEN = ""
OANDA_ACCOUNT_ID = "101-001-5213287-001"
latest_price_time = (datetime.utcnow() -
                     timedelta(seconds=15)).isoformat('T') + 'Z'

api = v20.Context(
    'api-fxpractice.oanda.com',
    '443',
    token=OANDA_ACCESS_TOKEN)

previousTradeID = None


def getRate(instruments='GBP_JPY'):
    # OANDA_ACCESS_TOKEN = "dbf0c7d289cd280bca36de687e731068-febaf325b65bb1f8a37ee7f614138018"
    # OANDA_ACCOUNT_ID = '001-001-1118573-002'  # put your access id here
    # OANDA_ACCESS_TOKEN = "885bf1da9c44c514dbb6f5e243301ce0-a3d96fc184407787350dc03ec57c4f5c"
    # OANDA_ACCOUNT_ID = "101-001-5213287-001"
    # latest_price_time = (datetime.utcnow() -
    #                      timedelta(seconds=15)).isoformat('T') + 'Z'
    #
    # api = v20.Context(
    #     'api-fxpractice.oanda.com',
    #     '443',
    #     token=OANDA_ACCESS_TOKEN)

    response = api.pricing.get(
        OANDA_ACCOUNT_ID,
        instruments=instruments,
        since=latest_price_time,
        includeUnitsAvailable=False)
    prices = response.get("prices", 200)
    if len(prices):
        bidPrice = prices[0].bids[0].price
        askPrice = prices[0].asks[0].price
        # print("Bid: ", bidPrice)
        # print("Ask: ", askPrice)
    return ((bidPrice + askPrice) / 2, bidPrice, askPrice, latest_price_time)


# decision making and trading


def decide(simulation=True, pair='GBP_JPY'):
    rates, bids, asks, rsis, psarData = unpackData()
    pip = .01 if pair[4:] == 'JPY' else .0001
    # True for buy, False for sell, None for None
    decision = readPSAR(psarData, pip)
    print('\t', decision)
    # print(decision)
    if simulation and decision != None:
        simulate(decision, bids, asks, rates[-1], pair)
    elif decision != None:
        if(decision):
            if(previousTradeID == None):
                response = api.order.market(
                    OANDA_ACCOUNT_ID,
                    instrument=pair,
                    units=5000)
                print("Opening LONG Position")
                previousTradeID = response.get('orderFillTransaction').id
            else:
                response = api.trade.close(
                    OANDA_ACCOUNT_ID,
                    tradeID=previousTradeID)
                print("Closing LONG Position")

        else:
            if(previousTradeID == None):
                response = api.order.market(
                    OANDA_ACCOUNT_ID,
                    side="sell",
                    instrument=pair,
                    units=5000)
                previousTradeID = response.get('orderFillTransaction').id
            else:
                response = api.trade.close(
                    OANDA_ACCOUNT_ID,
                    tradeID=previousTradeID)

        print("Trading id", response.get('orderFillTransaction').id)
        print("Account Balance", response.get(
            'orderFillTransaction').accountBalance)
        print("Price", response.get('orderFillTransaction').price)

    return 42


def simulate(decision, bids, asks, rate, pair='GBP_JPY'):
    print('Simulating trade...')
    account = open('testAccount.txt', 'r').read().splitlines()
    account = [line.split() for line in account]
    marginRatio = 20
    for i in range(3):
        try:
            if pair[:3] != 'USD':
                BASEHOME = getRate(pair[:3] + '_USD')[0]
            else:
                BASEHOME = 1
            if pair[4:] != 'USD':
                QUOTEHOME = getRate('USD_' + pair[4:])[0]
            else:
                QUOTEHOME = 1
            break
        except:
            print('Failed to retrieve home currency conversion rates')
            return

    if account == []:
        balance = 1000
    else:
        balance = float(account[-1][0])
        lastRate = float(account[-1][3])
    if account == [] or account[-1][4] == 'close':
        units = int(balance * marginRatio / BASEHOME)
    else:
        units = int(account[-1][2])
    marginBalance = marginRatio * balance

    # new balance = (Closing Rate - Opening Rate) * (Closing {quote}/{home
    # currency}) * Units
    bid = float(bids[-1])
    ask = float(asks[-1])

    if decision:
        action = 'buy'
        if len(account) >= 1 and account[-1][1] == 'buy' and account[-1][4] == 'open':
            return
        if len(account) >= 1 and account[-1][4] == 'open':
            openingRate = ask
            closingRate = lastRate
            status = 'close'
        else:
            openingRate = ask
            closingRate = bid
            status = 'open'
        balance += (closingRate - openingRate) * (1 / QUOTEHOME) * units
    else:
        action = 'sell'
        if len(account) >= 1 and account[-1][1] == 'sell' and account[-1][4] == 'open':
            return
        if len(account) >= 1 and account[-1][4] == 'open':
            openingRate = lastRate
            closingRate = ask
            status = 'close'
        else:
            openingRate = ask
            closingRate = bid
            status = 'open'
        balance += (closingRate - openingRate) * (1 / QUOTEHOME) * units

    print('***', action, units, 'balance:', balance, '***\n')
    account.append([str(balance), action, str(units), rate, status])
    updateList(account, 'testAccount.txt')


def updateList(L, file='testAccount.txt'):
    row = L[-1]
    result = ''
    for item in row:
        result += str(item) + ' '
    textFile = open(file, 'a')
    textFile.write(result[:-1] + '\n')
    textFile.close()


def readPSAR(psarData, pip):
    actionMargin = 3
    thisTrend = findTrend(psarData, 0)
    baseLine = findBase(psarData)
    print('baseline', baseLine)
    print('action threshold', actionMargin)
    print('this trend', thisTrend)
    print('trend length', len(thisTrend))
    if len(thisTrend) >= 2:
        if thisTrend[0][-1] == '+':
            if abs(float(thisTrend[0][0]) - baseLine) > actionMargin * pip:
                return True
        else:
            if abs(float(thisTrend[0][0]) - baseLine) > actionMargin * pip:
                return False
    return None


def findBase(psarData):
    # calculates the baseLine rate. for simplicity, we use the median of
    #   at most n many past periods
    n = 50
    rates = list(reversed([line[0] for line in psarData]))
    for i in range(len(rates)):
        if i >= n:
            rates = rates[:n]
            break
    rates = sorted(rates)
    return float(rates[len(rates) // 2])


def findTrend(psarData, n):
    # requires 2d list of psarData from psars.txt and n, the number of the trend to
    #   be isolated, starting from 0, the current trend
    # returns a list of the last trend from psarData, with index 0 being the most
    #   recent point
    count = 0
    direction = psarData[-1][-1]
    i = len(psarData) - 1
    end = len(psarData)
    while i > 0:
        if psarData[i][-1] != direction:
            count += 1
            if count > n:
                return list(reversed(psarData[i + 1:end]))
            else:
                if direction == '+':
                    direction = '-'
                    end = i + 1
                else:
                    direction = '+'
                    end = i + 1
        i -= 1
    return psarData[::-1]


def unpackData():
    data = open('prices.txt', 'r').read()
    data = [line.split(' ') for line in data.splitlines()]
    rates = [line[0] for line in data]
    bids = [line[1] for line in data]
    asks = [line[2] for line in data]

    psars = open('psars.txt', 'r').read().splitlines()
    psars = [line.split(' ') for line in psars]
    PSAR = [line[0] for line in psars]

    rsis = open('rsi.txt', 'r').read().splitlines()
    rsis = [line.split(' ') for line in rsis]
    RSI = [line[0] for line in rsis]

    return rates, bids, asks, RSI, psars

run(1, 5, 'AUD_USD')
# decide()
