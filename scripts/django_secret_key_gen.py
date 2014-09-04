# This is a one-time process to set the initial salt (SECRET_KEY)

import random

# Borrowed from: https://gist.github.com/ndarville/3452907
# Effectively what django does under the hood:
# https://github.com/django/django/blob/9893fa12b735f3f47b35d4063d86dddf3145cb25/django/core/management/commands/startproject.py#L28

print 'Set the following value to SECRET_KEY on the webserver:'
print ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
