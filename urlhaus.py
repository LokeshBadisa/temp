# import asyncio
# import json
# import aiohttp
# from tqdm import tqdm
# import pandas as pd
# from urllib.parse import urlparse
# import re

# MAX_CONCURRENCY = 1000


# def has_domain_name(url):
#     parsed = urlparse(url)
#     hostname = parsed.hostname
    
#     if not hostname:
#         return False
    
#     # Check if hostname is an IP address
#     ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
#     is_ip = re.match(ip_pattern, hostname)
    
#     return not is_ip


# async def fetch_mime(url, session, sem, pbar):
#     async with sem:
#         try:
#             async with session.get(url, allow_redirects=True) as r:
#                 mime = r.headers.get("Content-Type", "")
#         except Exception:
#             mime = None
#         finally:
#             pbar.update(1)
#     return url, mime

# async def main(URLS):
#     sem = asyncio.Semaphore(MAX_CONCURRENCY)
#     connector = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)

#     async with aiohttp.ClientSession(connector=connector) as session:
#         pbar = tqdm(total=len(URLS), desc="Fetching MIME")
#         tasks = [
#             fetch_mime(url, session, sem, pbar)
#             for url in URLS
#         ]
#         results = await asyncio.gather(*tasks)
#         pbar.close()

#     #Save results to a json file
#     with open("urlhaus_results.json", "w") as f:
#         json.dump(results, f)

# if __name__ == "__main__":
#     df = pd.read_csv('/media/lokesh/Windows-SSD/Ubuntu-Stuff/RA/Obfuscated Link Prediction/Datasets/urlhaus.csv')
#     df['has_domain'] = df['url'].apply(has_domain_name)
#     df = df[df['has_domain']]
#     URLS = df['url'].tolist()
#     asyncio.run(main(URLS))

import pandas as pd
from urllib.parse import urlparse
import re
import asyncio
from tqdm import tqdm
import aiohttp
import json

MAX_CONCURRENCY = 500


def is_numeric_domain(domain):
    return bool(re.fullmatch(r"[0-9.]+", domain)) or bool(re.fullmatch(r"[0-9.]+", domain.split(":")[0]))

def remove_domains(domain):
    if domain in ['raw.githubusercontent.com']:
        return True
    return False

async def get_true_homepage(url,session,sem):
    try:
        async with sem:
            p = urlparse(url)
            base = f"{p.scheme}://{p.netloc}/"
            async with session.get(base, allow_redirects=True, ssl=False, timeout=10) as r:
                if r.status != 200:
                    return f'Error: {str(r.status)}, {str(r.url)}'
                # print('status:',r,r.url)
                return str(r.url)
    except Exception as e:
        return f'Error: {str(e)}'

async def helper(url,D,pbar,session,sem):        
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}/"
    if base not in D:
        D[base] = await get_true_homepage(url,session,sem)
        pbar.update(1)
    else:
        pbar.update(1)

async def main(URLS):
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
    D = {}

    async with aiohttp.ClientSession(connector=connector) as session:
        pbar = tqdm(total=len(URLS))
        tasks = [
            helper(url, D, pbar,session,sem)
            for url in URLS
        ]
        await asyncio.gather(*tasks)
        pbar.close()

    #Save results to a json file
    with open("urlhaus_active_domain.json", "w") as f:
        json.dump(D, f)    

if __name__ == "__main__":
    df = pd.read_csv('urlhaus.csv')
    df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
    df = df[~df['domain'].apply(is_numeric_domain) & ~df['domain'].apply(remove_domains)]
    asyncio.run(main(df['url'].tolist()))
