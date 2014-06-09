from bitcash.settings import PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN

import plivo
import re


def send_sms(dst, text, src="16502647255"):
    rest_api = plivo.RestAPI(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN)
    # strip other chars (space + - etc)
    dst_cleaned = re.sub('[^0-9]*', '', dst)
    #TODO: check HTTP status code and handle case where this fails
    return rest_api.send_message({'src': src, 'dst': dst_cleaned, 'text': text})
