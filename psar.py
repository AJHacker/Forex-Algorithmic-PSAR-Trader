# main file and financial analysis
from lxml import html
import requests
import time
import threading
import sys
from getPrices import getRate as findOandaRate
from algopy import decide


def run(f=5, interval=30, pair='GBPJPY'):
    clearData()
    start = time.time()
    freq = f

    count = 0
    pointsPer = int(interval / f)
    while True:
        if count == pointsPer:
            PSAR(f, interval)
            RSI(f, interval)
            decide()
            count = 1
        else:
            count += 1
        try:
            (price, bid, ask, now) = findOandaRate()
        except:
            print('connection error')

        text_file = open("prices.txt", "a")
        text_file.write("%s %s %s %s\n" % (price, bid, ask, now))
        text_file.close()
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
    pointsPer = int(interval / f)

    data = open('prices.txt', 'r').read()
    data = [line.split(' ') for line in data.splitlines()]
    lastPoint = data[-1]
    rates = [line[0] for line in data]

    psars = open('psars.txt', 'r').read().splitlines()
    psars = [line.split(' ') for line in psars]  # psar EP AF start direction

    if psars == []:  # initial PSAR values
        AF = .02
        EP = max(rates)
        newSAR = min(rates)
        trendDirection = '+'
    else:
        (lastSAR, EP, AF, trendDirection) = psars[-1]
        lastSAR = float(lastSAR)
        (newRate, lo, hi) = rateStats(rates, pointsPer)
        EP = float(EP)
        AF = float(AF)
        if lo < lastSAR < hi:
            if trendDirection == '+':
                trendDirection = '-'
                newSAR = EP
                EP = lo
                AF = .02
            else:
                trendDirection = '+'
                newSAR = EP
                EP = hi
                AF = .02

        elif trendDirection == '+':
            if hi > EP:
                EP = hi
                if AF < .2:
                    AF += .02
            # The formula from wikipedia
            if lastSAR > lo:
                newSAR = lo
            else:
                newSAR = lastSAR + AF * (EP - lastSAR)

        elif trendDirection == '-':
            if lo < EP:
                EP = lo
                if AF < .19:
                    AF += .02
            # The formula from wikipedia
            if lastSAR > hi:
                newSAR = hi
            else:
                newSAR = lastSAR + AF * (EP - lastSAR)

    psars.append([str(newSAR), str(EP), str(AF), str(trendDirection)])
    updateList(psars)
    print('\t', 'PSAR:', newSAR, EP, AF, trendDirection)


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
    print('\t', 'RSI:', RSI)


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

if __name__ == '__main__':
    run(1, 5)
