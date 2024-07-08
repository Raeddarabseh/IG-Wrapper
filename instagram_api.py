#!/usr/bin/python3
import os
import sys
import json
import uuid
import requests
import configparser
from Crypto.Hash import SHA256, HMAC


class Instagram:
    def __init__(self, mariam_darabseh, 0785579996):
        self.session = requests.session()
        self.username = username
        self.password = 0785579996
        self.device_id = "DADA237D-CB58-4D4D-8096-2F5E172921A3"
        self.pk = None
        self.csrftoken = None
        self.base_url = "https://i.instagram.com/api/v1/"
        self.secret_key = (
            "ac5f26ee05af3e40a81b94b78d762dc8287bcdd8254fe86d0971b2aded8884a4"
        )
        self.key_version = "4"
        self.headers = {
            "Host": "i.instagram.com",
            "X-IG-Connection-Speed": "44kbps",
            "Accept": "*/*",
            "X-IG-Connection-Type": "WiFi",
            "X-IG-App-ID": "124024574287414",
            "Accept-Language": "en-US;q=1",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-IG-ABR-Connection-Speed-KBPS": "0",
            "User-Agent": "Instagram 39.0.0.12.95 (iPhone6,1; iOS 10_2; en_US; en-US; scale=2.00; gamut=normal; 640x1136) AppleWebKit/420+",
            "Connection": "keep-alive",
            "X-IG-Capabilities": "36r/Bw==",
        }

    def calculate_hash(self, message):
        # json.dumps(dicthere).replace(' ','')
        # ensure message param is string-ed dict
        hmac = HMAC.new(self.secret_key.encode(), message.encode(), SHA256)
        return hmac.hexdigest()

    def reorder_signed_body(self, signed_body_json):
        key_association = {}
        reordered_dict = {}
        for key in list(signed_body_json.keys()):
            result = 0
            for char in key:
                result = (-result + (result << 5) + ord(char)) & 0xFFFFFFFF
            if sys.maxsize > 2 ** 32:  # if os is 64 bit
                if result > 0x7FFFFFFF:
                    result -= 0x100000000
                elif result < -0x80000000:
                    result += 0x100000000
            key_association[key] = result
        hash_sorted_keys = sorted(key_association.items(), key=lambda x: x[1])
        for t in hash_sorted_keys:
            reordered_dict[t[0]] = signed_body_json[t[0]]
        return reordered_dict

    def generate_signed_body(self, signed_body_dict):
        reordered_stringed_dict = json.dumps(
            self.reorder_signed_body(signed_body_dict)
        ).replace(" ", "")
        signed_hash = self.calculate_hash(reordered_stringed_dict)
        return f"{signed_hash}.{reordered_stringed_dict}"

    def make_request(
        self,
        method,
        endpoint,
        params=None,
        data=None,
        json=None,
        headers=None,
        json_content=True,
    ):
        res = self.session.request(
            method,
            f"{self.base_url}{endpoint}",
            params=params,
            data=data,
            json=json,
            headers=headers,
        )
        # print(f"{res} {res.content}")
        # print(params)
        # print(json)
        # print(data)

        if json_content is True:
            return res.json()
        return res

    def login_2fa(self, username, code_2fa, id_2fa):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "username": username,
                    "adid": "uuid-adid",
                    "device_id": self.device_id,
                    "two_factor_identifier": str(id_2fa),
                    "verification_code": str(code_2fa),
                }
            ),
            "ig_sig_key_version": self.key_version,
        }

        login_2fa_response = self.make_request(
            "POST",
            "accounts/two_factor_login/",
            data=data,
            headers=self.headers,
            json_content=False,
        )
        return login_2fa_response

    def login(self):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "reg_login": "0",
                    "password": self.password,
                    "device_id": self.device_id,
                    "username": self.username,
                    "adid": "uuid-adid",
                    "login_attempt_count": "0",
                    "phone_id": self.device_id,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        login_response = self.make_request(
            "POST",
            "accounts/login/",
            data=data,
            headers=self.headers,
            json_content=False,
        )
        if login_response.json().get("two_factor_required"):
            code_2fa = input("[*] 2fa required - Enter code received: ")
            username = login_response.json().get("two_factor_info").get("username")
            id_2fa = (
                login_response.json()
                .get("two_factor_info")
                .get("two_factor_identifier")
            )
            login_response = self.login_2fa(username, code_2fa, id_2fa)

        self.pk = str(login_response.json()["logged_in_user"]["pk"])
        self.csrftoken = login_response.cookies["csrftoken"]
        return login_response.json()

    def logout(self):
        data = {"device_id": self.device_id}
        return self.make_request(
            "POST", "accounts/logout/", data=data, headers=self.headers
        )

    def change_password(self, new_password):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "old_password": self.password,
                    "new_password1": new_password,
                    "_uuid": self.device_id,
                    "new_password2": new_password,
                    "_uid": self.pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", "accounts/change_password/", data=data, headers=self.headers
        )

    def get_dms(self):
        query_string_params = {
            "use_unified_inbox": "true",
            "push_disabled": "true",
            "persistentBadging": "true",
        }
        return self.make_request(
            "GET", "direct_v2/inbox/", params=query_string_params, headers=self.headers
        )

    def get_autocomplete_list(self):
        query_string_params = {"version": "2"}
        return self.make_request(
            "GET",
            "friendships/autocomplete_user_list/",
            params=query_string_params,
            headers=self.headers,
        )

    def get_reels(self):
        return self.make_request("GET", "feed/reels_tray/", headers=self.headers)

    def get_news_inbox(self):
        query_string_params = {"push_disabled": "true"}
        return self.make_request(
            "GET", "news/inbox/", params=query_string_params, headers=self.headers
        )

    def get_timeline(self):
        data = {
            "phone_id": self.device_id,
            "_csrftoken": self.pk,
            "seen_posts": "",
            "timezone_offset": "-14400",
            "is_charging": "0",
            "battery_level": "20",
            "will_sound_on": "0",
            "_uuid": self.device_id,
            "recovered_from_crash": "1",
            "feed_view_info": "",
            "reason": "cold_start_fetch",
            "session_id": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "unseen_posts": "",
            "is_async_ads": "0",
            "is_prefetch": "0",
        }
        feed_headers = {
            "Host": "i.instagram.com",
            "X-FB": "0",
            "family_device_id": self.device_id,
            "X-IG-Connection-Speed": "44kbps",
            "Accept": "*/*",
            "X-IG-Connection-Type": "WiFi",
            "X-IG-App-ID": "124024574287414",
            "Accept-Language": "en-US;q=1",
            "Accept-Encoding": "gzip, deflate",
            "X-IDFA": str(uuid.uuid4()).upper(),
            "X-Ads-Opt-Out": "0",
            "X-IG-ABR-Connection-Speed-KBPS": "0",
            "User-Agent": "Instagram 39.0.0.12.95 (iPhone6,1; iOS 10_2; en_US; en-US; scale=2.00; gamut=normal; 640x1136) AppleWebKit/420+",
            "X-DEVICE-ID": self.device_id,
            "X-IG-Capabilities": "36r/Bw==",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        return self.make_request(
            "POST", "feed/timeline/", data=data, headers=feed_headers
        )

    def get_users_feed(self, user_pk):
        return self.make_request(
            "GET", f"feed/user/{str(user_pk)}/", headers=self.headers
        )

    def get_notifications_badge(self):
        data = {
            "_csrftoken": self.csrftoken,
            "_uuid": self.device_id,
            "user_ids": self.pk,
            "device_id": self.device_id,
        }
        return self.make_request(
            "POST", "notifications/badge/", data=data, headers=self.headers
        )

    def register(self, device_token):
        data = {
            "_csrftoken": self.csrftoken,
            "users": self.pk,
            "_uuid": self.device_id,
            "device_id": self.device_id,
            "device_token": device_token,
            "device_type": "ios",
        }
        query_string_params = {"platform": "12", "device_type": "ios"}
        return self.make_request(
            "POST",
            "push/register/",
            data=data,
            params=query_string_params,
            headers=self.headers,
        )

    def get_recent_searches(self):
        return self.make_request(
            "GET", "fbsearch/recent_searches/", headers=self.headers
        )

    def get_hidden_search_entities(self):
        return self.make_request(
            "GET", "fbsearch/get_hidden_search_entities/", headers=self.headers
        )

    def get_suggested_searches_user_type(self):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "type": "users",
        }
        return self.make_request(
            "GET",
            "fbsearch/suggested_searches/",
            params=query_string_params,
            headers=self.headers,
        )

    def get_suggested_searches_blended_type(self):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "type": "blended",
        }
        return self.make_request(
            "GET",
            "fbsearch/suggested_searches/",
            params=query_string_params,
            headers=self.headers,
        )

    def get_explore_page(self):
        query_string_params = {
            "session_id": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "is_ptr": "true",
            "surface": "grid",
            "timezone_offset": "-14400",
        }
        return self.make_request(
            "GET", "discover/explore/", params=query_string_params, headers=self.headers
        )

    def get_nearby_places(self, latitude, longitude):
        query_string_params = {
            "lat": float(latitude),
            "timezone_offset": "-14400",
            "lng": float(longitude),
        }
        return self.make_request(
            "GET", "fbsearch/places/", params=query_string_params, headers=self.headers
        )

    def get_search_places(self, latitude, longitude, place):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "lat": float(latitude),
            "lng": float(longitude),
            "query": str(place),
            "timezone_offset": "-14400",
        }
        return self.make_request(
            "GET", "fbsearch/places/", params=query_string_params, headers=self.headers
        )

    def search_tags(self, tag):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "q": str(tag),
            "is_typeahead": "true",
            "timezone_offset": "-14400",
        }
        return self.make_request(
            "GET", "tags/search/", params=query_string_params, headers=self.headers
        )

    def related_tags(self, tag):
        query_string_params = {
            "visited": f'[{{"id":"{tag}","type":"hashtag"}}]',
            "related_types": '["location","hashtag"]',
        }
        return self.make_request(
            "GET",
            f"v1/tags/{tag}/related/",
            params=query_string_params,
            headers=self.headers,
        )

    def get_tag_info(self, tag):
        return self.make_request("GET", f"tags/{tag}/info/", headers=self.headers)

    def get_tag_feed(self, tag):
        return self.make_request("GET", f"feed/tag/{tag}/", headers=self.headers)

    def search_top(self, search_string):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "query": search_string,
            "context": "blended",
            "timezone_offset": "-14400",
        }
        return self.make_request(
            "GET",
            "fbsearch/topsearch_flat/",
            params=query_string_params,
            headers=self.headers,
        )

    def search_people(self, search_string):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "query": search_string,
            "is_typeahead": "true",
            "timezone_offset": "-14400",
        }
        return self.make_request(
            "GET", "users/search/", params=query_string_params, headers=self.headers
        )

    def get_top_live(self):
        return self.make_request("GET", "discover/top_live/", headers=self.headers)

    def get_news(self):
        return self.make_request("GET", "news/", headers=self.headers)

    def get_news_log(self):
        data = {
            "_csrftoken": self.csrftoken,
            "pk": self.pk,
            "_uuid": self.device_id,
            "action": "click",
        }  # encoded???
        return self.make_request("POST", "news/log/", data=data, headers=self.headers)

    def get_pending(self):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "rank_mutual": "0",
        }
        return self.make_request(
            "GET",
            " friendships/pending/",
            params=query_string_params,
            headers=self.headers,
        )

    def get_friendship_status(self, user_ids_array):
        data = {
            "_csrftoken": self.csrftoken,
            "include_reel_info": "0",
            "_uuid": self.device_id,
            "user_ids": ",".join(map(str, user_ids_array)),
        }
        return self.make_request(
            "POST", "friendships/show_many/", data=data, headers=self.headers
        )

    def get_user_info(self, user_pk):
        query_string_params = {
            "device_id": self.device_id,
            "from_module": "feed_timeline",
        }
        return self.make_request(
            "GET",
            f"users/{user_pk}/info/",
            params=query_string_params,
            headers=self.headers,
        )

    def show_friendship(self, user_pk):
        return self.make_request(
            "GET", f"friendships/show/{user_pk}/", headers=self.headers
        )

    def get_users_story(self, user_pk):
        return self.make_request(
            "GET", f"feed/user/{user_pk}/story/", headers=self.headers
        )

    def get_users_highlights_reel(self, user_pk):
        return self.make_request(
            "GET", f"highlights/{user_pk}/highlights_tray/", headers=self.headers
        )

    def mute_real(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "tray_position": "13",
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "_csrftoken": self.csrftoken,
                    "reel_type": "story",
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            f"friendships/mute_friend_reel/{user_pk}/",
            data=data,
            headers=self.headers,
        )

    def follow(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "user_id": user_pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"friendships/create/{user_pk}/", data=data, headers=self.headers
        )

    def unfollow(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "user_id": user_pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"friendships/destroy/{user_pk}/", data=data, headers=self.headers
        )

    def get_users_followings(self, user_pk):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "rank_mutual": "0",
        }
        return self.make_request(
            "GET",
            f"friendships/{user_pk}/following/",
            params=query_string_params,
            headers=self.headers,
        )

    def search_users_followings(self, user_pk, search_string):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "query": search_string,
            "rank_mutual": "0",
        }
        return self.make_request(
            "GET",
            f"friendships/{user_pk}/following/",
            params=query_string_params,
            headers=self.headers,
        )

    def get_users_followers(self, user_pk):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "rank_mutual": "0",
        }
        return self.make_request(
            "GET",
            f"friendships/{user_pk}/followers/",
            params=query_string_params,
            headers=self.headers,
        )

    def search_users_followers(self, user_pk, search_string):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "query": search_string,
            "rank_mutual": "0",
        }
        return self.make_request(
            "GET",
            f"friendships/{user_pk}/followers/",
            params=query_string_params,
            headers=self.headers,
        )

    def get_users_followed_tags(self, user_pk):
        return self.make_request(
            "GET", f"users/{user_pk}/following_tags_info/", headers=self.headers
        )

    def block_user(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "user_id": user_pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"friendships/block/{user_pk}/", data=data, headers=self.headers
        )

    def unblock_user(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "user_id": user_pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"friendships/unblock/{user_pk}/", data=data, headers=self.headers
        )

    def get_user_tagged_media(self, user_pk):
        return self.make_request(
            "GET", f"usertags/{user_pk}/feed/", headers=self.headers
        )

    def turn_on_users_post_notifications(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {"_uuid": self.device_id, "_uid": self.pk, "_csrftoken": self.csrftoken}
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"friendships/favorite/{user_pk}/", data=data, headers=self.headers
        )

    def turn_off_users_post_notifications(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {"_uuid": self.device_id, "_uid": self.pk, "_csrftoken": self.csrftoken}
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            f"friendships/unfavorite/{user_pk}/",
            data=data,
            headers=self.headers,
        )

    def get_all_saved(self):
        return self.make_request("GET", "feed/saved/", headers=self.headers)

    def get_saved_collections(self):
        return self.make_request("GET", "collections/list/", headers=self.headers)

    def create_dm_thread(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "use_unified_inbox": "true",
                    "_uuid": self.device_id,
                    "recipient_users": f"[{user_pk}]",
                    "_uid": self.pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", "direct_v2/create_group_thread/", data=data, headers=self.headers
        )

    def get_dm_thread_contents(self, thread_id):
        query_string_params = {"use_unified_inbox": "true"}
        return self.make_request(
            "GET",
            f"direct_v2/threads/{thread_id}/",
            params=query_string_params,
            headers=self.headers,
        )

    def mute_dm_thread(self, thread_id):
        data = {
            "_uuid": self.device_id,
            "_csrftoken": self.csrftoken,
            "use_unified_inbox": "true",
        }
        return self.make_request(
            "POST",
            f"direct_v2/threads/{thread_id}/mute/",
            data=data,
            headers=self.headers,
        )

    def unmute_dm_thread(self, thread_id):
        data = {
            "_uuid": self.device_id,
            "_csrftoken": self.csrftoken,
            "use_unified_inbox": "true",
        }
        return self.make_request(
            "POST",
            f"direct_v2/threads/{thread_id}/unmute/",
            data=data,
            headers=self.headers,
        )

    def delete_dm_thread(self, thread_id):
        data = {
            "_uuid": self.device_id,
            "_csrftoken": self.csrftoken,
            "use_unified_inbox": "true",
        }
        return self.make_request(
            "POST",
            f"direct_v2/threads/{thread_id}/hide/",
            data=data,
            headers=self.headers,
        )

    def hide_search_entity(self, user_pk):
        data = {
            "_csrftoken": self.csrftoken,
            "_uuid": self.device_id,
            "section": "suggested",
            "user": f"[{user_pk}]",
        }
        return self.make_request(
            "POST", "fbsearch/hide_search_entities/", data=data, headers=self.headers
        )

    def clear_search_history(self):
        data = {"_uuid": self.device_id, "_csrftoken": self.csrftoken}
        return self.make_request(
            "POST", "fbsearch/clear_search_history/", data=data, headers=self.headers
        )

    def get_all_liked_posts(self):
        return self.make_request("GET", "feed/liked/", headers=self.headers)

    def get_blocked_list(self):
        return self.make_request("GET", "users/blocked_list/", headers=self.headers)

    def approve_user_follow(self, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "user_id": user_pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"friendships/approve/{user_pk}/", data=data, headers=self.headers
        )

    def save_post(self, media_id, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "module_name": "single_feed_profile",
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"media/{media_id}_{user_pk}/save/", data=data, headers=self.headers
        )

    def unsave_post(self, media_id, user_pk):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "module_name": "single_feed_profile",
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        print(f"media/{media_id}_{user_pk}/unsave/")
        return self.make_request(
            "POST",
            f"media/{media_id}_{user_pk}/unsave/",
            data=data,
            headers=self.headers,
        )

    def like_post(self, media_id, user_pk, double_tapped):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "module_name": "photo_view",
                    "media_id": f"{media_id}'_'{user_pk}",
                    "user_id": user_pk,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        query_string_params = {"d": str(str(double_tapped) == "True")}
        return self.make_request(
            "POST",
            f"media/{media_id}_{user_pk}/like/",
            params=query_string_params,
            data=data,
            headers=self.headers,
        )

    def unlike_post(self, media_id, user_pk, double_tapped):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "module_name": "photo_view",
                    "media_id": f"{media_id}'_'{user_pk}",
                    "user_id": user_pk,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            f"media/{media_id}_{user_pk}/unlike/",
            data=data,
            headers=self.headers,
        )

    def comment(self, media_id, user_pk, comment_text):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "comment_text": comment_text,
                    "idempotence_token": "idempotence_token",
                    "containermodule": "comments_v2_single_feed_profile",
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            f"media/{media_id}_{user_pk}/comment/",
            data=data,
            headers=self.headers,
        )

    def like_comment(self, comment_id):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "comment_id": comment_id,
                    "_uid": self.pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", f"media/{comment_id}/comment_like/", data=data, headers=self.headers
        )

    def see_comment_likes(self, comment_id):
        query_string_params = {
            "rank_token": f"{self.pk}_{str(uuid.uuid4()).upper()}",
            "rank_mutual": "0",
        }
        return self.make_request(
            "GET",
            f"media/{comment_id}/comment_likers/",
            params=query_string_params,
            headers=self.headers,
        )

    def unlike_comment(self, comment_id):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "comment_id": comment_id,
                    "_uid": self.pk,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            f"media/{comment_id}/comment_unlike/",
            data=data,
            headers=self.headers,
        )

    def remove_comment(self, media_id, user_pk, comment_id):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "comment_ids_to_delete": comment_id,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "_csrftoken": self.csrftoken,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            f"media/{media_id}_{user_pk}/comment/bulk_delete/",
            data=data,
            headers=self.headers,
        )

    def reply_comment(self, reply_text, parent_comment_id):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "containermodule": "comments_v2_single_feed_profile",
                    "comment_text": reply_text,
                    "replied_to_comment_id": parent_comment_id,
                    "parent_comment_id": parent_comment_id,
                    "idempotence_token": "idempotence_token",
                    "_csrftoken": self.csrftoken,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            f"media/{media_id}_{user_pk}/comment/",
            data=data,
            headers=self.headers,
        )

    def get_account_security_info(self):
        data = {
            "signed_body": self.generate_signed_body(
                {"_uuid": self.device_id, "_uid": self.pk, "_csrftoken": self.csrftoken}
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", "accounts/account_security_info/", data=data, headers=self.headers
        )

    def send_2FA_activation(self, phone_number):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "device_id": self.device_id,
                    "phone_number": f"+1{phone_number}",
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST",
            "accounts/send_two_factor_enable_sms/",
            data=data,
            headers=self.headers,
        )

    def enable_2FA(self, phone_number, verification_number):
        data = {
            "signed_body": self.generate_signed_body(
                {
                    "_csrftoken": self.csrftoken,
                    "_uuid": self.device_id,
                    "_uid": self.pk,
                    "device_id": self.device_id,
                    "phone_number": f"+1{phone_number}",
                    "verification_code": verification_number,
                }
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", "accounts/enable_sms_two_factor/", data=data, headers=self.headers
        )

    def regenerate_backup_codes(self):
        data = {
            "signed_body": self.generate_signed_body(
                {"_uuid": self.device_id, "_uid": self.pk, "_csrftoken": self.csrftoken}
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", "accounts/regen_backup_codes/", data=data, headers=self.headers
        )

    def disable_2FA(self):
        data = {
            "signed_body": self.generate_signed_body(
                {"_uuid": self.device_id, "_uid": self.pk, "_csrftoken": self.csrftoken}
            ),
            "ig_sig_key_version": self.key_version,
        }
        return self.make_request(
            "POST", "accounts/disable_sms_two_factor/", data=data, headers=self.headers
        )

    def get_users_recent_posts(self, pk):
        recent_posts = {}
        post_number = 1
        for item in IG.get_users_feed(user_pk)["items"]:
            carousel_media = []
            if item.get("carousel_media") is not None:
                # multiple media post
                for media in item.get("carousel_media"):
                    if (
                        media.get("video_duration") is None
                    ):  # TODO use media_type 1=image, 2=video
                        # post is an image
                        carousel_media.append(
                            media["image_versions2"]["candidates"][0]["url"]
                        )
                    else:
                        carousel_media.append(media["video_versions"][0]["url"])
                recent_posts.update({post_number: carousel_media})
            elif item.get("video_duration") is None:
                # post is an image
                recent_posts.update(
                    {post_number: item["image_versions2"]["candidates"][0]["url"]}
                )
            else:
                recent_posts.update({post_number: item["video_versions"][0]["url"]})
            post_number += 1
        return recent_posts


# adid is uuid

root_directory = os.getcwd()
cfg = configparser.ConfigParser()
configFilePath = os.path.join(root_directory, "config.cfg")
cfg.read(configFilePath)
username, password = cfg.get("login", "username"), cfg.get("login", "password")

IG = Instagram(username, password)
IG.login()
search_results = IG.search_top("zweed4u")
top_result = search_results["list"][0]  # first result of the search
user_pk = top_result["user"]["pk"]
# print(json.dumps(IG.get_users_recent_posts(user_pk), indent=4))

import time

saved_posts = IG.get_all_saved()
while len(saved_posts["items"]):
    for saved_post in saved_posts["items"]:
        print(f"Removing ...")
        # pk , id.split(_)[1]
        IG.unsave_post(
            saved_post["media"]["pk"], saved_post["media"]["id"].split("_")[1]
        )
    print("Fetching next batch of saved posts and sleeping to avoid rate limiting...")
    saved_posts = IG.get_all_saved()
    time.sleep(5)
