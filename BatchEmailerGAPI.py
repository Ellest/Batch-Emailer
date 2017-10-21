from __future__ import print_function
import httplib2
import os
import base64
import urllib

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient import errors
from email.mime.text import MIMEText
from collections import deque

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python.json
SCOPES = 'https://mail.google.com' # all operations
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Batch Mailer Gmail API'

class BatchEmailerGAPI:

	def __init__(self, username, pw, subject, file_path=None, msg_path=None):

		self.username = username
		self.pw = pw
		self.subject = SUBJECT
		self.recipients = set() # using a hashtable to keep track of recipients
		self.recipients_path = file_path
		self.message_text = self.get_message(msg_path)

		self.load_recipients(file_path)

		self.service = self.authorize()

	def load_recipients(self, path):
		if path:
			with open(path) as f:
				for line in f.readlines():
					self.recipients.add(line)

	def get_message(self, path):
		if path:
			contents = []
			with open(path) as f:
				for line in f.readlines():
					contents.append(line)
			return ''.join(contents)

	def get_credentials(self):
	    """Gets valid user credentials from storage.

	    If nothing has been stored, or if the stored credentials are invalid,
	    the OAuth2 flow is completed to obtain the new credentials.

	    Returns:
	        Credentials, the obtained credential.
	    """
	    home_dir = os.path.expanduser('~')
	    credential_dir = os.path.join(home_dir, '.credentials')
	    if not os.path.exists(credential_dir):
	        os.makedirs(credential_dir)
	    credential_path = os.path.join(credential_dir,
	                                   'gmail-python.json')

	    store = Storage(credential_path)
	    credentials = store.get()
	    if not credentials or credentials.invalid:
	        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
	        flow.user_agent = APPLICATION_NAME
	        if flags:
	            credentials = tools.run_flow(flow, store, flags)
	        else: # Needed only for compatibility with Python 2.6
	            credentials = tools.run(flow, store)
	        print('Storing credentials to ' + credential_path)
	    return credentials

	def authorize(self):
		"""
		docs
		"""
		credentials = self.get_credentials()
		http = credentials.authorize(httplib2.Http())
		return discovery.build('gmail', 'v1', http=http)

	def create_message(self, to_addr, subject, message_text):
		"""
		docs
		"""
		message = MIMEText(message_text)
		message['to'] = to_addr
		message['from'] = self.username
		message['subject'] = subject
		raw = base64.urlsafe_b64encode(message.as_bytes())
		return {'raw':raw.decode()}

	def send_message(self, to_addr=None):
		"""
		docs
		"""
		if not to_addr: # set default recipient to self
			to_addr = self.username

		for _ in range(len(self.recipients)):
			recipient = self.recipients.pop()
			try:
				message = self.create_message(to_addr, self.subject, self.message_text)
				response = (self.service.users()
								  .messages()
								  .send(userId=self.username, body=message)
								  .execute())
				print('Message ID: {0}'.format(response['id']))
			except errors.HttpError as error:
				print('An Error Occured: {0}. Could not send email to {1}'.format(error, recipient))
				self.recipients.add(recipient) # remove if successful

		self.update_recipient_list()
		
	def update_recipient_list(self):
		with open(self.recipients_path, 'w') as f:
			for recipient in self.recipients:
				print(recipient)
				f.write(recipient)

if __name__ == '__main__':

	# setting up params
	USERNAME = '<your_email>@gmail.com'
	PW = '<your_password>'
	FILE_PATH = 'recipients.txt'
	MSGTXT_PATH = 'message.txt'
	SUBJECT = 'Join Us!'

	myEmailer = BatchEmailerGAPI(USERNAME, PW, SUBJECT, FILE_PATH, MSGTXT_PATH)

	myEmailer.send_message()