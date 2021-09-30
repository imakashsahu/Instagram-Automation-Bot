import configparser
import logging
import requests
import json
import re
import datetime

class InstagramBot():
	def __init__(self):
		self.config = configparser.ConfigParser()
		self.config.read('etc/instagram_config.ini', encoding='utf-8')
		self.instagram_id = self.config['creds']['instagram_account_id']
		self.access_token = self.config['creds']['long_lived_access_token']
		self.hashtags = self.config['monitor']['hashtags']

		logging.basicConfig(filename='var/instagram.log',
							format='%(asctime)s - [%(levelname)s] - %(message)s',
							encoding='utf-8')
		self.logger=logging.getLogger()
		self.logger.setLevel(logging.INFO)

		self.media_dir = "tmp/"
	
	# Returns list of hashtags from config to monitor
	def get_hashtags_list(self):
		hashtag = re.split(', ', self.hashtags)
		self.logger.info(f"Monitoring [{self.hashtags}] list of hashtags in this run")
		return hashtag
	
	def get_hashtag_id(self, hashtag):
		graph_api_call = requests.get(f"https://graph.facebook.com/ig_hashtag_search?"
							f"user_id={self.instagram_id}&q={hashtag}"
							f"&access_token={self.access_token}")
		hashtag_id = graph_api_call.json()['data'][0]['id']
		return hashtag_id

	def get_hashtag_media(self, hashtag_id):
		media_fields = "id,permalink,comments_count,like_count,media_type,media_url,timestamp,caption,children{id,permalink,media_type,media_url,timestamp}"
		graph_api_call = requests.get(f"https://graph.facebook.com/{hashtag_id}/"
							f"top_media?fields={media_fields}"
							f"&user_id={self.instagram_id}"
							f"&access_token={self.access_token}")
		hashtag_posts = graph_api_call.json()['data']
		return hashtag_posts

	def start(self):
		# data = requests.get(f"https://graph.facebook.com/ig_hashtag_search?user_id={self.instagram_id}&q=python&access_token={self.access_token}")
		# print(data.json())
		self.logger.info(f"Started a new run at : {datetime.datetime.now()}")
		for hashtag in self.get_hashtags_list():
			hashtag_id = self.get_hashtag_id(hashtag)
			hashtag_post = self.get_hashtag_media(hashtag_id)
			for i in range(0, 25):
				print(hashtag_post[i])

if __name__ == "__main__":
	InstagramBot().start()