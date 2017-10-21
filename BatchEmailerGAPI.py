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
		"""
		Helper function that parses the recipients.txt file to generate a hashset
		of recipients. 

		Returns:
			None
		"""
		if path:
			with open(path) as f:
				for line in f.readlines():
					self.recipients.add(line)

	def get_message(self, path):
		"""
		Helper function that parses the message_text.txt file to generate a string
		of the email body to be used when generating the email message.

		Returns:
			None
		"""
		if path:
			contents = []
			with open(path) as f:
				for line in f.readlines():
					contents.append(line)
			return ''.join(contents)

	def get_credentials(self):
	    """
	    Gets valid user credentials from storage.

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
		Authenticates credentials. Uses the get_credentials helper function
		to authenticate the email corresponding to the user name.

		Returns:
			discovery object to be used for sending emails
		"""
		credentials = self.get_credentials()
		http = credentials.authorize(httplib2.Http())
		return discovery.build('gmail', 'v1', http=http)

	def create_message(self, to_addr, subject, message_text):
		"""
		Creates a MIMEText object out of the given speicications. Encodes 
		the object then decodes to get the raw string of the encoded object
		for security reasons.
		
		Args:
			to_addr: recipient's email address
			subject: subject line in the email
			message_text: body of email

		Returns:
			map containing raw text of the MIMEText message
		"""
		message = MIMEText(message_text)
		message['to'] = to_addr
		message['from'] = self.username
		message['subject'] = subject
		raw = base64.urlsafe_b64encode(message.as_bytes())
		return {'raw':raw.decode()}

	def send_message(self, to_addr=None):
		"""
		Main method that sends the email. Creates a MIMEText object using a helper
		function then uses the discovery object created upon authenticatation to 
		send the email. Prints the response id given back by the server for each 
		email sent. After all recipients have been processed, accounts associated
		with failed attemps are recorded back into the recipients.txt file for 
		future attempts.

		Returns:
			None
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
				self.recipients.add(recipient) # re-add if email send unsuccessful

		self.update_recipient_list() # update recipient list with a list of failed accounts
		
	def update_recipient_list(self):
		"""
		Helper function that writes the list of email accounts associated with 
		failed attempts to the recipients.txt file.

		Returns:
			None
		"""
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