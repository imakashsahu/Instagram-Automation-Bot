import configparser
import logging
import requests
import json
import re
import datetime
import uuid

from requests.api import post
import langdetect

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
		self.logger.info(f"Monitoring '{self.hashtags}' list of hashtags in this run")
		
		return hashtag
	
	def get_hashtag_id(self, hashtag):
		try:
			self.logger.info(f"Fetching hashtag id for #{hashtag}")
			graph_api_call = requests.get(f"https://graph.facebook.com/ig_hashtag_search?"
								f"user_id={self.instagram_id}&q={hashtag}"
								f"&access_token={self.access_token}"
							)
			hashtag_id = graph_api_call.json()['data'][0]['id']
			
			return hashtag_id
		except Exception as error:
			self.logger.error(f"[API HASHTAG ID] : {error}")
			return None


	def get_hashtag_media(self, hashtag_id):
		try:
			# Specify if to fetch top_media  or recent_media
			media_type = 'recent_media'
			media_fields = """id,permalink,comments_count,like_count,media_type,media_url,
					timestamp,caption,children{id,permalink,media_type,media_url,timestamp}"""
			
			self.logger.info(f"Fetching posts for hashtag id '{hashtag_id}'")
			graph_api_call = requests.get(f"https://graph.facebook.com/{hashtag_id}/"
								f"{media_type}?fields={media_fields}"
								f"&user_id={self.instagram_id}"
								f"&access_token={self.access_token}"
							)
			hashtag_posts = graph_api_call.json()['data']
			
			return hashtag_posts
		except Exception as error:
			self.logger.error(f"[API MEDIA FETCH] : {error}")

	def detect_post_lang(self, hashtag_post):
		try:
			for i in range(0, 25):
				if hashtag_post[i]['media_type'] in ('IMAGE', 'VIDEO'):
					post_lang = langdetect.detect(hashtag_post[i]['caption'])
					if post_lang == 'en':
						self.logger.info(f"Selected '{hashtag_post[i]['permalink']}' to be posted")
						
						return hashtag_post[i]
		except Exception as error:
			self.logger.error(f"[LANGUAGE DETECT] : {error}")

	def download_media(self, media_url, media_type):
		try:
			media = requests.get(media_url)
			file_name = (f"{media_type.lower()}.{'jpg' if media_type=='IMAGE' else 'mp4'}")
			file_location = self.media_dir + file_name
			
			with open(file_location, 'wb') as media_file:
				media_file.write(media.content)
			
			return file_location
		except Exception as error:
			self.logger.error(f"[LANGUAGE DETECT] : {error}")	

	def start(self):
		try:
			self.logger.info(f"Don't do anything I would do, "
						f"and definitely don't do anything I wouldn't do…")
			for hashtag in self.get_hashtags_list():
				hashtag_id = self.get_hashtag_id(hashtag)
				if hashtag_id:
					hashtag_post = self.get_hashtag_media(hashtag_id)
					
					# Check if Post language is English
					post = self.detect_post_lang(hashtag_post)
					if post:
						tmp_id = uuid.uuid4()
						media_file = self.download_media(post['media_url'], post['media_type'])
						print(media_file)

		except Exception as error:
			self.logger.error(f"[START METHOD] : {error}")

if __name__ == "__main__":
	InstagramBot().start()