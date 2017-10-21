import smtplib
from email.mime.text import MIMEText

class BatchEmailerSMTP:

	def __init__(self, username, pw, template_file):
		self.username = username
		self.pw = pw
		self.file = template_file

	def generate_message(self, subject, message_text, to_addr):
		message = MIMEText(message_text)
		message['Subject'] = subject
		message['From'] = self.username
		message['To'] = to_addr
		return message

	def send_email(self, subject, message_text, to_addr):

		message = self.generate_message(subject, message_text, to_addr)

		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.ehlo()
		server.starttls() # starts encrypted connection
		server.ehlo()
		server.login(self.username, self.pw)
		server.sendmail(self.username, to_addr, message.as_string())
		server.close()

if __name__ == '__main__':

	username = '<your_email>@gmail.com'
	pw = '<your_password>'
	file_path = 'temp'
	myEmailer = BatchEmailerSMTP(username, pw, file_path)

	sbj_string = 'test'
	msg_string = 'hi'
	myEmailer.send_email(sbj_string, msg_string)
