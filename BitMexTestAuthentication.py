import hashlib
import hmac
import json
import time
import urllib


def authentication_of_account(ws, apiKey, secretKey):
    # Time now in UNIX + 1h = API Token expires
    expires = int(time.time() + 60*60)

    verb = "GET"
    endpoint = "/realtime"
    signature = bitmex_signature(secretKey, verb, endpoint, expires)

    ws.send(json.dumps({"op": "authKeyExpires", "args": [apiKey, expires, signature]}))


def bitmex_signature(secretKey, verb, url, nonce, postdict=None):
    """Given an API Secret key and data, create a BitMEX-compatible signature."""
    data = ''
    if postdict:
        # separators remove spaces from json
        # BitMEX expects signatures from JSON built without spaces
        data = json.dumps(postdict, separators=(',', ':'))
    parsedURL = urllib.parse.urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query
    # print("Computing HMAC: %s" % verb + path + str(nonce) + data)
    message = (verb + path + str(nonce) + data).encode('utf-8')

    signature = hmac.new(secretKey.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
    return signature