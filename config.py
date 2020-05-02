import os
from flask_babel import lazy_gettext as _l

basedir = os.path.abspath(os.path.dirname(__file__)).replace('\\', '/')

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'leave-hope-to-enter'
    DATA_DIR   = basedir + '/covid/data'
    DATA_FILE  = DATA_DIR + '/covid-20200424.csv'
    D_FMT2     = '%d/%m/%Y'              # format date as dd/mm/yyyy
    LANGUAGES = ['en', 'it']
    SITE = {
        'ABSTRACT':  "luciano de falco alfano website: IT and not so IT articles", 
        'WTITLE':    "luciano de falco alfano's website", 
        'WSUBTITLE': _l('When the archer misses the center of the target, he turns round and seeks for the cause of his failure in himself (Confucius)'), 
        'WLICENSE':  _l('CC BY-SA 4.0 license'), 
        'WLICENSEREF': "https://creativecommons.org/licenses/by-sa/4.0/", 
    }
    VER = '0.3'
    LOG = {
        'FILE': basedir + '/covid/logs/covid.log',
        'BUFSIZE': 10240,
    }
