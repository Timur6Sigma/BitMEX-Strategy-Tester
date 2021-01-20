import numpy as np
import json
import dateutil.parser as dateparser
import time

symbol, id, side, size, price = 0, 1, 2, 3, 4


# Test for Welcome response
def connection_check_welcome(ws):
    everythingOkay = True
    # response should be a welcome response
    response = json.loads(ws.recv())
    print(response)
    welcome = "Welcome to the BitMEX Realtime API."
    try:
        if not (response["info"] == welcome):
            everythingOkay = False
    except:
        everythingOkay = False
    return everythingOkay


def connection_check_authentication(ws):
    everythingOkay = True
    # response should be a welcome response
    response = json.loads(ws.recv())
    print(response)
    try:
        if not (response["success"] == True and response["request"]["op"] == "authKeyExpires"):
            everythingOkay = False
    except:
        everythingOkay = False

    return everythingOkay


# Check for successful subscription response
def connection_check_subscription(ws, subscription, instrument):
    everythingOkay = True
    # response should be a success response
    response = json.loads(ws.recv())
    print(response)
    try:
        if not (response["success"] == True and response["subscribe"] == subscription + ":" + instrument):
            everythingOkay = False
    except:
        everythingOkay = False
    return everythingOkay


# Subscribe or unsubscribe to the an stream
def subscribe_to_stream(ws, sub, data, instrument):
    if sub == "subscribe":
        ws.send(json.dumps({"op": "subscribe", "args": [data + ":" + instrument]}))
    elif sub == "unsubscribe":
        ws.send(json.dumps({"op": "unsubscribe", "args": [data + ":" + instrument]}))


# Get open position Value of symbol
def get_current_positionvalue_of_symbol(response, symbol):
    position = None
    data = response["data"][0]
    try:
        if data["symbol"] == symbol:
            position = data["currentQty"]
    except:
        pass
    return position


# Get Orderbook (currently orderBookL2_25) in an array bid and array ask with symbol, id, side, size, price each
def get_orderbook(response, bid, ask):
    data = response["data"]

    if response["action"] == "update":
        for row in data:
            rowDictKeys = list(row.keys())
            if row["side"] == "Buy":
                index = np.where(bid[:, id] == str(row["id"]))
                if "size" in rowDictKeys:
                    bid[index, size] = row["size"]
            elif row["side"] == "Sell":
                index = np.where(ask[:, id] == str(row["id"]))
                if "size" in rowDictKeys:
                    ask[index, size] = row["size"]

    elif response["action"] == "delete":
        for row in data:
            if row["side"] == "Buy":
                index = np.where(bid[:, id] == str(row["id"]))
                bid = np.delete(bid, index, axis=0)
            else:
                index = np.where(ask[:, id] == str(row["id"]))
                ask = np.delete(ask, index, axis=0)

    elif response["action"] == "insert":
        for row in data:
            if row["side"] == "Buy":
                bid = np.vstack((bid, np.array([[row["symbol"], row["id"], row["side"], row["size"], row["price"]]])))
            else:
                ask = np.vstack((ask, np.array([[row["symbol"], row["id"], row["side"], row["size"], row["price"]]])))

    elif response["action"] == "partial":
        bid = np.array([])
        ask = np.array([])

        for row in data:
            if row["side"] == "Buy":
                if len(np.shape(bid)) == 1 and np.shape(bid)[0] == 0:
                    bid = np.append(bid, np.array([[row["symbol"], row["id"], row["side"], row["size"], row["price"]]]))
                else:
                    bid = np.vstack(
                        (bid, np.array([[row["symbol"], row["id"], row["side"], row["size"], row["price"]]])))

            else:
                if len(np.shape(ask)) == 1 and np.shape(ask)[0] == 0:
                    ask = np.append(ask, np.array([row["symbol"], row["id"], row["side"], row["size"], row["price"]]))
                else:
                    ask = np.vstack(
                        (ask, np.array([[row["symbol"], row["id"], row["side"], row["size"], row["price"]]])))

    # Max bid is in bid[0], and Min ask in ask[0]
    bid = bid[np.argsort(bid[:, price])[::-1]]
    ask = ask[np.argsort(ask[:, price])]

    return bid, ask


def get_best_quotes(bid, ask):
    bidMaxPrice = float(bid[0][price])
    askMinPrice = float(ask[0][price])

    bidMaxSize = int(bid[0][size])
    askMinSize = int(ask[0][size])

    return bidMaxPrice, askMinPrice, bidMaxSize, askMinSize


def get_trades(response, recentTrades):
    data = response["data"]

    recentTrades = np.flip(recentTrades, axis=0)

    for row in data:
        timestamp = dateparser.parse(row["timestamp"])
        timestampInUnix = timestamp.timestamp()

        if len(np.shape(recentTrades)) == 1 and np.shape(recentTrades)[0] == 0:
            recentTrades = np.append(recentTrades, np.array(
                [[timestampInUnix, row["symbol"], row["side"], row["size"], row["price"]]]))
        else:
            recentTrades = np.vstack(
                (recentTrades, np.array([[timestampInUnix, row["symbol"], row["side"], row["size"], row["price"]]])))

    recentTrades = np.flip(recentTrades, axis=0)
    recentTrades = recentTrades[:200]

    return recentTrades


def test_signal(bidMaxPrice, askMinPrice, equity, entry, tp, sl, fee, signal):
    finished = False
    if signal == "Buy":
        if (askMinPrice > (entry + tp)) or (askMinPrice < (entry - sl)):
            pnl = ((askMinPrice - entry) / entry) * (1 - fee) - (entry * fee)
            equity.append((1 + pnl) * equity[-1])
            print("Sold:", askMinPrice, str(round(pnl * 100, 4)) + "%", equity[::-1])
            finished = True

    elif signal == "Sell":

        if (bidMaxPrice < (entry - tp)) or (bidMaxPrice > (entry + sl)):
            pnl = ((entry - bidMaxPrice) / entry) * (1 - fee) - (entry * fee)
            equity.append((1 + pnl) * equity[-1])
            print("Bought:", bidMaxPrice, str(round(pnl * 100, 4)) + "%", equity[::-1])
            finished = True
    return finished