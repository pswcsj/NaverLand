"""
Naver Land Scraper

This script scrapes property listings from Naver Land (m.land.naver.com)
based on user-defined criteria such as location, transaction type,
property type, and price range.

It performs the following main steps:
1.  Collects user input for search criteria.
2.  Builds appropriate URLs to query Naver Land's API.
3.  Fetches data, handling potential issues like robot authentication prompts
    and JSON parsing.
4.  Extracts detailed information for each property listing.
5.  Saves the collected data into a CSV file named 'result.csv'.

Usage:
    Run this script from the command line:
    $ python main.py
    The script will then prompt for search criteria.
"""
import json
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- Global Constants ---
TYPE_DICT = {
    '매매': 'A1',
    '전세': 'B1',
    '월세': 'B2',
    '단기임대': 'B3'
}
PROPERTY_DICT = {
    '아파트': 'APT',
    '빌라': 'VL',
    '단독/다가구': 'DDDGG',
    '상가주택': 'SGJT',
    '원룸': 'OR',
    '상가': 'SG',
    '토지': 'TJ',
    '공장/창고': 'GJCG',
    '지식산업센터': 'APTHGJ',
    '건물': 'GM',
    '오피스텔': 'OPST',
    '아파트분양권': 'ABYG',
    '오피스텔분양권': 'OBYG',
    '재건축': 'JGC',
    '전원주택': 'JWJT',
    '한옥주택': 'HOJT',
    '재개발': 'JGB',
    '고시원': 'GSW',
    '사무실': 'SMS'
}
HEADER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/86.0.4240.198 Safari/537.36"
    ),
    'Referer': 'https://m.land.naver.com/'
}
DF_COLUMNS = [
    '거래 방식', '지역', '매물 종류', '가격대',
    '면적', '특징', '매물번호', '부동산', '상세정보 링크'
]
MAX_FETCH_RETRIES = 4 # e.g. 1 initial try + 3 retries = 4 total attempts
FETCH_RETRY_DELAY_SECONDS = 20 # Increased delay for CAPTCHA

# --- Helper Functions ---

def get_values_from_url(url_string):
    """
    Extracts geographic parameters from a Naver Land map URL string.

    Args:
        url_string (str): The URL string, typically from a map page response.
                          Expected to contain a segment like '.../map/lat:lon:zoom:cortarNo/...'

    Returns:
        tuple: A tuple containing (latitude, longitude, zoom_level, cortar_number).
               Returns (None, None, None, None) if parameters cannot be found.
               - lan (str): Latitude.
               - lon (str): Longitude.
               - z (str): Zoom level.
               - cortarNo (str): Administrative region code. Empty if not present.
    """
    if not url_string: return None, None, None, None # Handle empty URL string
    info_list = url_string.split('/')
    map_part_index = -1
    for i, part in enumerate(info_list):
        if ':' in part and part.count(':') >= 2:
            try:
                float(part.split(':')[0])
                float(part.split(':')[1])
                int(part.split(':')[2])
                map_part_index = i
                break
            except ValueError:
                continue
    if map_part_index == -1 or map_part_index >= len(info_list):
        print(f"Warning: Could not find map parameters (lat:lon:z) in URL: {url_string}")
        return None, None, None, None
    map_params = info_list[map_part_index].split(':')
    lan = map_params[0]
    lon = map_params[1]
    z = map_params[2]
    cortarNo = map_params[3] if len(map_params) > 3 else ''
    return lan, lon, z, cortarNo


def format_price_display(prc):
    """
    Formats a price value (integer) into a display string "X억 Y만" or "Y만".

    Args:
        prc (int or float or str): The price value, typically in units of '만' (10,000 Won).

    Returns:
        str: A formatted price string (e.g., "3억 5000만", "8000만")
             or "가격정보없음" if formatting fails.
    """
    if not isinstance(prc, (int, float)):
        try:
            prc = int(prc)
        except (ValueError, TypeError):
            return "가격정보없음"
    if prc >= 10000:
        billions = int(prc / 10000)
        ten_thousands = prc % 10000
        if ten_thousands > 0:
            return f"{billions}억 {ten_thousands}만"
        return f"{billions}억"
    return f"{prc % 10000}만"


