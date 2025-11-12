import requests
import time

def api_request(method, url, token, **kwargs):
    headers = {"Authorization": token}
    while True:
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers
        r = requests.request(method, url, **kwargs)
        if r.status_code == 429:
            retry = r.json().get("retry_after", 5)
            time.sleep(retry)
            continue
        if r.status_code in (200, 201, 204):
            try:
                return r.json() if r.content else None
            except:
                return None
        else:
            return None

def get_user_info(token):
    return api_request("GET", "https://discord.com/api/v9/users/@me", token)

def get_dm_channels(token):
    return api_request("GET", "https://discord.com/api/v9/users/@me/channels", token)

def fetch_messages(token, channel_id, limit=100, before=None):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={limit}"
    if before:
        url += f"&before={before}"
    return api_request("GET", url, token)

def delete_message(token, channel_id, message_id):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"
    return api_request("DELETE", url, token)
