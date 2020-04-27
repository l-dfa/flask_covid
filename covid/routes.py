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

# import appllication modules
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
        
FIELDS_CHOICES = [('1', 'cases'), ('2', 'deaths'),]


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
    #breakpoint()
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
    form.fields.choices = FIELDS_CHOICES.copy()
    form.fields.default = ['1',]
    form.countries.choices = nations.get_for_select()
    
    if form.validate_on_submit():
        # contest: nations or continent
        contest = 'nations'  #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CHANGE, this will be from form
        # chaining nations ids
        ids = '-'.join(form.countries.data)             # here build string with nations ids: e.g. it-fr-nl
        # chaining names of fields to plot
        columns = [name for code, name in FIELDS_CHOICES if code in form.fields.data ]
        columns = '-'.join(columns)
        # type of values: normal or normalized
        normalize = False  #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CHANGE, this will be from form
        overlap   = False  #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CHANGE, this will be from form
        return redirect(url_for('draw_graph', 
                                contest=contest, 
                                ids=ids, 
                                fields=columns, 
                                normalize=normalize, 
                                overlap=overlap
                               )
                       )
    return render_template('select.html', 
                           title=_('Select country'), 
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
    app.logger.debug('draw_graph({}, {}, {}, {}, {})'.format(contest, ids, fields, normalize, overlap))
    normalize = True if normalize in {'True', 'true',} else False
    overlap   = True if overlap   in {'True', 'true',} else False
    # args to return here
    kwargs={'contest':  contest,
           'ids':       ids,
           'fields':    fields,
           'normalize': normalize,
           'overlap':   overlap,
          }
    # check request contest
    if contest not in {'continents', 'nations'}:
        raise KeyError
    # check resquest countries ids
    countries = ids.split('-')                         # list of ids of nations or continents
    country_names = [ nations.get_nation_name(country) for country in countries]
    df = open_data(app.config['DATA_FILE'], pd.read_csv, world_shape)
    if contest == 'nations':
        field = 'geoId'
    else:
        field = 'continentExp'
    checklist = df[field].drop_duplicates()
    if set(countries)-set(checklist):    # some countries aren't in checklist: not good
        unknown = set(countries)-set(checklist)
        raise ValueError(_('these countries are unknown: %(unknown)s', unknown=unknown))
    # end of parameters checks
    threshold = 0
    
    if contest == 'nations':
        img_data, threshold = draw_nations(df, countries, fields, normalize=normalize, overlap=overlap)
    else:
        img_data = draw_continents(df, countries, fields, normalize=normalize, overlap=overlap)
    
    title = _('overlap') if overlap else _('plot')
    kwargs['overlap'] = False if overlap else True    # ready to switch from overlap to not overlap, and vice versa
    
    columns = fields.split('-')
    
    return render_template('plot.html',
                           title=title,
                           columns=columns,
                           countries=country_names,
                           overlap=overlap,
                           threshold=threshold,
                           img_data = img_data,
                           kwargs=kwargs,
                          )


def draw_continents(df, countries, fields, normalized=False):
    '''DO NOT USE. this is a placeholder to develop'''
    app.logger.debug('draw_continents')
    raise KeyError
    sdf = df[(df['geoId'].isin(countries))]
    countries = sdf['countriesAndTerritories'].drop_duplicates().tolist()
    # this is slow but manage missing days
    sdf1 = pivot_by_iteration(sdf, column=column)
    sdf1 = sdf1.cumsum()

    # Generate the figure **without using pyplot**.
    fig = generate_figure(sdf1, countries, xlabelrot=80)
    
    # Save it to a temporary buffer.
    buf = StringIO()
    fig.savefig(buf, format="svg")
    soup = bs.BeautifulSoup(buf.getvalue(),'lxml')          # parse image
    img_data = soup.find('svg')                             # get image data only (<svg ...> ... </svg>)
    return render_template('plot.html',
                           title=_('plot'),
                           column=column,
                           countries=countries,
                           ids=ids,
                           overlap=False,
                           img_data = img_data
                          )


def draw_nations(df, countries, fields, normalize=False, overlap=False):
    app.logger.debug('draw_nations')
    fields = fields.split('-')                         # list of fields to plot
    allowed = {'cases', 'deaths'}
    if set(fields) - allowed:                          # some fields aren't allowed
        notallowed = set(fields)-allowed
        raise ValueError(_('%(function)s: these fields are not allowed: %(notallowed)s', function='draw_nations', notallowed=notallowed))

    if type(normalize) is not type(True):
        raise ValueError(_('%(function)s: on parameter <normalize>', function='draw_nations'))
    
    if type(overlap) is not type(True):
        raise ValueError(_('%(function)s: on parameter <overlap>', function='draw_nations'))
    
    sdf = df[(df['geoId'].isin(countries))]
    countries = sdf['countriesAndTerritories'].drop_duplicates().tolist()
    
    # fighting for a good picture
    fig = Figure(figsize=(9,7))
    ax = fig.subplots()
    xlabelrot = 80
    title  = _l('Observations about Covid-19 outbreak')
    ylabel = _l('number of cases') if not normalize else _l('rate to population')
    xlabel = _l('date') if not overlap else _l('days from overlap point')
    
    for field, ltype in zip(fields, ['-', '--', '-.', ':'][0:len(fields)]):
        if overlap:
            threshold = suggest_threshold(sdf, column=field, ratio=THRESHOLD_RATIO)
            sdf1 = pivot_with_overlap(sdf, column=field, threshold=threshold)
        else:
            threshold = 0
            sdf1 = pivot_by_iteration(sdf, column=field)  # this is slow but manage missing days
        
        if sdf1 is None:
            raise ValueError(_('%(function)s: got an empty dataframe from pivot', function='draw_nations'))
        
        sdf1 = sdf1.cumsum()

        # Generate the figure **without using pyplot**.
        fig = generate_figure(ax, sdf1, countries, column=field, ltype=ltype)
    
    ax.grid(True, linestyle='--')
    ax.legend()
    ax.tick_params(axis='x', labelrotation=xlabelrot)
    
    ax.set_title (title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.subplots_adjust(bottom=0.2)


    # Save it to a temporary buffer.
    buf = StringIO()
    fig.savefig(buf, format="svg")
    soup = bs.BeautifulSoup(buf.getvalue(),'lxml')          # parse image
    img_data = soup.find('svg')                             # get image data only (<svg ...> ... </svg>)
    return (img_data, threshold,)


def generate_figure(ax, df, countries, column='cases', ltype = '-'):
    '''# Generate the figure **without using pyplot**.'''
    
    for country, color in zip(countries, COLORS[0:len(countries)]):
        ax.plot(df.index.values,          # x
                df[country],         # y
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

def pivot_by_iteration(df, column='cases'):
    '''
    pivot a dataframe iterating over columns and dates
    
    params df        pandas dataframe
    
    return sdf       pandas dataframe
    
    remark.
      given a df as   date ... cases death country ... with:
        - date       a date
        - cases      the total cases on the day (i.e, 
                       - if march 01 2020 cases is 100 @ Italy and we have 10 new cases in Italy that day,
                       -  then: march 02 2020 cases value is 110 @ Italy)
        - death      the total number of deceased on the day (same consideration as above) 
        - country    a country
      example:   date ...     cases death country
                 2020-03-01   100   10    country1
                 2020-03-01   80    8     country2
                 ...
                 2020-03-01   101   11    countryN
      this function builds a dataframe as
                         country1 country2 ... countryN
            date
            2020-03-01   100      80           101
      where values in countryI are the cases in that country
      
      Warning: this function is pretty slow because iterate over rows
    '''
    
    # building an empty df with dates as index
    dates = df['dateRep'].drop_duplicates().sort_values()
    sdf = pd.DataFrame(dates, columns=['dateRep'])                  # df with dates
    countries = df['countriesAndTerritories'].drop_duplicates().tolist()
    sdf = sdf.reindex(sdf.columns.tolist() + countries, axis=1)   # add a column every country
    sdf.set_index('dateRep', inplace=True)                           # dates to index
    
    # iterating over countries
    for country in countries:
        acountry = df[df['countriesAndTerritories']==country]
        # iterating over dates in a country
        for adate in acountry['dateRep']:
            try:
                # what a mess to extract a value!
                # §§ CHECK §§
                sdf.loc[adate, country] = acountry[acountry['dateRep']==adate][column].values.tolist()[0]
            except:
                sdf.loc[adate, country] = np.nan
    
    return sdf

def suggest_threshold(df, column='cases', ratio=0.1):
    '''ratio of the more little between the max cases of the countries
    
    params:
        - df              pandas dataframe
        - column          str - column with values to check
        - ratio           float - ratio to apply default is 10%
        
    return threshold      int 
    '''
    countries = df['countriesAndTerritories'].drop_duplicates().tolist()
    little_country, little_cases = (countries[0], df[df['countriesAndTerritories']==countries[0]][column].max(), )
    for country in countries[1:]:
        max_cases =  df[df['countriesAndTerritories']==country][column].max()
        if max_cases < little_cases:
            little_country, little_cases = (country, max_cases,)
    return ceil(little_cases * ratio)
    
    
def pivot_with_overlap(df, column= 'cases', threshold=THRESHOLD):
    '''
    pivot a dataframe iterating over columns and dates
    traslating values to start at the same date
    
    params 
        - df                pandas dataframe
        - column          str - column with values to check
        - threshold       int - value to overcome for two consecutive days
    
    return
        - sdf       pandas dataframe
        - None      in case of empty dataframe
    
    remark.
      given a df as   date ... cases death country ... with:
        - date       a date
        - cases      the total cases on the day (i.e, 
                       - if march 01 2020 cases is 100 @ Italy and we have 10 new cases in Italy that day,
                       -  then: march 02 2020 cases value is 110 @ Italy)
        - death      the total number of deceased on the day (same consideration as above) 
        - country    a country
      example:   date ...     cases death country
                 2020-03-01   0     0     country1
                 2020-03-01   80    8     country2
                 2020-03-02   10    0     country1
                 2020-03-02   20    8     country2
                 2020-03-03   20    1     country1
                 2020-03-03   100   11    countryN
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
      
      Finally: column
    '''

    # building an empty df ...
    dates = df['dateRep'].drop_duplicates().sort_values(ascending=True)
    sdf = pd.DataFrame()                                         # empty df 
    countries = df['countriesAndTerritories'].drop_duplicates().tolist()
    #    ... iterating over countries ...
    for country in countries:
        acountry = df[df['countriesAndTerritories']==country]
        cases_list = []
        zero_flag = True                   # while true: skip to next day
        #        ... iterating over dates in a country
        for adate in dates:
            #            catch two adjacent days data
            try:
                # what a mess to extract a value!
                # §§ CHECK §§
                cases = acountry[acountry['dateRep']==adate][column].values.tolist()[0]
            except:
                cases = None
            #            if we are skipping and cases is None, needless to continue, shunt the cicle
            if zero_flag and cases is None:
                continue
            #            cases is not None, get the 2nd day
            if zero_flag:
                try:
                    next_cases = acountry[acountry['dateRep']==adate+timedelta(days=1)][column].values.tolist()[0]
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
            if adate+timedelta(days=1) in dates.values:
                continue
            else:
                sdf[country] = pd.Series(cases_list).astype(int)
    if sdf.columns.to_list() == []:
        sdf = None
    return sdf


