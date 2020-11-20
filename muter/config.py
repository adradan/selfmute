import os
import urllib


class Config:
    TOKEN = os.getenv('MUTER_TOKEN')
    user = urllib.parse.quote_plus(os.getenv('MONGO_USER'))
    pw = urllib.parse.quote_plus(os.getenv('MONGO_PW'))
    MONGO_URL = f'mongodb+srv://{user}:{pw}@automuter.7ypk1.mongodb.net/automuter.selfmuter?retryWrites=true&w=majority'
