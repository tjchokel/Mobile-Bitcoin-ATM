# Initial Setup Instructions #

## Install Some Stuff ##
- Follow the instructions [here](http://docs.python-guide.org/en/latest/starting/install/osx/) to install [Homebrew](http://brew.sh/) and then (re)install python.
- If for some reason the step above does not install pip and virtualenv, follow the instructions [here](https://pip.pypa.io/en/latest/installing.html#python-os-support) to get pip and then install virtualenv using pip install virtualenv.
- Install ngrok with `brew install ngrok` (thanks Homebrew!)
- Install the latest stable version of postgres 9. We recommend using Postgresapp for mac, available [here](http://postgresapp.com/).

## Configure Some Stuff ##
- Create an ssh key if you don't already have one with `$ ssh-keygen -t rsa`
- [Add your SSH key to your github account](https://github.com/settings/ssh) (you can copy it to the clipboard using `$ pbcopy < ~/.ssh/id_rsa.pub`)
- `cd` into your projects/workspaces directory and run `$ git clone https://github.com/coinsafe/bitcash.git`. Note that this will only work if MF has added you to [the coinsafe repository](https://github.com/coinsafe/bitcash)). The result of `$ git remote -v` should look like this:
```
origin	git@github.com:coinsafe/web.git (fetch)
origin	git@github.com:coinsafe/web.git (push)
```
- `cd bitcash/` to get to the project root direction, create a virtual environment (`$ virtualenv venv`) and then activate it (`$ source venv/bin/activate`)
- Install requirements: `$ pip install -r requirements.txt` (this will take a few mins)
- Create a `.env` file in the project root directory with the following (get actual creds securely from MF):
```
DEBUG=True
TEMPLATE_DEBUG=True
DJ_DEFAULT_URL=postgres://postgres:YOURLOCALPASSWORDHERE@localhost:5432/coinsafe_local
SECRET_KEY=GENERATE_THIS_USING_DJANGO_SECRET_KEY_GEN.py
SITE_DOMAIN=pick_this_yourself.ngrok.com
POSTMARK_API_KEY=GET_FROM_MF
PLIVO_AUTH_ID=GET_FROM_MF
PLIVO_AUTH_TOKEN=GET_FROM_MF
BCI_SECRET_KEY=GET_FROM_MF
CHAIN_COM_API_KEY=GET_FROM_MF
AWS_STORAGE_BUCKET_NAME=GET_FROM_MF
AWS_ACCESS_KEY_ID=GET_FROM_MF
AWS_SECRET_ACCESS_KEY=GET_FROM_MF
MAILGUN_API_KEY=GET_FROM_MF
```
(this is for your local machine, production is a little different as `settings.py` is smartly designed to default to production settings)

- Create a database on your local machine with whatever name you like. I recommend `coinsafe_local` so it's clear you're working on a local copy. You'll be using this above in `DJ_DEFAULT_URL`. I've assumed your user is `postgres`, but you could have a different user.
- Generate a salt (`SECRET_KEY`) using the script in [django_secret_key_gen.py](https://github.com/coinsafe/bitcash/blob/master/scripts/django_secret_key_gen.py). This uses `os.urandom` under the hood for a CSPRNG.

- Create DB tables from code (replace `foreman` with `heroku` for running on production, which should basically never happen again):

```bash
# Create original tables (this will create South tables)
$ foreman run ./manage.py syncdb

# Run the migration (south will takeover)
$ foreman run ./manage.py migrate
```
(More info on south generally [here](http://stackoverflow.com/questions/4840102/why-dont-my-south-migrations-work/4840262))

## Run the Site Locally ##

Run the webserver locally:
```
$ foreman run ./manage.py runserver
```

Now visit: http://127.0.0.1:8000/

To perform cash-out transactions, we need to also run `ngrok` in the terminal so that we can recieve webhooks locally:
```
$ ngrok -subdomain=pick_this_yourself 8000
```
(be sure that `pick_this_yourself` matches your selection in your `.env` file above)

Now visit http://pick_this_yourself.ngrok.com (you could even do this on your phone)

## Check Out the Admin Section ##


- Create a superuser admin (for yourself), by entering the following into `$ foreman run ./manage.py shell`:

```python
from users.models import AuthUser
KYCUser.objects.create_superuser(username='YOURCHOICE', email='YOURCHOICE', password='PASSWORDGOESHERE')
```

Now visit http://127.0.0.1:8000/admin


## Submit Your First Pull Request ##

First, pull the latest version of the code from github:
```
$ git pull origin master
```

Make a new branch:
```
$ git checkout -b my_branch
```

Make some trivial change and commit it:
```
$ git commit -am 'my changes'
```

Push it up to github:
```
$ git push origin my_branch
```

Submit your pull request (or at least be able to) here:
https://github.com/coinsafe/bitcash

Congrats, you're all setup!

# Post Setup Instructions #

## Build Awesome Features ##

You're on your own for that.

## User Impersonation ##

To impersonate a user, you must be logged in as the super admin. From there, append `?__impersonate=username_here` to the end of the url. 

To switch back to your admin user, add `?__unimpersonate=True` to the url.
