import requests
from src.config import config_instance


def create_user_agent(client_id: str) -> str:
    return f"Python:{client_id}:1.0 (by /u/mobius-crypt)"


async def authenticate_reddit() -> tuple[requests.Session, str]:
    """
        authenticate reddit and return Session and Token
    :return:
    """
    # Reddit API credentials
    client_id = config_instance().REDDIT_SETTINGS.client_id
    client_secret = config_instance().REDDIT_SETTINGS.client_secret
    username = config_instance().REDDIT_SETTINGS.username
    password = config_instance().REDDIT_SETTINGS.password

    # Authentication endpoint URL
    auth_url = 'https://www.reddit.com/api/v1/access_token'

    # Headers with user agent and Content-Type
    headers = {
        'User-Agent': create_user_agent(client_id=client_id),
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # Data for authentication request
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password
    }

    # Create a session and authenticate
    _session: requests.Session = requests.Session()
    _session.auth = (client_id, client_secret)
    response: requests.Response = _session.post(auth_url, headers=headers, data=data)
    print(response.content)
    if response.status_code == 200:
        _access_token: str = response.json()['access_token']
        print("Authentication successful!")
        return _session, _access_token
    else:
        print("Error authenticating. Status code:", response.status_code)
        return None, None