def get_location_details(data_dict, headers):
    """
    Fetches and returns human-readable location details (address)
    based on latitude and longitude using Naver's geocoding API.

    Args:
        data_dict (dict): A dictionary containing 'lng' (longitude) and 'lat' (latitude).
        headers (dict): HTTP headers to use for the request.

    Returns:
        str: A formatted address string, or "-" if fetching or parsing fails.
    """
    if not all(k in data_dict for k in ('lng', 'lat')):
        print("Error: data_dict must contain 'lng' and 'lat' for get_location_details.")
        return "-"
    try:
        geo_url = (
            f"https://map.naver.com/v5/api/geocode"
            f"?request=coordsToaddr&version=1.0&sourcecrs=epsg:4326"
            f"&output=json&orders=addr"
            f"&coords={data_dict['lng']},{data_dict['lat']}"
        )
        response = requests.get(geo_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        json_text = soup.body.text if soup.body else soup.text
        json_data = json.loads(json_text)

        if not json_data.get('results'):
            print(f"Warning: 'results' not found in geocode API response "
                  f"for {data_dict.get('lng', 'N/A')},{data_dict.get('lat', 'N/A')}")
            return "-"
        json_ju = json_data['results'][0]
        area1 = json_ju['region']['area1']['name']
        area2 = json_ju['region']['area2']['name']
        area3 = json_ju['region']['area3']['name']
        area4 = json_ju['region']['area4']['name']
        land_num1 = json_ju['land']['number1']
        land_num2 = json_ju['land']['number2']
        location_geo = f"{area1} {area2} {area3} {area4} {land_num1}-{land_num2}"
        return location_geo.strip()
    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching location for "
              f"{data_dict.get('lng', 'N/A')},{data_dict.get('lat', 'N/A')}: {e}")
        return "-"
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"Error parsing location details for "
              f"{data_dict.get('lng', 'N/A')},{data_dict.get('lat', 'N/A')}: {e}")
        return "-"

