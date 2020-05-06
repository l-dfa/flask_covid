# filename routes.py
#   views of flask_covid project / covid application

# import std modules
from io import StringIO
#from pathlib import Path
from datetime import datetime, date, timedelta
from math import ceil

# import 3th parties modules
import bs4    as bs
import pandas as pd
import matplotlib as mpl
import numpy  as np

from flask      import Flask, flash, redirect, render_template, session, url_for, request
from flask import g
from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask_babel import get_locale

from markupsafe import escape
from matplotlib.figure import Figure

# import application modules
from covid       import app, nations
from covid.forms import SelectForm

# here we go
THRESHOLD = 200
THRESHOLD_RATIO = 0.05
COLORS=['tab:blue',
        'tab:orange',
        'tab:green',
        'tab:red',
        'tab:purple',
        'tab:brown',
        'tab:pink',
        'tab:gray',
        'tab:olive',
        'tab:cyan']
        
FIELDS_CHOICES = [('1', 'cases'), ('2', 'deaths'),('3','d²cases/dt²')]
FIELDS = {
    'cases':  {'id': '1',
               'explanation': _l('are the cumulative  cases positive to the infection'),
               'short': _('cumulative positive cases'),
              },
    'deaths': {'id': '2', 
               'explanation': _l('are the cumulative number of persons deceased due to the infection'),
               'short': _('cumulative number of deaths'),
              },
    'd²cases_dt²': {'id': '3', 
                    'explanation': _l('is the second derivative of cumulative positive cases; this indicates if the cases curve has upward or downward concavity'),
                    'short': _l("concavity's orientation of cumulative positive cases"),
                   },
}


# European Union: 27 countries
EU = (
    "Austria",
    "Belgium",  
    "Bulgaria",  
    "Croatia",  
    "Cyprus",  
    "Czechia",  
    "Denmark",  
    "Estonia",  
    "Finland",  
    "France",  
    "Germany",  
    "Greece", 
    "Hungary", 
    "Ireland", 
    "Italy", 
    "Latvia", 
    "Lithuania", 
    "Luxembourg", 
    "Malta", 
    "Netherlands", 
    "Poland", 
    "Portugal", 
    "Romania", 
    "Slovakia", 
    "Slovenia", 
    "Spain", 
    "Sweden", 
)


@app.before_request
def before_request():
    app.logger.debug('before_request()')
    g.locale = str(get_locale())


@app.route('/')
@app.route('/index')
def index():
    '''section's home'''
    app.logger.debug('index()')
    df = open_data(app.config['DATA_FILE'], pd.read_csv, world_shape)
    first, last = (df['dateRep'].min(), df['dateRep'].max(),)
    how_many = df['countriesAndTerritories'].drop_duplicates().count()
    return render_template('index.html', 
                           title=_("Covid: time trend analysis"), 
                           #NATIONS=nations.get_for_list(), 
                           FIRST=first,
                           LAST=last,
                           HOW_MANY=how_many
                          )


@app.route('/select', methods=['GET', 'POST'])
def select():
    '''select what country's trend to show'''
    #nations = make_nations(DATA_FILE)
    
    app.logger.debug('select()')
    form = SelectForm()
    #form.fields.choices = FIELDS_CHOICES.copy()
    form.fields.choices = list(zip([FIELDS[key]['id'] for key in FIELDS.keys()], FIELDS.keys()))
    # to set a default, this does not work; we need to use the "default" parameter in the class, or set data (see below)
    #form.fields.default = ['1',]
    form.contest.choices = [('nations','nations',), ('continents', 'continents',),]
    form.continents.choices = [ (c, c, ) for c in nations.keys()]
    form.countries.choices = nations.get_for_select()
    
    if form.validate_on_submit():

        # check contest: nations or continents
        contest = form.contest.data[:]
        if contest == 'nations':
            ids = '-'.join(form.countries.data)             # here build string with nations ids: e.g. it-fr-nl
        elif contest == 'continents':
            ids = '-'.join(form.continents.data)             # here build string with continents ids: e.g. Asia-Europe
        else:
            raise ValueError(_('%(function)s: %(contest)s is not a valid contest', function='select', contest=contest))
            
        # chaining names of fields to plot
        #columns = [name for code, name in FIELDS_CHOICES if code in form.fields.data ]
        columns = [name for name in FIELDS.keys() if FIELDS[name]['id'] in form.fields.data ]
        columns = '-'.join(columns)
        
        # type of values: normal or normalized
        normalize = False  #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CHANGE, this will be from form
        overlap   = False  #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CHANGE, this will be from form
        
        ## TEST <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        #contest = 'continents'
        #ids = 'Europe-Asia'
        
        return redirect(url_for('draw_graph', 
                                contest=contest, 
                                ids=ids, 
                                fields=columns, 
                                normalize=normalize, 
                                overlap=overlap
                               )
                       )

    #form.fields.data = ['1']                            # this sets a default value
    return render_template('select.html', 
                           title=_('Select country'), 
                           all_fields=FIELDS,
                           form=form,
                           nations=nations.get_for_list()
                          )


