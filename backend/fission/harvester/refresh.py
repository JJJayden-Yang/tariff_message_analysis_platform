import requests
from requests.auth import HTTPBasicAuth
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from mastodon import Mastodon
import re
from flask import current_app, request



API_KEY = '5bb1c2c0df194b3d833e1206a9eeaeae'
OUTPUT_JSON = 'output_data_new.json'
BASE_URL = 'https://api.aio.eresearch.unimelb.edu.au'
ACCESS_TOKEN = 'SSS0iHzypgNFBYEgnB5l84CPLmFfvvg3_qTJCrR9JFk'

data = set()
json_data = []

def get_jwt(api_key):
    res = requests.post(f"{BASE_URL}/login", auth=HTTPBasicAuth('apikey', api_key))
    if res.ok:
        return res.text
    else:
        raise Exception(f"fail to get JWT: {res.status_code}, {res.text}")

def fetch_all_ids(jwt, query):
    url = f"{BASE_URL}/analysis/textsearch/collections/mastodon"
    headers = {'Authorization': f"Bearer {jwt}"}
    params = {'query': query}
    all_ids = []
    bookmark = None

    while True:
        if bookmark:
            headers['x-ado-bookmark'] = bookmark
        else:
            headers.pop('x-ado-bookmark', None)

        res = requests.get(url, headers=headers, params=params)
        if not res.ok:
            break

        ids = res.json()
        if not ids:
            break

        all_ids.extend(ids)
        bookmark = res.headers.get('x-ado-bookmark')
        if not bookmark:
            break

    return all_ids


def update_yesterday_data():
    global data, json_data
    print("\n🕒 daily refresh...")
    jwt = get_jwt(API_KEY)
    last_5_days = (datetime.now(timezone.utc) - timedelta(days=5)).strftime('%Y-%m-%d')
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    query = f'text:"tariff" AND date:[{last_5_days} TO {yesterday}]'
    ids = fetch_all_ids(jwt, query)
    print(f"🔢 total new ID number: {len(ids)}")

    mastodon_post_pattern = re.compile(
        r'^(?:https?://)?[a-zA-Z0-9.-]+/(?:@[^/]+|users?/[^/]+)/\d+$'
    )

    #
    valid_ids = [id_ for id_ in ids if mastodon_post_pattern.match(id_)]
    print(f"✅ The number of legal Mastodon post links: {len(valid_ids)}")

    data.update(valid_ids)

    for i, id in enumerate(valid_ids):
        try:
            print(f"⏳ [{i+1}/{len(valid_ids)}] processing: {id}")

            processed_data = process_url(id)
            # json_data.append(processed_data)
            response: Optional[requests.Response] = requests.post(
                url='http://router.fission/mqueue/mdata',
                headers={'Content-Type': 'application/json'},
                json=processed_data
    )
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ fail: {id} -> {e}")

def infer_region_from_note(note):
    note = note.lower()
    patterns = {
        "Australia": ["australia", "melbourne", "sydney", "brisbane", "perth", "adelaide", "🇦🇺", "aussie"],
        "Germany": ["germany", "berlin", "munich", "hamburg", "🇩🇪", "deutschland"],
        "Japan": ["japan", "tokyo", "osaka", "kyoto", "🇯🇵", "nippon", "nihon"],
        "China": ["china", "beijing", "shanghai", "guangzhou", "shenzhen", "🇨🇳", "zhongguo", "中国", "大陆", "中华", "taiwan", "taipei", "kaohsiung", "🇹🇼", "台灣", "台北", "hong kong", "hk", "🇭🇰", "香港"],
        "Korea": ["korea", "seoul", "🇰🇷", "대한민국", "한국"],
        "United States": ["usa", "united states", "new york", "los angeles", "san francisco", "chicago", "boston", "washington", "🇺🇸", "america"],
        "Canada": ["canada", "toronto", "vancouver", "montreal", "🇨🇦"],
        "France": ["france", "paris", "lyon", "marseille", "🇫🇷"],
        "United Kingdom": ["uk", "united kingdom", "england", "london", "manchester", "🇬🇧", "britain", "scotland"],
        "India": ["india", "delhi", "mumbai", "bangalore", "🇮🇳", "hindustan", "भारत"],
        "Spain": ["spain", "madrid", "barcelona", "🇪🇸"],
        "Italy": ["italy", "rome", "milan", "naples", "🇮🇹", "italia"],
        "Netherlands": ["netherlands", "amsterdam", "🇳🇱", "holland"],
        "Brazil": ["brazil", "rio", "rio de janeiro", "são paulo", "🇧🇷", "brasil"],
        "Russia": ["russia", "moscow", "saint petersburg", "🇷🇺", "россия"],
        "Mexico": ["mexico", "mexico city", "🇲🇽"],
        "Sweden": ["sweden", "stockholm", "🇸🇪"],
        "Norway": ["norway", "oslo", "🇳🇴"],
        "Finland": ["finland", "helsinki", "🇫🇮"],
        "Poland": ["poland", "warsaw", "🇵🇱"],
        "Indonesia": ["indonesia", "jakarta", "🇮🇩"],
        "Thailand": ["thailand", "bangkok", "🇹🇭"],
        "Philippines": ["philippines", "manila", "🇵🇭"],
        "Vietnam": ["vietnam", "hanoi", "ho chi minh", "🇻🇳", "việt nam"],
        "Malaysia": ["malaysia", "kuala lumpur", "🇲🇾"],
        "Singapore": ["singapore", "🇸🇬"],
        "New Zealand": ["new zealand", "auckland", "wellington", "🇳🇿"]
    }
    for region, keywords in patterns.items():
        for kw in keywords:
            if kw in note:
                return region
    return None