def fetch_data_from_url(url, headers, is_json=True, 
                        max_retries=MAX_FETCH_RETRIES, 
                        retry_delay=FETCH_RETRY_DELAY_SECONDS):
    """
    Fetches data from a URL, handles potential robot authentication,
    and optionally parses JSON. Includes retry mechanism.

    Args:
        url (str): The URL to fetch data from.
        headers (dict): HTTP headers for the request.
        is_json (bool): If True, attempts to parse the response as JSON.
        max_retries (int): Maximum number of retries for recoverable errors.
        retry_delay (int): Delay in seconds between retries.

    Returns:
        dict or str or None: Parsed JSON, raw text, or None if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=15) # Increased timeout
            response.raise_for_status()

            # Check for Naver's robot authentication page
            if response.url == 'https://m.land.naver.com/error/abuse':
                print(f"CAPTCHA or error page encountered at {url}. "
                      f"Please manually solve the CAPTCHA in your browser for Naver Land "
                      f"or check the URL, then the script will retry automatically.")
                print(f"Attempt {attempt + 1} of {max_retries}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                continue # Go to next attempt

            if is_json:
                soup = BeautifulSoup(response.text, 'html.parser')
                json_content_str = None
                if soup.body and soup.body.string:
                    json_content_str = soup.body.string
                elif soup.string:
                    json_content_str = soup.string
                if not json_content_str:
                    script_tag = soup.find('script', type='application/json')
                    if script_tag:
                        json_content_str = script_tag.string
                
                if not json_content_str: # Still no JSON content
                    print(f"Warning: No JSON content found from {url} on attempt {attempt + 1}. "
                          f"Text: {response.text[:200]}.")
                    # This might be a non-CAPTCHA error page that's not JSON
                    # Consider it a failure for this attempt if JSON is expected
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else: # Last attempt
                        print(f"Failed to get valid JSON from {url} after {max_retries} attempts.")
                        return None
                try:
                    return json.loads(json_content_str)
                except json.JSONDecodeError as e_json:
                    print(f"JSONDecodeError for {url} on attempt {attempt + 1}: {e_json}. "
                          f"Text: {json_content_str[:200]}.")
                    # If it's not a CAPTCHA page but still fails JSON parsing, it's an issue.
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else: # Last attempt
                        print(f"Failed to decode JSON from {url} after {max_retries} attempts.")
                        return None
            return response.text # Return raw text if not JSON and successful

        except requests.exceptions.HTTPError as e_http:
            print(f"HTTP error for {url} on attempt {attempt + 1}: {e_http}. "
                  f"Status: {e_http.response.status_code}.")
            # Retry on 403 (Forbidden) as it might be temporary or CAPTCHA related
            if e_http.response.status_code == 403 and attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            # For other HTTP errors, or if last retry, fail.
            if attempt == max_retries -1 : print(f"Failed HTTP request to {url} after {max_retries} attempts.")
            return None 
        except requests.exceptions.RequestException as e_req:
            print(f"Network error while fetching {url} on attempt {attempt + 1}: {e_req}.")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay) # Basic network errors might resolve
                continue
            else: # Last attempt
                print(f"Failed network request to {url} after {max_retries} attempts.")
                return None
    
    print(f"Failed to fetch data from {url} after {max_retries} retries "
          f"due to persistent CAPTCHA or error.")
    return None


def get_cluster_info(map_response_url, property_type_code, transaction_type_code,
                     price_query_string, headers):
    lan, lon, z, cortarNo = get_values_from_url(map_response_url)
    if lan is None: return 0, ""
    effective_price_query = price_query_string[1:] if price_query_string.startswith('?') else price_query_string
    if effective_price_query and not effective_price_query.endswith('&'): effective_price_query += '&'
    cluster_url_params_str = (
        f"cortarNo={cortarNo}&rletTpCd={property_type_code}"
        f"&tradTpCd={transaction_type_code}&z={z}&lat={lan}&lon={lon}"
        f"&{effective_price_query}"
    )
    if cluster_url_params_str.endswith('&'):
        cluster_url_params_str = cluster_url_params_str[:-1]
    cluster_list_url = (
        f"https://m.land.naver.com/cluster/clusterList"
        f"?view=atcl&{cluster_url_params_str}"
    )
    print(f"Cluster List URL: {cluster_list_url}")
    json_data = fetch_data_from_url(cluster_list_url, headers, is_json=True)
    if not json_data or 'data' not in json_data or 'ARTICLE' not in json_data['data']:
        print("Error: Could not fetch/parse cluster data, or format is unexpected.")
        if json_data: print(f"Problematic JSON (first 200 chars): {str(json_data)[:200]}")
        return 0, cluster_url_params_str
    total_article_count = sum(item.get('count', 0) for item in json_data['data']['ARTICLE'])
    print(f"Total items found (total_article_count): {total_article_count}")
    return total_article_count, cluster_url_params_str


def get_user_inputs(type_dict, property_dict):
    loc = input("지역을 입력하세요 > ")
    transaction_type = ""
    while True:
        print(list(type_dict.keys()))
        type_input_str = input("원하는 거래 방식을 입력하세요 > ")
        if type_input_str in type_dict:
            transaction_type = type_input_str
            break
        print("잘못된 입력입니다. 다시 시도해주세요.")
    property_type_name = ""
    property_type_code = ""
    while True:
        print(list(property_dict.keys()))
        gunn_input_str = input("원하는 건물을 입력하세요 > ")
        if gunn_input_str in property_dict:
            property_type_name = gunn_input_str
            property_type_code = property_dict[gunn_input_str]
            break
        print("잘못된 입력입니다. 다시 시도해주세요.")
    price_info = {}
    # Basic validation could be added here to ensure price inputs are numeric strings
    # For now, assuming API handles non-numeric gracefully or user enters valid numbers.
    if transaction_type == '매매':
        price_info['priceMin'] = input("매매가의 최솟값을 입력하세요(만) > ")
        price_info['priceMax'] = input("매매가의 최댓값을 입력하세요(만) > ")
    elif transaction_type == '전세':
        price_info['priceMin'] = input("보증금의 최솟값을 입력하세요(만) > ")
        price_info['priceMax'] = input("보증금의 최댓값을 입력하세요(만) > ")
    elif transaction_type in ('월세', '단기임대'):
        price_info['priceWMin'] = input("보증금의 최솟값을 입력하세요(만) > ")
        price_info['priceWMax'] = input("보증금의 최댓값을 입력하세요(만) > ")
        price_info['priceMMin'] = input("월세의 최솟값을 입력하세요(만) > ")
        price_info['priceMMax'] = input("월세의 최댓값을 입력하세요(만) > ")
    return loc, transaction_type, property_type_name, property_type_code, price_info


def build_base_search_url(initial_loc, headers):
    current_loc = initial_loc
    max_location_retries = 3 # Limit retries for ambiguous location
    location_retry_count = 0
    while location_retry_count < max_location_retries:
        search_url = f"https://m.land.naver.com/search/result/{current_loc}"
        print(f"Attempting to get base map URL with: {search_url}")
        try:
            response = requests.get(search_url, headers=headers, allow_redirects=True, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error during base search URL fetch: {e}.")
            location_retry_count +=1
            current_loc = input(
                f"Failed to fetch for '{current_loc}'. Attempt {location_retry_count}/{max_location_retries}. "
                f"Enter a valid location or press Enter to exit: "
            )
            if not current_loc: return None, None
            continue
        print(f"Response URL after search: {response.url}")
        if response.url == 'https://m.land.naver.com/error/abuse':
            print("Robot authentication required for base search.")
            location_retry_count +=1
            current_loc = input(
                f"Please solve CAPTCHA and enter location again. Attempt {location_retry_count}/{max_location_retries} "
                f"(or press Enter to exit): "
            )
            if not current_loc: return None, None
            continue
        if '/map/' in response.url:
            try:
                map_index = response.url.split('/').index('map')
                base_map_url = '/'.join(response.url.split('/')[:map_index + 2])
                return base_map_url, response
            except ValueError:
                print(f"Error: 'map' in URL but could not parse: {response.url}")
                location_retry_count +=1
                current_loc = input(
                    f"Could not parse map URL. Attempt {location_retry_count}/{max_location_retries}. "
                    f"Enter specific location (or Enter to exit): "
                )
                if not current_loc: return None, None
                continue
        else:
            location_retry_count +=1
            current_loc = input(
                f"Location '{current_loc}' ambiguous. Attempt {location_retry_count}/{max_location_retries}. "
                f"Enter detailed location (or Enter to exit): "
            )
            if not current_loc: return None, None
    print(f"Failed to resolve location '{initial_loc}' after {max_location_retries} attempts.")
    return None, None


def build_detailed_search_url(base_map_url, transaction_type, property_code,
                              transaction_code, price_info):
    price_query_string = ""
    if transaction_type == '매매':
        price_query_string = (f"?dprcMin={price_info.get('priceMin', '')}"
                              f"&dprcMax={price_info.get('priceMax', '')}")
    elif transaction_type == '전세':
        price_query_string = (f"?wprcMin={price_info.get('priceMin', '')}"
                              f"&wprcMax={price_info.get('priceMax', '')}")
    elif transaction_type in ('월세', '단기임대'):
        price_query_string = (f"?wprcMin={price_info.get('priceWMin', '')}"
                              f"&wprcMax={price_info.get('priceWMax', '')}"
                              f"&rprcMin={price_info.get('priceMMin', '')}"
                              f"&rprcMax={price_info.get('priceMMax', '')}")
    if price_query_string and not price_query_string.endswith('&'): price_query_string += '&'
    final_navigation_url = (f"{base_map_url}/{property_code}/{transaction_code}"
                            f"{price_query_string if price_query_string else ''}")
    if final_navigation_url.endswith('&'): final_navigation_url = final_navigation_url[:-1]
    return final_navigation_url, price_query_string


def extract_article_details(article_item_data, headers, transaction_type, property_type_name):
    location_str = "-"
    try:
        if 'lat' in article_item_data and 'lng' in article_item_data:
            location_str = get_location_details(article_item_data, headers)
        else:
            print(f"Warning: lat/lng missing for articleNo {article_item_data.get('atclNo', 'N/A')}")
    except Exception as e:
        print(f"Error getting location for {article_item_data.get('atclNo', 'N/A')}: {e}")
    price_display_str = ""
    if transaction_type in ('매매', '전세'):
        price_display_str = format_price_display(article_item_data.get('prc', 0))
    elif transaction_type in ('월세', '단기임대'):
        deposit = format_price_display(article_item_data.get('prc', 0))
        rent = format_price_display(article_item_data.get('rentPrc', 0))
        price_display_str = f"{deposit}/{rent}"
    full_location_info = (f"{location_str} {article_item_data.get('atclNm', '')} "
                          f"{article_item_data.get('bildNm', '')} {article_item_data.get('flrInfo', '')}"
                         ).strip().replace("  ", " ")
    article_number = article_item_data.get('atclNo', '')
    return {
        '거래 방식': transaction_type, '지역': full_location_info,
        '매물 종류': property_type_name, '가격대': price_display_str,
        '면적': f"{article_item_data.get('spc1', '')}/{article_item_data.get('spc2', '')}",
        '특징': article_item_data.get('atclFetrDesc', '-'),
        '매물번호': article_number, '부동산': article_item_data.get('rltrNm', ''),
        '상세정보 링크': f"https://m.land.naver.com/article/info/{article_number}"
    }


def process_article_page(page_num, url_info_params, headers, transaction_type,
                         property_type_name, property_type_code):
    article_list_url = (f"https://m.land.naver.com/cluster/ajax/articleList"
                        f"?{url_info_params}sort=rank&page={page_num}")
    print(f"Fetching article page: {article_list_url}")
    json_page_data = fetch_data_from_url(article_list_url, headers)
    if not json_page_data:
        print(f"Failed to fetch data for page {page_num} from {article_list_url}")
        return []
    processed_articles_on_page = []
    article_list_from_response = []
    if isinstance(json_page_data, dict) and 'body' in json_page_data:
        article_list_from_response = json_page_data.get('body', [])
    elif isinstance(json_page_data, list):
        article_list_from_response = json_page_data
    else:
        print(f"Warning: Unexpected data structure for article list on page {page_num}. "
              f"Data (first 200 chars): {str(json_page_data)[:200]}")
        return []
    for item_data in article_list_from_response:
        if not isinstance(item_data, dict):
            print(f"Warning: Article item is not a dictionary: {item_data}")
            continue
        article_no = item_data.get('atclNo')
        if not article_no:
            print(f"Warning: Article item missing 'atclNo'. Item: {item_data}")
            continue
        if item_data.get('sameAddrCnt', 0) >= 2:
            jungbok_url = (f"https://m.land.naver.com/article/getSameAddrArticle"
                           f"?articleNo={article_no}")
            print(f"Fetching multi-listing details: {jungbok_url}")
            json_jungbok_data = fetch_data_from_url(jungbok_url, headers)
            if json_jungbok_data and isinstance(json_jungbok_data, list):
                for sub_item_data in json_jungbok_data:
                    if not isinstance(sub_item_data, dict):
                        print(f"Warning: Sub-item is not a dictionary: {sub_item_data}")
                        continue
                    processed_articles_on_page.append(
                        extract_article_details(sub_item_data, headers,
                                                transaction_type, property_type_name))
            elif json_jungbok_data:
                print(f"Warning: Expected list from jungbok_url but got "
                      f"{type(json_jungbok_data)}. URL: {jungbok_url}")
        else:
            processed_articles_on_page.append(
                extract_article_details(item_data, headers,
                                        transaction_type, property_type_name))
    return processed_articles_on_page


def save_to_csv(data_list, filename="result.csv", columns_order=None):
    if not columns_order: columns_order = DF_COLUMNS
    if not data_list:
        print("No listings found to save.")
        return
    try:
        df = pd.DataFrame(data_list, columns=columns_order)
        # Ensure all columns are present, add missing ones with default value (e.g. None or '-')
        for col in columns_order:
            if col not in df.columns:
                df[col] = "-" # Or pd.NA
        df = df[columns_order] # Reorder/select columns to match definition

        df.to_csv(filename, encoding='utf-8-sig', index=False)
        print(f"\nSuccessfully saved {len(df)} listings to {filename}")
        print("First 5 rows of the saved data:")
        print(df.head())
    except Exception as e:
        print(f"\nError saving DataFrame to CSV: {e}")


def main():
    print("Starting Naver Land Scraper...")
    (loc, transaction_type, property_type_name,
     property_type_code, price_info) = get_user_inputs(TYPE_DICT, PROPERTY_DICT)
    print(f"\n--- User Inputs ---"
          f"\nLocation: {loc}"
          f"\nTransaction Type: {transaction_type}"
          f"\nProperty Type Name: {property_type_name}"
          f"\nProperty Type Code: {property_type_code}"
          f"\nPrice Info: {price_info}")
    raw_base_map_url, map_page_response = build_base_search_url(loc, HEADER)
    if not (raw_base_map_url and map_page_response and map_page_response.url):
        print("Could not obtain a valid base map URL. Exiting.")
        return
    print(f"\n--- Base Search URL ---"
          f"\nRaw Base Map URL: {raw_base_map_url}"
          f"\nActual Map Page URL: {map_page_response.url}")
    transaction_type_api_code = TYPE_DICT[transaction_type]
    (nav_url_with_all_params, price_query_str) = build_detailed_search_url(
        raw_base_map_url, transaction_type, property_type_code,
        transaction_type_api_code, price_info)
    print(f"\n--- Detailed Search URL Components ---"
          f"\nConceptual Navigation URL: {nav_url_with_all_params}"
          f"\nPrice Query String for API: {price_query_str}")
    print(f"Fetching cluster info using URL: {map_page_response.url}")
    (total_items_count, cluster_api_params_str) = get_cluster_info(
        map_page_response.url, property_type_code,
        transaction_type_api_code, price_query_str, HEADER)
    if total_items_count == 0 and not cluster_api_params_str: # Critical failure in get_cluster_info
        print("Failed to get cluster information. Cannot proceed. Exiting.")
        return
    print(f"\n--- Cluster Info ---"
          f"\nTotal items: {total_items_count}"
          f"\nCluster API Parameters: {cluster_api_params_str}")
    all_article_listings = []
    if total_items_count > 0 and cluster_api_params_str:
        num_pages = (total_items_count + 19) // 20
        print(f"Calculated number of pages: {num_pages}")
        for i in range(1, num_pages + 1):
            print(f"\nProcessing page {i} of {num_pages}...")
            page_listings_data = process_article_page(
                i, cluster_api_params_str, HEADER, transaction_type,
                property_type_name, property_type_code)
            if page_listings_data: all_article_listings.extend(page_listings_data)
            print(f"Processed page {i}, found {len(page_listings_data)} listings. "
                  f"Total so far: {len(all_article_listings)}")
            if i < num_pages:
                print("Sleeping for 1 second...")
                time.sleep(1)
    else:
        print("No items found or cluster URL parameters missing. Skipping articles.")
    save_to_csv(all_article_listings, "result.csv", columns_order=DF_COLUMNS)
    print("\nScript finished.")

if __name__ == "__main__":
    main()