#@app.route('/graph/<ids>/')
@app.route('/graph/<contest>/<ids>/<fields>/<normalize>/<overlap>')
def draw_graph(contest, ids, fields='cases', normalize=False, overlap=False):
    '''show countries trend
       
    params: 
        - contest       str - nations | continents
        - ids           str - string of concat nation idsor continents;
                           e.g. it-fr-nl or  asia-europe
        - fields        str - string of concat fields to show; e.g. cases-deaths
        - normalized    bool - if true values are normalized on population
    
    functions:
        - draw nations cases
        - draw nations deaths
        - draw continents cases
        - draw continents deaths
        - draw normalized values
       '''
    fname = 'draw_graph'
    app.logger.debug('{}({}, {}, {}, {}, {})'.format(fname, contest, ids, fields, normalize, overlap))
    
    # START parameters check
    normalize = True if normalize in {'True', 'true',} else False
    overlap   = True if overlap   in {'True', 'true',} else False
    #   args to return here
    kwargs={'contest':  contest,
           'ids':       ids,
           'fields':    fields,
           'normalize': normalize,
           'overlap':   overlap,
          }
          
    #   check request contest
    if contest=='nations':
        country_field = 'geoId'
        country_name_field = 'countriesAndTerritories'
    elif contest=='continents':
        country_field = 'continentExp'
        country_name_field = 'continentExp'
    else:
        raise ValueError(_('%(function)s: contest %(contest)s is not allowed: ', function=fname, contest=contest))
        
    #   check request countries or continents
    countries = ids.split('-')                         # list of ids of nations or continents
    if contest=='nations':
        country_names = [ nations.get_nation_name(country) for country in countries]
    else:
        country_names = countries
        
    df = open_data(app.config['DATA_FILE'], pd.read_csv, world_shape)
    checklist = df[country_name_field].drop_duplicates()
    if set(country_names)-set(checklist):    # some countries aren't in checklist: not good
        unknown = set(country_names)-set(checklist)
        raise ValueError(_('%(function)s: these countries/continents are unknown: %(unknown)s', function=fname, unknown=unknown))
        
    # end of parameters checks
    continents_composition = None
    if contest=='continents':
        continents_composition = dict()
        for continent in country_names:
            continents_composition[continent] = nations[continent].copy()
    threshold = 0
    
    img_data, threshold = draw_nations(df, country_name_field, country_names, fields, normalize=normalize, overlap=overlap)
    
    title = _('overlap') if overlap else _('plot')
    kwargs['overlap'] = False if overlap else True    # ready to switch from overlap to not overlap, and vice versa
    
    columns = fields.split('-')
    
    return render_template('plot.html',
                           title=title,
                           columns=columns,
                           all_fields=FIELDS,
                           countries=country_names,
                           continents_composition=continents_composition,
                           overlap=overlap,
                           threshold=threshold,
                           img_data = img_data,
                           kwargs=kwargs,
                          )


