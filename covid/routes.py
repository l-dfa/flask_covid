# filename routes.py
#   views of flask_covid project / covid application

from io import StringIO
#from pathlib import Path
from datetime import datetime, date, timedelta

import bs4    as bs
import pandas as pd
import numpy  as np

#import covid.utils as u
from math import ceil

from flask      import Flask, flash, redirect, render_template, session, url_for
from flask import g
from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask_babel import get_locale

from markupsafe import escape
from matplotlib.figure import Figure

from covid       import app, nations
from covid.forms import SelectForm, SubmitField

WTITLE = "luciano de falco alfano's website"
THRESHOLD = 200
THRESHOLD_RATIO = 0.05

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
    g.locale = str(get_locale())
#def get_date_range(df):
#    return (df['dateRef'].min(), df['dateRef'].max(),)

@app.route('/')
@app.route('/index')
def index():
    '''section's home'''
    df = open_data(app.config['DATA_FILE'], pd.read_csv, world_shape)
    #first, last = get_data_range(df)
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
    form = SelectForm()
    #form.country.choices = nations.get_for_select()
    form.countries.choices = nations.get_for_select()
    if form.validate_on_submit():
        ids = '-'.join(form.countries.data)             # here build string with nations ids: e.g. it-fr-nl
        #breakpoint()   #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        return redirect(url_for('draw_graph', ids=ids))
    return render_template('select.html', 
                           title=_('Select country'), 
                           form=form
                          )


@app.route('/graph/<ids>')
def draw_graph(ids):
    '''show countries trend
    
       params: ids    str -  string of concat nation ids; e.g. it-fr-nl
       '''
    df = open_data(app.config['DATA_FILE'], pd.read_csv, world_shape)
    countries = ids.split('-')                         # list of ids
    sdf = df[(df['geoId'].isin(countries))]
    countries = sdf['countriesAndTerritories'].drop_duplicates().tolist()
    # this is slow but manage missing days
    sdf1 = pivot_by_iteration(sdf)
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
                           countries=countries,
                           ids=ids,
                           overlap=False,
                           img_data = img_data
                          )

@app.route('/overlap/<ids>')
def draw_overlap(ids):
    '''show overlapped countries trend
    
       params: ids    str -  string of concat nation ids; e.g. it-fr-nl
       '''
    df = open_data(app.config['DATA_FILE'], pd.read_csv, world_shape)
    countries = ids.split('-')                         # list of ids
    sdf = df[(df['geoId'].isin(countries))]
    countries = sdf['countriesAndTerritories'].drop_duplicates().tolist()
    # this is slow but manage missing days
    threshold = suggest_threshold(sdf, ratio=THRESHOLD_RATIO)
    sdf1 = pivot_with_overlap(sdf, threshold=threshold)
    if sdf1 is None:
      return "this is an error: go back!"
    sdf1 = sdf1.cumsum()

    # Generate the figure **without using pyplot**.
    fig = generate_figure(sdf1, countries)
    
    # Save it to a temporary buffer.
    buf = StringIO()
    fig.savefig(buf, format="svg")
    soup = bs.BeautifulSoup(buf.getvalue(),'lxml')          # parse image
    img_data = soup.find('svg')                             # get image data only (<svg ...> ... </svg>)
    return render_template('plot.html',
                           title=_('overlap'),
                           countries=countries,
                           ids=ids,
                           overlap=True,
                           threshold=threshold,
                           img_data = img_data
                          )

def generate_figure(df, countries, xlabelrot=0):
    '''# Generate the figure **without using pyplot**.'''
    fig = Figure()
    ax = fig.subplots()
    for country in countries:
        ax.plot(df.index.values,          # x
                df[country],         # y
                label=country          # label in legend
        )
    ax.grid(True, linestyle='-')
    ax.legend()
    ax.tick_params(axis='x', labelrotation=xlabelrot)
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

def pivot_by_iteration(df):
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
                sdf.loc[adate, country] = acountry[acountry['dateRep']==adate]['cases'].values.tolist()[0]
            except:
                sdf.loc[adate, country] = np.nan
    
    return sdf

def suggest_threshold(df, ratio=0.1):
    '''ratio of the more little between the max cases of the countries
    
    params:
        - df              pandas dataframe
        - ratio           float - ratio to apply default is 10%
        
    return threshold      int 
    '''
    countries = df['countriesAndTerritories'].drop_duplicates().tolist()
    little_country, little_cases = (countries[0], df[df['countriesAndTerritories']==countries[0]]['cases'].max(), )
    for country in countries[1:]:
        max_cases =  df[df['countriesAndTerritories']==country]['cases'].max()
        if max_cases < little_cases:
            little_country, little_cases = (country, max_cases,)
    return ceil(little_cases * ratio)
    
    
def pivot_with_overlap(df, threshold=THRESHOLD):
    '''
    pivot a dataframe iterating over columns and dates
    traslating values to start at the same date
    
    params 
      - df             pandas dataframe
    
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
    '''

    # building an empty df with dates as index ...
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
                cases = acountry[acountry['dateRep']==adate]['cases'].values.tolist()[0]
            except:
                cases = None
            #            if we are skipping and cases is None, needless to continue, shunt the cicle
            if zero_flag and cases is None:
                continue
            #            cases is not None, get the 2nd day
            if zero_flag:
                try:
                    next_cases = acountry[acountry['dateRep']==adate+timedelta(days=1)]['cases'].values.tolist()[0]
                except:
                    next_cases = None
            #if zero_flag and \
            #   (cases is None or cases < threshold or 
            #    next_cases is None or next_cases < threshold ):   # all zeros: goto next date
            #    continue
            #elif zero_flag:                                   # 1st not zero? this flag go down: no more stops values to add
            #    breakpoint()
            #    zero_flag = False
                
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


