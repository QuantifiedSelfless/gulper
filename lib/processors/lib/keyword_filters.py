import re


def is_great_quote(text, keywords):
    text = text.lower()
    words = set(text.split())
    if len(words) < 3:
        return False
    if any(len(w) > 10 or 'http' in w
            for w in words):
        return False
    if "@" in text:
        return False
    for keyword in keywords:
        if keyword in words:
            return True
    return False


def process_post(text, keywords):
    # If there is enough perm quotes, quit.
    sentences = re.split(r' *[\.\?!][\'"\)\]]* *', text)
    for sentence in map(str.strip, sentences):
        if is_great_quote(sentence, keywords):
            yield sentence


def process_facebook(user_data, keywords):
    if user_data.data.get('fbtext', None):
        fbtext = user_data.data['fbtext']
        fbposts = fbtext.get('text') or []
        for post in fbposts:
            yield from process_post(post['text'], keywords)


def process_twitter(user_data, keywords):
    if user_data.data.get('twitter', None):
        twitter = user_data.data['twitter']
        tweets = twitter.get('tweets') or []
        for post in tweets:
            yield from process_post(post, keywords)


def process_reddit(user_data, keywords):
    if user_data.data.get('reddit', None):
        reddit = user_data.data['reddit']
        posts = reddit.get('text') or []
        for post in posts:
            yield from process_post(post['body'], keywords)


def process_gmail(user_data, keywords):
    if user_data.data.get('gmail'):
        gmail = user_data.data['gmail']
        snippets = gmail.get('snippets') or []
        for post in snippets:
            yield from process_post(post, keywords)