def draw_nations(df, country_name_field, country_names, fields, normalize=False, overlap=False):
    fname = 'draw_nations'
    app.logger.debug(fname)
    
    fields = fields.split('-')                         # list of fields to plot
    allowed = set(list(FIELDS.keys()))
    if set(fields) - allowed:                          # some fields aren't allowed
        notallowed = set(fields)-allowed
        raise ValueError(_('%(function)s: these fields are not allowed: %(notallowed)s', function=fname, notallowed=notallowed))

    # adding d2cases_dt2
    if 'd²cases_dt²' in fields:
        df['d²cases_dt²'] = df['cases'] - df['cases'].shift(-1)

    if type(normalize) is not type(True):
        raise ValueError(_('%(function)s: on parameter <normalize>', function=fname))
    
    if ( type(overlap) is not type(True)
         or (overlap and len(fields)>1)
       ):
        raise ValueError(_('%(function)s: on parameter <overlap>', function=fname))
    
        
    sdf = df[(df[country_name_field].isin(country_names))]                # selected dataframe
    
    # building a dataframe with the necessary data
    edf = pd.DataFrame()                                                  # empty dataframe
    
    # temporary series to build dates; here as str 'yyyy-mm-dd'
    stemp = (sdf['year'].apply(lambda x:"{:04d}-".format(x)) +
                      sdf['month'].apply(lambda x:"{:02d}-".format(x)) +
                      sdf['day'].apply(lambda x:"{:02d}".format(x))
                     )
    
    edf['dateRep'] = stemp.map(lambda x: datetime.strptime(x, '%Y-%m-%d').date()) # date from str to date
    
    for field in fields:                                                  # adding fields cases&|deaths
        edf[field]  = sdf[field]
        
    edf[country_name_field] = sdf[country_name_field]                     # adding names of countries|continents
    edf = edf.groupby(['dateRep', country_name_field]).sum()
    
    if not overlap:
        threshold = 0
        sdf1 = pd.pivot_table(edf, index='dateRep',columns=country_name_field)
    else:
        threshold = suggest_threshold(edf, country_name_field, column=fields[0], ratio=THRESHOLD_RATIO)
        sdf1 = pivot_with_overlap(edf, country_name_field, column=fields[0], threshold=threshold)
    if sdf1 is None:
        raise ValueError(_('%(function)s: got an empty dataframe from pivot', function=fname))
    
    #breakpoint()        #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    #sdf1 = sdf1.cumsum()
    tmpfields = fields[:]
    if 'd²cases_dt²' in fields:
        tmpfields.remove('d²cases_dt²')
    for field in tmpfields:
        sdf1[field] = sdf1[field].cumsum()
    
    # fighting for a good picture
    fig = Figure(figsize=(9,7))
    if 'd²cases_dt²' in fields:
        ax = fig.add_axes([0.1,0.35,0.8,0.6])  # left, bottom, width, height
        ax2 = fig.add_axes([0.1,0.20,0.8,0.15], sharex=ax)
    else:
        ax = fig.subplots()
    
    xlabelrot = 80
    title  = _l('Observations about Covid-19 outbreak')
    ylabel = _l('number of cases') if not normalize else _l('rate to population')
    y2label = _l('n.of cases')
    xlabel = _l('date') if not overlap else _l('days from overlap point')
    
    fig = generate_figure(ax, sdf1, country_names, columns=tmpfields)
    
    ax.grid(True, linestyle='--')
    ax.legend()
    ax.set_title (title)
    ax.set_ylabel(ylabel)
    if 'd²cases_dt²' not in fields:
        ax.tick_params(axis='x', labelrotation=xlabelrot)
        ax.set_xlabel(xlabel)
        fig.subplots_adjust(bottom=0.2)
    
    if 'd²cases_dt²' in fields:
        fig = generate_figure(ax2, sdf1, country_names, columns=['d²cases_dt²'])
        ax2.set_ylabel(y2label)
        ax2.tick_params(axis='x', labelrotation=xlabelrot)
        ax2.grid(True, linestyle='--')
        ax2.legend()
        ax2.set_xlabel(xlabel)
    
    # Save it to a temporary buffer.
    buf = StringIO()
    fig.savefig(buf, format="svg")
    soup = bs.BeautifulSoup(buf.getvalue(),'lxml')          # parse image
    img_data = soup.find('svg')                             # get image data only (<svg ...> ... </svg>)
    return (img_data, threshold,)


def generate_figure(ax, df, countries, columns=None):
    '''# Generate the figure **without using pyplot**.'''
    if columns is None: columns = ['cases']
    
    for column, ltype in zip(columns, ['-', '--', '-.', ':'][0:len(columns)]):
        for country, color in zip(countries, COLORS[0:len(countries)]):
            ax.plot(df.index.values,          # x
                    df[column][country],         # y
                    ltype,
                    color=color,
                    label=_('%(column)s of %(country)s', column=column, country=country)         # label in legend
                   )
        
    fig = ax.get_figure()

    return fig


def world_shape(df):
    '''
    models dataframe to our needs
    
    params: df        pandas dataframe - df to model
    
    return df         pandas dataframe - the modeled dataframe
    '''
    df['dateRep'] = df['dateRep'].map(lambda x: datetime.strptime(x, app.config['D_FMT2']).date()) # from str to date
    df.loc[(df['countriesAndTerritories']=='CANADA'), 'countriesAndTerritories'] = 'Canada'
    return df


def open_data(fname, opener, shaper):
    '''read a dataframe from file
    
    params
      - fname      str or Path - name of file to read
      - opener     pandas method - method to use to read file
      - shaper     function - to shape dataframe before to return it
      
    return df          pandas dataframe
    '''
    df = opener(fname)
    df = shaper(df)
    return df


