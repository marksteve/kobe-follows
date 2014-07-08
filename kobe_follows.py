import json
import logging
import math
import os
import time

import requests
import schedule
from requests_oauthlib import OAuth1Session

logger = logging.getLogger("schedule")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

twitter = OAuth1Session(
  os.environ["TWITTER_API_KEY"],
  client_secret=os.environ["TWITTER_API_SECRET"],
  resource_owner_key=os.environ["TWITTER_ACCESS_TOKEN"],
  resource_owner_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"])

pushbullet = requests.Session()
pushbullet.auth = (os.environ["PUSHBULLET_ACCESS_TOKEN"], '')


screen_names = dict()
follows = set()


def get_data(res):
  data = res.json()
  if "errors" in data:
    raise Exception("\n".join([
      "{code}: {message}".format(**error) for error in data["errors"]
    ]))
  return data


def get_screen_names(user_ids):
  return [("@" + screen_names[user_id]) for user_id in user_ids]


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
    curr_follows.add(user["id_str"])
    screen_names[user["id_str"]] = user["screen_name"]
  logger.info("Current follows: %r", get_screen_names(curr_follows))

  new_follows = curr_follows - follows
  logger.info("New follows: %r", get_screen_names(new_follows))

  if len(new_follows) == len(curr_follows):
    logger.info("Initial run!")
  elif len(new_follows) > 0:
    pushbullet.post(
      "https://api.pushbullet.com/v2/pushes",
      data=json.dumps(dict(
        type="list",
        title="Kobe's new follows",
        items=get_screen_names(new_follows),
      )),
      headers={
        "Content-Type": "application/json",
      })
    twitter.post(
      "https://api.twitter.com/1.1/statuses/update.json",
      data=dict(
        status="@kobebryant followed:\n" + "\n".join(
          get_screen_names(new_follows)
        ),
      ))

  follows.update(new_follows)


def fetch_followed_users(user_ids):
  followed_users = []
  for i in range(int(math.ceil(len(user_ids) / 100.))):
    res = twitter.post(
      "https://api.twitter.com/1.1/users/lookup.json",
      data=dict(
        user_id=",".join(user_ids[i * 100:(i + 1) * 100]),
      ))
    followed_users.extend(get_data(res))
  return followed_users


def main():
  schedule.every().minute.do(fetch_kobe_follows)
  schedule.run_all()
  while True:
    schedule.run_pending()
    time.sleep(1)


if __name__ == "__main__":
  main()
