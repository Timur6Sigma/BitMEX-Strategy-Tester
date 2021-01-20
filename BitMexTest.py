import json
import websocket
from bitmex import bitmex
import BitMexTestFunctions
import BitMexTestKeysApi
import BitMexTestAuthentication
import warnings

# Disable all warnings
warnings.filterwarnings("ignore")

######################################################
# For Signal
signal = "Neutral"

######################################################
# Backtesting
equity = [5000]

######################################################
# bid and ask variables (the orderbooklist and the std div variables and lists)
bid, ask, bidMaxPrice, askMinPrice, bidMaxSize, askMinSize = None, None, None, None, None, None

######################################################
# API Keys for authentication
apiKey = BitMexTestKeysApi.apiKey
secretKey = BitMexTestKeysApi.secretKey

# Client only used to create/amend/cancel orders
client = bitmex(test=True, api_key=apiKey, api_secret=secretKey)

######################################################
# orderQty
orderQty = 1

######################################################
ws = websocket.create_connection("wss://www.bitmex.com/realtime")

successfullyConnected = False
if BitMexTestFunctions.connection_check_welcome(ws):

    BitMexTestAuthentication.authentication_of_account(ws, apiKey, secretKey)
    if BitMexTestFunctions.connection_check_authentication(ws):

        BitMexTestFunctions.subscribe_to_stream(ws, "subscribe", "orderBookL2_25", "XBTUSD")
        if BitMexTestFunctions.connection_check_subscription(ws, "orderBookL2_25", "XBTUSD"):

            BitMexTestFunctions.subscribe_to_stream(ws, "subscribe", "position", "XBTUSD")
            if BitMexTestFunctions.connection_check_subscription(ws, "position", "XBTUSD"):

                successfullyConnected = True
                print("-Successfully connected-")

######################################################
if successfullyConnected:

    while True:

        response = json.loads(ws.recv())
        # Check what that for a response is and work with it
        if response["table"] == "orderBookL2_25":
            bid, ask = BitMexTestFunctions.get_orderbook(response, bid, ask)
            if bid.size and ask.size:
                bidMaxPrice, askMinPrice, bidMaxSize, askMinSize = BitMexTestFunctions.get_best_quotes(bid, ask)
        elif response["table"] == "position":
            pass
        else:
            print("SOS - unknown response:")
            print(response)
            print("-Websocket API will be closed-")
            break

        ######################################################
        # When response is processed and something is in bid and ask -> process the data to trade
        if bid is not None and ask is not None and bid.size and ask.size:

            ######################################################
            signal = None   # Here a signalgenerating function should return "Buy" or "Sell" to "signal"

            if signal == "Buy":
                print("Buy at", bidMaxPrice)
                entryPrice = bidMaxPrice
                # To test Buy Signal
                while True:
                    response = json.loads(ws.recv())
                    # Check what that for a response is and work with it
                    if response["table"] == "orderBookL2_25":
                        bid, ask = BitMexTestFunctions.get_orderbook(response, bid, ask)
                        if bid.size and ask.size:
                            bidMaxPrice, askMinPrice, bidMaxSize, askMinSize = BitMexTestFunctions.get_best_quotes(bid, ask)
                    finished = BitMexTestFunctions.test_signal(bidMaxPrice, askMinPrice, equity, entryPrice, 10, 10, 0, signal)
                    if finished:
                        break

            elif signal == "Sell":
                print("Sell at", askMinPrice)
                entryPrice = askMinPrice
                # To test Sell Signal
                while True:
                    response = json.loads(ws.recv())
                    # Check what that for a response is and work with it
                    if response["table"] == "orderBookL2_25":
                        bid, ask = BitMexTestFunctions.get_orderbook(response, bid, ask)
                        if bid.size and ask.size:
                            bidMaxPrice, askMinPrice, bidMaxSize, askMinSize = BitMexTestFunctions.get_best_quotes(bid, ask)
                    finished = BitMexTestFunctions.test_signal(bidMaxPrice, askMinPrice, equity, entryPrice, 10, 10, 0, signal)
                    if finished:
                        break

    ws.close()

else:
    print("Not successfully connected - closing Websocket and ending program")
    ws.close()
