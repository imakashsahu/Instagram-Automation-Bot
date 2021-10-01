import configparser
import logging
import requests
import json
import re
import datetime
import base64

from requests.api import post
import langdetect

class InstagramBot():
	def __init__(self):
		self.config = configparser.ConfigParser()
		self.config.read('etc/instagram_config.ini', encoding='utf-8')
		self.instagram_id = self.config['creds']['instagram_account_id']
		self.access_token = self.config['creds']['long_lived_access_token']
		self.hashtags = self.config['monitor']['hashtags']
		self.imgbb_key = self.config['imgbb']['key']

		logging.basicConfig(filename='var/instagram.log',
							format='%(asctime)s - [%(levelname)s] - %(message)s',
							encoding='utf-8')
		self.logger=logging.getLogger()
		self.logger.setLevel(logging.DEBUG)

		self.media_dir = "tmp/"
	
	# Returns list of hashtags from config to monitor
	def get_hashtags_list(self):
		hashtag = re.split(', ', self.hashtags)
		self.logger.info(f"Monitoring '{hashtag[datetime.datetime.now().hour]}' hashtag in this run")
		# Return hashtag on index corresponding to hour of the day
		return hashtag[datetime.datetime.now().hour]
	
	def get_hashtag_id(self, hashtag):
		try:
			self.logger.info(f"Fetching hashtag id for #{hashtag}")
			graph_api_call = requests.get(f"https://graph.facebook.com/v12.0/ig_hashtag_search?"
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
			graph_api_call = requests.get(f"https://graph.facebook.com/v12.0/{hashtag_id}/"
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
				if hashtag_post[i]['media_type'] in ('IMAGE'):
					post_lang = langdetect.detect(hashtag_post[i]['caption'])
					if post_lang == 'en':
						self.logger.info(f"Selected '{hashtag_post[i]['permalink']}' to be posted")
						
						return hashtag_post[i]
		except Exception as error:
			self.logger.error(f"[LANGUAGE DETECT] : {error}")

	def upload_media_to_imgbb(self, media_file):
		try:
			with open(media_file, "rb") as file:
				url = "https://api.imgbb.com/1/upload"
				payload = {
					"key": self.imgbb_key,
					"image": base64.b64encode(file.read()),
				}
				media_img_url = requests.post(url, payload)

				return media_img_url.json()['data']['url']
		except Exception as error:
			self.logger.error(f"[MEDIA UPLOAD] : {error}")

	def download_media(self, media_url, media_type):
		try:
			media = requests.get(media_url)
			file_name = (f"{media_type.lower()}.{'jpg' if media_type=='IMAGE' else 'mp4'}")
			file_location = self.media_dir + file_name
			
			with open(file_location, 'wb') as media_file:
				media_file.write(media.content)
			
			media_imgbb_url = self.upload_media_to_imgbb(file_location)
			return media_imgbb_url
		except Exception as error:
			self.logger.error(f"[MEDIA DOWNLOAD] : {error}")

	def create_ig_media_container(self, media_file, caption, permalink):
		try:
			post_caption = f"""#love #instagood #like #follow #instagram #photooftheday #photography 
							#beautiful #fashion #bhfyp #picoftheday #happy #art #life #smile #likeforlikes 
							#cute #instadaily #me #followme #style #nature #likes #instalike #followforfollowback 
							#beauty #photo #myself #bhfyp"""
			graph_api_call = requests.post(f"https://graph.facebook.com/v12.0/{self.instagram_id}/"
								f"media?image_url={media_file}"
								f"&access_token={self.access_token}"
								f"&caption='{post_caption}'"
							)
			media_container = graph_api_call.json()
			self.logger.info(f"Created container {media_container} for {permalink}")
			return media_container['id']
		except Exception as error:
			self.logger.error(f"[MEDIA CONTAINER] : {error}")
			return None

	def publish_media(self, media_container_id, permalink):
		try:
			graph_api_call = requests.post(f"https://graph.facebook.com/v12.0/{self.instagram_id}/"
								f"media_publish?creation_id={media_container_id}"
								f"&access_token={self.access_token}"
							)
			publish_media = graph_api_call.json()
			self.logger.info(f"Published {media_container_id} for {permalink}")
			return True
		except Exception as error:
			self.logger.error(f"[PUBLISH MEDIA] : {error}")
			return None

	def start(self):
		try:
			self.logger.info(f"Don't do anything I would do, "
						f"and definitely don't do anything I wouldn't do…")
			# Fetch post for hashtag on index corresponding to hour of the day
			hashtag = self.get_hashtags_list()
			hashtag_id = self.get_hashtag_id(hashtag)
			if hashtag_id:
				hashtag_post = self.get_hashtag_media(hashtag_id)
					
				# Check if Post language is English
				post = self.detect_post_lang(hashtag_post)
				if post:
					media_file = self.download_media(post['media_url'], post['media_type'])
					self.logger.info(f"Trying to publish : {media_file} for {post['permalink']}")
					media_container_id = self.create_ig_media_container(media_file, post['caption'], post['permalink'])
					if media_container_id:
						self.publish_media(media_container_id, post['permalink'])
						self.logger.info(f"Stopping bot after successfully publishing")
		except Exception as error:
			self.logger.error(f"[START METHOD] : {error}")

if __name__ == "__main__":
	InstagramBot().start()