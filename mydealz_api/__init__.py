import hmac
import time
import json
import urllib
from hashlib import sha1
from random import randint
from http import HTTPStatus
from base64 import encodebytes

import requests

MAIN_ENDPOINT = "https://www.mydealz.de/rest_api/v2/thread"
SEARCH_ENDPOINT = "https://www.mydealz.de/rest_api/v2/search/suggestions"
PRODUCT_ENDPOINT = "https://www.mydealz.de/rest_api/v2/thread/{}"
COMMENTS_ENDPOINT = "https://www.mydealz.de/rest_api/v2/thread/{}/comments"

class MyDealz:
    GROUP_MAPPING = dict()
    DISCUSSION_MAPPING = dict()
    MERCHANT_MAPPING = dict()
    
    def _headers(self, endpoint_url: str, query: dict) -> dict:
        hmac_key = "f0561bf4d666c1cfe942390bc2761a9ce02cedb8&"  # TODO look at this again
        hmac_key = hmac_key.encode()
        
        # set pre-defined authorization-header parameters
        authorization = {
            "oauth_consumer_key":"83561944886fdab16690e78a1f5f5559846dd86d",
            "oauth_nonce": str(randint(-2**63, 2**63-1)),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_version": "1.0",
        }
        
        # create signature
        request_method = "GET"
        endpoint_url = urllib.parse.quote_plus(endpoint_url)
        if query.get("criteria"):
            query["criteria"] = urllib.parse.quote(query["criteria"])
        query.update(authorization)
        query = {k: v for k,v in sorted(query.items(), key=lambda item: item[0])}
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        query = urllib.parse.quote_plus(query)
        message = "&".join([request_method, endpoint_url, query])
        message = message.encode()
        signature = hmac.new(hmac_key, message, sha1).digest()
        signature = encodebytes(signature)
        signature = signature.decode().strip()
        authorization["oauth_signature"] = urllib.parse.quote_plus(signature)
        
        # header
        user_agent = "com.tippingcanoe.mydealz ANDROID [v7.05.02] [30 | sdk_gphone_x86_64] [@2.625x]"
        authorization = f"""OAuth { ",".join([f'{k}="{v}"' for k,v in authorization.items()]) }"""
        return {
            "user-agent": user_agent,
            "authorization": authorization,
        }
    
    def _create_query(self, *, 
                      group_id=False, 
                      merchant_id=False, 
                      only_discussions: bool = None, 
                      only_vouchers: bool = None, 
                      search_query: str = None, 
                      tab, 
                      only_online, 
                      only_non_expired, 
                      whereabouts, 
                      after = -1, 
                      history_item_needed: bool = None,
                      limit = None):
        query = dict()

        if search_query != None:
            payload = {"query": search_query}
            payload.update({"tab": tab})
        else:
            payload = {"tab": tab}
        if only_discussions != None:
            payload.update({"only_discussions": only_discussions})
        if only_vouchers != None:
            payload.update({"only_vouchers": only_vouchers})
        if group_id:
            payload.update({"group_id": group_id})
        if merchant_id:
            payload.update({"merchant_id": merchant_id})
        if only_non_expired:
            payload.update({"only_non_expired": True})
        if only_online:
            payload.update({"only_online": True})
        payload.update({"whereabouts": whereabouts})
        payload = json.dumps(payload, separators=(",", ":"))
        
        if after != -1:
            query.update({"after": after})
        query.update({"criteria": payload})
        if history_item_needed:
            query.update({"history_item_needed": "true"})
        else:
            query.update({"history_item_needed": "false"})
        if limit:
            query.update({"limit": limit})
        
        return query
    
    def deals_overview(self, tab: str, *, after: int | str = -1, only_online: bool = False, only_non_expired: bool = False):  
        """
        tab: "featured", "hottest_day", "hottest_overall", "hottest_week", "hottest_month", "hot", "new", "discussed"
        after: can be -> a timestamp, like 1726515436  (for tab "new", "hot", "discussed")
                      -> p_00250, i.e. the number (250) of still available elements to show  (for tab "featured")
                      -> 0000002071, i.e. the score over which elements are being shown  (for tab "hottest_...")
        """
        query = self._create_query(
            tab=tab,
            only_online=only_online,
            only_non_expired=only_non_expired,
            whereabouts="deals",
            after=after,
            history_item_needed=False,
            limit=25
        )
        
        headers = self._headers(MAIN_ENDPOINT, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([MAIN_ENDPOINT, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")
        
    def groups(self, tab, group_id: int, *, after: int | str = -1, only_online: bool = False, only_non_expired: bool = False):
        """
        tab: "new", "hot"
        after: timestamp
        """
        query = self._create_query(
            tab=tab,
            group_id=group_id,
            only_online=only_online,
            only_non_expired=only_non_expired,
            whereabouts="group",
            after=after,
            history_item_needed=False,
            limit=25
        )
        
        headers = self._headers(MAIN_ENDPOINT, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([MAIN_ENDPOINT, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")
        
    def discussions(self, tab, group_id: int = None, *, after: int | str = -1, only_online: bool = False, only_non_expired: bool = False):
        """tab: "new", "discussed" """
        query = self._create_query(
            tab=tab,
            group_id=group_id,
            only_online=only_online,
            only_non_expired=only_non_expired,
            whereabouts="discussions",
            after=after,
            history_item_needed=False,
            limit=25
        )
        
        headers = self._headers(MAIN_ENDPOINT, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([MAIN_ENDPOINT, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")

    def merchants(self, tab, merchant_id: int, *, after: int | str = -1, only_online: bool = False, only_non_expired: bool = False):
        """tab: "deals", "vouchers" """
        query = self._create_query(
            tab=tab,
            merchant_id=merchant_id,
            only_online=only_online,
            only_non_expired=only_non_expired,
            whereabouts="merchant",
            after=after,
            history_item_needed=False,
            limit=25
        )

        headers = self._headers(MAIN_ENDPOINT, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([MAIN_ENDPOINT, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")
    
    def search(self, search_query: str, deal: bool = None, discussions: bool = None, *, only_online: bool = False, only_non_expired: bool = False):
        """deal _or_ discussions has to be True."""
        if (deal and discussions) or (deal == None and discussions == None):
            print("not allowed")
            return
        if deal:
            only_discussions = False
            only_vouchers = False
        if discussions:
            only_discussions = True
            only_vouchers = None
            
        query = self._create_query(
            search_query=search_query,
            tab="new",
            only_discussions=only_discussions,
            only_vouchers=only_vouchers,
            only_non_expired=only_non_expired,
            only_online=only_online,
            whereabouts="search"
        )
        
        headers = self._headers(MAIN_ENDPOINT, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([MAIN_ENDPOINT, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")
    
    def search_suggestions(self, search_query: str):
        payload = {"query": search_query}
        payload = json.dumps(payload, separators=(",", ":"))
        query = {"criteria": payload}
        headers = self._headers(SEARCH_ENDPOINT, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([SEARCH_ENDPOINT, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")
        
    def product(self, product_id: int):
        query = {
            "history_item_needed": "false",
            "mark_as_seen": "true",
        }
        url = PRODUCT_ENDPOINT.format(product_id)
        headers = self._headers(url, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([url, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")
    
    def comments(self, product_id: int, sort_by: str = "newest_first", limit: int = 25):
        """sort_by: "most_helpful", "oldest_first", "newest_first", "top_first" """
        query = {
            "sort_by": sort_by,
            "include_pinned_comments": "true",
            "mark_as_seen": "true",
            "limit": limit,
            "exclude_inactive": "false",
        }
        url = COMMENTS_ENDPOINT.format(product_id)
        headers = self._headers(url, query)
        query = "&".join([f"{k}={v}" for k,v in query.items()])
        url = "?".join([url, query])
        
        response = requests.get(url, headers=headers)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            print("error")
    

class Discover:
    """Discover group_ids (discussions), group_ids (groups, i.e. categories) and merchant_ids."""
    # TODO
    pass


if __name__ == "__main__":
    # examples/testing
    ins = MyDealz()
    ins.deals_overview("new")
    ins.groups("new", group_id=1)
    ins.discussions("new", group_id=2041)
    ins.merchants(tab="deals", merchant_id=49)
    ins.search("penny", deal=True)
    ins.search_suggestions("penny")
    ins.product(2425810)
    ins.comments(2425810)