from colorama import Fore, Back, Style
from datetime import datetime
import pytz
import requests
import json
import colorama 
import time

def parseJsonConfig():
    configFileJson = json.loads(open("config.json").read())
    return configFileJson

def searchCryptoDNSRecord(config = parseJsonConfig()):
    cloudflareApiUrl = f'https://api.cloudflare.com/client/v4/zones/{config["zone_id"]}/dns_records?comment=while402 CryptoDNS'

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Email": config["cf_email"],
        "X-Auth-Key": config["api_token"]
    }
    
    response = requests.request("GET", cloudflareApiUrl, headers=headers)
    jsonResult = response.json()
    
    if jsonResult["success"] != True:
        print(Fore.RED + "Cant make API Request to CloudFlare." + Style.RESET_ALL)
        return [401]

    if len(jsonResult["result"]) == 0:
        print(f"Cant find DNS records from {Style.BRIGHT + Fore.BLUE + 'CryptoDNS' + Style.RESET_ALL}")
        return [404]
    
    return [200, jsonResult]
    
    

def makeNewTxtRecordCF(content, overwriteRecordID = '', config = parseJsonConfig(), hostname = parseJsonConfig()["dnsRecordHostname"]):
    cloudflareApiUrl = f"https://api.cloudflare.com/client/v4/zones/{config['zone_id']}/dns_records" + (f"/{overwriteRecordID}" if overwriteRecordID else "")

    jsonPayload = {
        "content": content,
        "name": hostname,
        "proxied": False,
        "type": "TXT",
        "id": config["zone_id"],
        "ttl": 60,
        "zone_id": config["zone_id"],
        "comment": "while402 CryptoDNS"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Email": config["cf_email"],
        "X-Auth-Key": config["api_token"]
    }
    
    try:
        response = requests.request("PUT", cloudflareApiUrl, json=jsonPayload, headers=headers)
    except Exception as err:
        return [500,err]
    
    jsonResult = response.json()
    
    if jsonResult["success"] == True:
        print(f"Status of loading new TXT record in cloudflare DNS: {Style.BRIGHT + Fore.GREEN +'Success' + Style.RESET_ALL}")
        return [200]
    else:
        print(f"Status of loading new TXT record in cloudflare DNS: {Style.BRIGHT + Fore.RED +'Fail' + Style.RESET_ALL}")
        return [401, jsonResult["errors"][0]]

def getCryptoPriceList(cryptoList = parseJsonConfig()["curencyList"]):
    cryptoExchangeRates = coinLoreLoadPrices()[1]
    resultJson = {}
    
    for cryptoCurency in cryptoList:
        try:
            resultJson[cryptoCurency] = cryptoExchangeRates[cryptoCurency]
        except:
            print(f"Cant find {cryptoCurency} curency")
    
    return resultJson
    
def coinLoreLoadPrices():
    url = "https://api.coinlore.net/api/tickers/"
    
    try:
        responseJson = requests.get(url).json()
    except Exception as err:
        return [500,err]
    
    outCryptoDict = {}
    for cryptoCurency in responseJson["data"]:
        outCryptoDict[cryptoCurency["symbol"]] = {"name": cryptoCurency["name"], "price_usd": cryptoCurency["price_usd"], "percent_change_24h": cryptoCurency["percent_change_24h"]}
    
    return [200,outCryptoDict]

def main():
    colorama.init()
    rewriteTimeout = parseJsonConfig()["rewriteTimeout"]

    while True:
        cryptoPriceList = json.dumps({"crypto": getCryptoPriceList(), "updateTime": datetime.now(pytz.timezone('Europe/Moscow')).strftime("%d %B %Y %H:%M")}, separators=(',', ':'))
        
        dnsRecord = searchCryptoDNSRecord()
        if dnsRecord[0] == 200:
            print("Overwriting DNS Record...")
            
            dnsRecordID = str(dnsRecord[1]['result'][0]['id'])
            makeNewTxtRecordCF(cryptoPriceList, overwriteRecordID = dnsRecordID)
        elif dnsRecord[0] == 500:
            print(f"Get error while sending request to CloudFlare: {Style.BRIGHT + Fore.RED + str(dnsRecord[1]) + Style.RESET_ALL}"
        elif dnsRecord[0] == 404:
            print("Making new DNS Record...")
            makeNewTxtRecordCF(cryptoPriceList)
        else:
            print("Untitled error!")
        
        print(f"Sleep for {Style.BRIGHT + Fore.CYAN + str(rewriteTimeout) + Style.RESET_ALL} seconds...")
        time.sleep(rewriteTimeout)

if __name__ == "__main__":
    main()