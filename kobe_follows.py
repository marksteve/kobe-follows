import json
import logging
import time

import config
import requests
import schedule
from requests_oauthlib import OAuth1Session

logger = logging.getLogger("schedule")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

twitter = OAuth1Session(
  config.TWITTER_API_KEY,
  client_secret=config.TWITTER_API_SECRET,
  resource_owner_key=config.TWITTER_ACCESS_TOKEN,
  resource_owner_secret=config.TWITTER_ACCESS_TOKEN_SECRET)

pushbullet = requests.Session()
pushbullet.auth = (config.PUSHBULLET_ACCESS_TOKEN, '')


follows = set()


def get_data(res):
  data = res.json()
  if "errors" in data:
    raise Exception("\n".join([
      "{code}: {message}".format(**error) for error in data["errors"]
    ]))
  return data


def fetch_kobe_follows():
  res = twitter.get(
    "https://api.twitter.com/1.1/friends/ids.json",
    params=dict(
      count=5000,
      screen_name="kobebryant",
      stringify_ids=True,
    ))
  data = get_data(res)

  curr_follows = set()
  for user in fetch_followed_users(data["ids"]):
    curr_follows.add(user["screen_name"])
  logger.info("Current follows: %r", curr_follows)

  new_follows = curr_follows - follows
  logger.info("New follows: %r", new_follows)

  if len(new_follows) == len(curr_follows):
    logger.info("Initial run!")
  else:
    pushbullet.post(
      "https://api.pushbullet.com/v2/pushes",
      data=json.dumps(dict(
        type="list",
        title="Kobe's new follows",
        items=list(new_follows),
      )),
      headers={
        "Content-Type": "application/json",
      })

  follows.update(new_follows)


def fetch_followed_users(user_ids):
  res = twitter.post(
    "https://api.twitter.com/1.1/users/lookup.json",
    data=dict(
      user_id=",".join(user_ids),
    ))
  data = get_data(res)
  return data


def main():
  schedule.every().minute.do(fetch_kobe_follows)
  schedule.run_all()
  while True:
    schedule.run_pending()
    time.sleep(1)


if __name__ == "__main__":
  main()