def suggest_threshold(df, country_name_field, column='cases', ratio=0.1):
    '''ratio of the more little between the max cases of the countries
    
    params:
        - df                     pandas dataframe MultiIndex: dateRep+country_name_field (countries | continents)
        - country_name_field     str - coutriesAndTerritories|continentExp
        - column                 str - column with values to check: cases|deaths
        - ratio                  float - ratio to apply default is 10%
        
    return threshold      int 
    '''

    countries = df.index.get_level_values(country_name_field).drop_duplicates().values.tolist()
    little_country, little_cases = (countries[0], df.xs(countries[0], level=country_name_field)[column].max(), )
    
    for country in countries[1:]:
        max_cases =  df.xs(country, level=country_name_field)[column].max()
        if max_cases < little_cases:
            little_country, little_cases = (country, max_cases,)
    return ceil(little_cases * ratio)
    
    
def pivot_with_overlap(df, country_name_field, column= 'cases', threshold=THRESHOLD):
    '''pivot a dataframe iterating over columns and dates traslating values to start at the same date
    
    params 
        - df                     pandas dataframe MultiIndex: dateRep+country_name_field (countries | continents)
        - country_name_field     str - coutriesAndTerritories|continentExp
        - column                 str - column with values to check: cases|deaths
        - threshold              int - value to overcome for two consecutive days
    
    return
        - sdf       pandas dataframe
        - None      in case of empty dataframe
    
    remark.
      given a (MultiIndex) df as   date+country cases death with:
        - date       a date
        - country    a country
        - cases      the total cases on the day (i.e, 
                       - if march 01 2020 cases is 100 @ Italy and we have 10 new cases in Italy that day,
                       -  then: march 02 2020 cases value is 110 @ Italy)
        - death      the total number of deceased on the day (same consideration as above) 
      example                        cases death 
                 date ...   country  
                 2020-03-01 country1  0     0     
                 2020-03-01 country2  80    8     
                 2020-03-02 country1  10    0     
                 2020-03-02 country2  20    8     
                 2020-03-03 country1  20    1     
                 2020-03-03 countryN  100   11    
                 ...
      this function builds a dataframe as
                 country1 country2 ... countryN
            row
            01   10       80           100
            02   20       20           ...
            03   ...      ...          ...
      where values in countryI are the cases in that country
      
      Warning: this function is pretty slow because iterate over rows
      
      Again: to align, seach a couple of adjacent days that exceed the indicated threshold
    '''
    fname = 'pivot_with_overlap'

    # building an empty df ...
    dates = df.index.get_level_values('dateRep').drop_duplicates().values.tolist()
    countries = df.index.get_level_values(country_name_field).drop_duplicates().values.tolist()

    sdf = pd.DataFrame(columns=[[],[]])                          # empty df, hierachical columns (two levels)
    #    ... iterating over countries ...
    for country in countries:
        #acountry = df[df[country_name_field]==country]
        acountry = df.xs(country, level=country_name_field)
        cases_list = []
        zero_flag = True                   # while true: skip to next day
        #        ... iterating over dates in a country
        for adate in dates:
            #            catch two adjacent days data
            try:
                cases = acountry.loc[adate, column]
            except:
                cases = None
            #            if we are skipping and cases is None, needless to continue, shunt the cicle
            if zero_flag and cases is None:
                continue
            #            cases is not None, get the 2nd day
            if zero_flag:
                try:
                    next_cases = acountry.loc[adate+timedelta(days=1), column]
                except:
                    next_cases = None
                
            #             if skip is true and two value are not None (cases isn't for sure) ...
            if (zero_flag and not next_cases is None):
                #         ... we check if the two values are both over threshold
                if (cases >= threshold and next_cases>= threshold):
                    zero_flag=False
                else:
                    continue
            #             if first condition is false, we check if skip is true; in such a case shunt to the for cycle
            elif zero_flag:
                continue
            #             if first condition is false, and skip is false, then we can work in the body of the for cycle
            else:
                pass
            #             preparing a list of cases
            cases = cases if cases is not None else 0
            cases_list.append(cases)
             #            if not last date, cicle, else add column to dataframe
            if adate+timedelta(days=1) in dates:
                continue
            else:
                # if new column is higher of dataframe, we need to stretch it, otherwise new column will be cutted
                if sdf.shape[1] > 0 and (sdf.shape[0] < len(cases_list)):
                    sdf = stretch(sdf, len(cases_list))
                sdf[column, country] = pd.Series(cases_list).astype(int)
                #app.logger.debug('{}: adding ({},{}) length: {}'.format(fname, column, country, len(cases_list)))

    if sdf.columns.to_list() == []:
        sdf = None
    return sdf

def stretch(df, height):
    '''raise the height of a dataframe to the requested size'''
    if df.shape[0] >= height:
        return df
    
    for ndx in range(df.shape[0], height):
        df.loc[ndx] = np.NaN * df.shape[1]
    return df

