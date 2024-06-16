import requests
from bs4 import BeautifulSoup
from twocaptcha import TwoCaptcha


# A wrapper of the requests module for use with BLS.
# class BLSRequest(requests):


# A BLS website exception.
class BLSException(Exception):

	# Creates a new instance of the BLS website exception class.
	def __init__(self, message):
		# Call the base exception class.
		super(BLSException, self).__init__(message)


# A BLS website verify response object.
class BLSVerifyResponse:

	# Creates a new BLS verify response object.
	def __init__(self, response):
		# Stores the response.
		self.response = response

	# Raises an exception if there is an error in the verify response.
	def raise_for_error(self):
		# Gets the response as text
		res_text = self.response.text.strip()
		# If there are invalid headers.
		if 'Data not found.' in res_text:
			# Raises an exception with the error message.
			raise BLSException('Invalid request headers.')
		# If there is an invalid token.
		elif res_text == 'Access Not allowed':
			# Raises an exception with the error message.
			raise BLSException('Invalid token.')
		# If bookings are full.
		elif res_text == 'full':
			# Raises an exception with the error message.
			raise BLSException('Appointment dates are not available.')
		# If the number has already been used.
		elif res_text == 'fail':
			# Raises an exception with the error message.
			raise BLSException('You have already booked appointment with this phone. Please try with another number.')
		# If the old verification should be used.
		elif res_text == 'same':
			# Raises an exception with the error message.
			raise BLSException('Please used last sent verification code.')
		# If there was an error with the phone number.
		elif res_text == 'error':
			# Raises an exception with the error message.
			raise BLSException('Please check your phone number and country code for phone.')

	# Raises an exception if there is a status error.
	def raise_for_status(self):
		# Checks the status.
		self.response.raise_for_status()


# A BLS website response object.
class BLSResponse(BLSVerifyResponse):

	# Creates a new BLS response object.
	def __init__(self, response):
		# Stores the response.
		self.response = response
		# Parses the response.
		self.soup = BeautifulSoup(response.content, 'html.parser')

	# Extracts and returns the csrf name from the response.
	def get_csrf_name(self):
		# Finds the booking form.
		booking_form = self.soup.find('form', {'name': 'Booking'})
		# Validates the existence of the booking form.
		if booking_form:
			# Finds the csrf name.
			csrf_name = booking_form.find('input', {'name': 'CSRFName'})
			# Validates the existence of the csrf name.
			if csrf_name:
				# Returns the csrf name.
				return csrf_name['value']

	# Extracts and returns the csrf token from the response.
	def get_csrf_token(self):
		# Finds the booking form.
		booking_form = self.soup.find('form', {'name': 'Booking'})
		# Validates the existence of the booking form.
		if booking_form:
			# Finds the csrf token.
			csrf_token = booking_form.find('input', {'name': 'CSRFToken'})
			# Validates the existence of the csrf token.
			if csrf_token:
				# Returns the csrf token.
				return csrf_token['value']

	# Extracts and returns the verify csrf token from the response.
	def get_verify_csrf_token(self):
		# Extracts and returns the csrf token.
		return self.response.text.split('&token=')[1].split('",')[0]

	# Extracts and returns the captcha sitekey.
	def get_captcha_sitekey(self):
		# Finds the captcha object.
		captcha = self.soup.find('div', {'class': 'g-recaptcha'})
		# Validates the existence of the captcha.
		if captcha:
			# Returns the sitekey.
			return captcha['data-sitekey']

	# Raises an exception if there is an error in the response.
	def raise_for_error(self):
		# Finds the error container.
		container = self.soup.find('div', {'class': 'col-sm-6 container paddingInBoxExtra roundCornerExtra'})
		# Validates that the container exists.
		if container:
			# Extracts the error message.
			error_message = container.text
			# Raises an exception with the error message.
			raise BLSException(error_message)


# A Python wrapper for the BLS website.
class BLS:

	# Stores the wrapper user agent.
	USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:62.0)'

	# Creates a new BLS instance.
	def __init__(self):
		# Creates a new request session.
		self.session = requests.session()
		# Sets the session headers.
		self.session.headers.update({'User-Agent': BLS.USER_AGENT})
		# Gets the appointment response and session cookies.
		self.appt_res = BLSResponse(self.session.get('https://algeria.blsspainvisa.com/english/book_appointment.php'))
		# Raises an exception if there is a status error.
		self.appt_res.raise_for_status()
		# Raises an exception if there is an error.
		self.appt_res.raise_for_error()

	# Sends a validation code to the given phone number.
	def send_verification(self, email, phone_code, phone_no, center_id):
		# Constructs the verification headers.
		ver_head = {'Referer': 'https://algeria.blsspainvisa.com/english/book_appointment.php', 'X-Requested-With': 'XMLHttpRequest'}
		# Constructs the verification data.
		ver_data = {'gofor': 'send_mail', 'email': email, 'phone_code': phone_code, 'phone_no': phone_no, 'center_id': center_id, 'visa': None, 'token': self.appt_res.get_verify_csrf_token()}
		# Posts the verification data to BLS.
		ver_res = BLSVerifyResponse(self.session.post('https://algeria.blsspainvisa.com/english/ajax.php', headers=ver_head, data=ver_data))
		# Raises an exception if there is a status error.
		ver_res.raise_for_status()
		# Raises an exception if there is an error.
		ver_res.raise_for_error()

	# Books an appointment with BLS.
	def book_appointment(self, phone_code, phone, email, verification_code, recaptcha_response):
		# Constructs the appointment headers.
		appt_head = {'Referer': 'https://algeria.blsspainvisa.com/english/book_appointment.php'}
		# Constructs the appointment data.
		appt_data = {'CSRFName': self.appt_res.get_csrf_name(), 'CSRFToken': self.appt_res.get_csrf_token(), 'app_type': 'Individual', 'member': 2, 'juridiction': '14#Adrar#9', 'visa_no': None, 'visa_valid_from': None, 'visa_valid_to': None, 'rejected': 'No', 'refusal_date': None, 'phone_code': phone_code, 'phone': phone, 'email': email, 'otp': verification_code, 'countryID': None, 'g-recaptcha-response': recaptcha_response, 'save': 'Continue'}
		# Posts the appointment data to BLS.
		appt_res = BLSResponse(self.session.post('https://algeria.blsspainvisa.com/english/book_appointment.php', headers=appt_head, data=appt_data))
		# Raises an exception if there is a status error.
		appt_res.raise_for_status()
		# Raises an exception if there is an error.
		appt_res.raise_for_error()


if __name__ == '__main__':
	# Creates a new instance of two captcha.
	tc = TwoCaptcha('')
	# Creates a new BLS instance.
	bls = BLS()
	# Sends a verfication code to the phone number.
	# bls.send_verification('hello@gmail.com', '213', None, 9)
	# Solves the captcha.
	tc.solve_captcha(site_key='', page_url='')
	# Books an appointment.
	bls.book_appointment('213', None, 'hello@gmail.com', None, None)