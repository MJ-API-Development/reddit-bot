import requests


def make_post(access_token, subreddit, title, content):
    # Post endpoint URL
    post_url = f'https://reddit.com/r/{subreddit}/submit'

    # Headers with user agent and authorization
    headers = {
        'User-Agent': 'YOUR_USER_AGENT',
        'Authorization': f'Bearer {access_token}'
    }

    # Data for post request
    data = {
        'kind': 'self',
        'title': title,
        'text': content
    }

    # Send the post request
    response = requests.post(post_url, headers=headers, data=data)
    print(response.content)
    if response.status_code == 200:
        print("Post successfully submitted!")
    else:
        print("Error submitting post. Status code:", response.status_code)

    return response.json()