def infer_region(language, domain, note=""):
    lang_to_country = {
        "ja": "Japan", "de": "Germany", "fr": "France", "es": "Spain",
        "zh": "China", "zh-cn": "China", "zh-hans": "China",
        "zh-tw": "China", "ko": "Korea"
    }

    domain_to_country = {
        "mastodon.social": "Global", "mstdn.jp": "Japan", "pawoo.net": "Japan",
        "fedibird.com": "Japan", "mas.to": "Global", "aus.social": "Australia",
        "mastodon.au": "Australia", "chaos.social": "Germany", "mastodon.online": "Global",
        "mastodon.world": "Global", "mastodon.cloud": "Global", "mastodon.uk": "United Kingdom",
        "techhub.social": "United States", "masto.ai": "United States", "noc.social": "France",
        "mastodon.art": "Global", "kolektiva.social": "United States", "toot.community": "United States",
        "hachyderm.io": "United States", "octodon.social": "France", "mastodon.coffee": "Germany",
        "fosstodon.org": "United States", "det.social": "Germany", "journa.host": "Global",
        "social.tchncs.de": "Germany", "treehouse.systems": "Global", "mastodon.lol": "United States",
        "tech.lgbt": "Germany"
    }

    lang_key = language.lower() if language else ""
    if lang_key and lang_key != "en" and lang_key in lang_to_country:
        return lang_to_country[lang_key]

    note_based = infer_region_from_note(note)
    if note_based:
        return note_based

    return domain_to_country.get(domain, "Global")

def extract_text(content_html):
    content_links = re.findall(r'<a href="([^"]+)".*?>(.*?)</a>', content_html)
    if content_links and not any(link[1].strip() for link in content_links):
        content_html = re.sub(r'<a href="([^"]+)".*?>(.*?)</a>', r'\1', content_html)
    cleaned = re.sub(r'<br\s*/?>', ' ', content_html)
    cleaned = re.sub(r'<.*?>', '', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()

def get_domain_from_url(url):
    return urlparse(url).netloc

def process_url(url):
    # Remove any quotes and strip whitespace
    url = url.strip().replace('"', '')
    
    # Add https:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    status_id = parsed_url.path.split('/')[-1]

    mastodon = Mastodon(access_token=ACCESS_TOKEN, api_base_url=base_url)
    status = mastodon.status(status_id)
    user = status['account']
    domain = get_domain_from_url(user["url"])
    language = status.get("language", "")
    note = user.get("note", "")
    region = infer_region(language, domain, note)

    post_data = {
        "post_id": status["id"],
        "created_time": str(status["created_at"]),
        "content": extract_text(status["content"]),
        "url": status["url"],
        "language": language,
        "region": region,
        "author": {
            "acct": user["acct"],
            "display_name": user["display_name"],
            "created_time": str(user["created_at"]),
            "url": user["url"],
            "Domain": domain,
            "note": extract_text(note),
        },
        "favourited_by": [],
        "reblogged_by": [],
        "replies": []
    }

    for booster in mastodon.status_reblogged_by(status_id):
        booster_note = booster.get("note", "")
        booster_domain = get_domain_from_url(booster["url"])
        post_data["reblogged_by"].append({
            "acct": booster["acct"],
            "display_name": booster["display_name"],
            "created_time": str(booster["created_at"]),
            "url": booster["url"],
            "Domain": booster_domain,
            "note": extract_text(booster_note),
            "region": infer_region(booster.get("language", ""), booster_domain, booster_note)
        })

    for favouriter in mastodon.status_favourited_by(status_id):
        fav_note = favouriter.get("note", "")
        fav_domain = get_domain_from_url(favouriter["url"])
        post_data["favourited_by"].append({
            "acct": favouriter["acct"],
            "display_name": favouriter["display_name"],
            "created_time": str(favouriter["created_at"]),
            "url": favouriter["url"],
            "Domain": fav_domain,
            "note": extract_text(fav_note),
            "region": infer_region(favouriter.get("language", ""), fav_domain, fav_note)
        })

    context = mastodon.status_context(status_id)
    for reply in context['descendants']:
        account = reply["account"]
        reply_note = account.get("note", "")
        reply_domain = get_domain_from_url(account["url"])
        post_data["replies"].append({
            "acct": account["acct"],
            "display_name": account["display_name"],
            "created_time": str(account["created_at"]),
            "url": account["url"],
            "Domain": reply_domain,
            "note": extract_text(reply_note),
            "language": reply.get("language", ""),
            "region": infer_region(account.get("language", ""), reply_domain, reply_note),
            "content": extract_text(reply["content"]).strip()
        })

    

    return post_data

def main():

    update_yesterday_data()  

    # formatted_json = json.dumps(json_data, ensure_ascii=False)
    print(f"\n✅ finish！ deal with {len(json_data)} posts success。")
    return "OK"
if __name__ == "__main__":
    main()

