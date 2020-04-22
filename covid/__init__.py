import os
import pandas as pd

from datetime import datetime, date

import click

from flask import Flask, request
from flask.cli import AppGroup
from flask_babel import Babel
from config import Config


class Nations(object):

    def __init__(self):
        #self.__n__ = {id: name for id, name in (('IT', 'Italy',), ('ES', 'Spain',), ('GE', 'Germany',), ('FR','France',), ('UK', 'United Kingdom',),)}
        self.__n__ = dict()

    def __setitem__(self, key, item):
        self.__n__[key] = item

    def __getitem__(self, key):
        return self.__n__[key]

    def __repr__(self):
        return repr(self.__n__)

    def __len__(self):
        return len(self.__n__)

    def __delitem__(self, key):
        del self.__n__[key]

    def has_key(self, k):
        return k in self.__n__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__n__.keys()

    def values(self):
        return self.__n__.values()

    def items(self):
        return self.__n__.items()

    def pop(self, *args):
        return self.__n__.pop(*args)

    def __cmp__(self, dict_):
        return self.__cmp__(self.__n__, n_)

    def __contains__(self, item):
        return item in self.__n__

    def __iter__(self):
        return iter(self.__n__)

    def __unicode__(self):
        return unicode(repr(self.__n__))

    def get_for_select(self):
        l = [(id, name) for id, name in self.__n__.items()]
        l.sort(key = lambda x: x[1])
        return l
        
    def get_for_list(self):
        l = [name for id, name in self.__n__.items()]
        l.sort()
        return l


def make_nations():
    '''create Nations from dataframe
    
    params: df   pandas dataframe - as from ECDC
    
    returns: n   istance of Nations
    '''
    df = pd.read_csv(app.config['DATA_FILE'])
    n = Nations()
    cdf = df[['countriesAndTerritories', 'geoId']].drop_duplicates()
    for row, c in cdf.iterrows():           # row, country:(name, id,)
        n[c[1]] = c[0]
    return n


app = Flask(__name__)            # warn.here sequence of actions count
translate_cli = AppGroup('translate')
app.config.from_object(Config)
#app.secret_key = os.urandom(16)      # needed by session

@translate_cli.command('init')
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel init -i messages.pot -d covid/translations -l ' + lang):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')
    
    
@translate_cli.command('update')
def update():
    """Update all languages."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel update -i messages.pot -d covid/translations'):
        raise RuntimeError('update command failed')
    os.remove('messages.pot')

@translate_cli.command('compile')
def compile():
    """Compile all languages."""
    if os.system('pybabel compile -d covid/translations'):
        raise RuntimeError('compile command failed')

app.cli.add_command(translate_cli)


nations = make_nations()
babel = Babel(app)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

from covid import routes

