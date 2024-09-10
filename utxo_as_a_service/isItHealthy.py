import requests
import os
import json
from datetime import datetime

url = os.environ['URL']

# get status directly from woc
def get_woc_last_block():
    r = requests.get("https://api.whatsonchain.com/v1/bsv/test/chain/info")
    print(r.text)

    if r.status_code == 200:
        j = r.json()
        last_block_height = j['blocks']
        print(last_block_height)
        return last_block_height
    
    else:
        print('WhatsOnChain returned status code ' + str(r.status_code))
        exit(1)

# get status from service
def get_service_last_block():
    # try to get status from service
    try:
        r = requests.get(url + '/status')
        print(r.text)

        if r.status_code == 200:
            # get last block time
            j = r.json()
            last_block_height = j['status']['block height']
            print(last_block_height)
            return last_block_height

        else:
            print('Service has status code ' + str(r.status_code) + ' and is unhealthy')
            exit(1)
    # catch exception if service is not available
    except:
        print(f"{url} + /status is unavailable")
        exit(1)


# Main function determines if uaas_rust service is healthy
# by comparing last block height from woc and service
def main():
    print ('Getting last block heights')
    woc_last_block = get_woc_last_block()
    print(f"Last block height from woc: {woc_last_block}")
    service_last_block = get_service_last_block()
    print(f"Last block height from service: {service_last_block}")

    if woc_last_block == service_last_block:
        print('Service is healthy')
        exit(0)
    else:
        print('Service is unhealthy')
        exit(1)



# main entry point
if __name__ == '__main__':
    main()


  
