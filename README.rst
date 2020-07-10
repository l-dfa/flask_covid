flask_covid
================

A simple web application to draw time series of cases of covid-19 
outbreak in selectable countries.

This project uses data from `European Centre for Disease Prevention and Control <https://www.ecdc.europa.eu/en>`_.
Data available in development environment range from 2019-12-31 to 2020-04-24.

If you wish an updated version of data, you can grab it 
`from this URL <https://opendata.ecdc.europa.eu/covid19/casedistribution/csv>`_
and substitute, using the same filename, ``./covid/data/covid-20200424.csv``.
Alternatively, you can change the ``DATA_FILE`` value in ``./config.py`` file.

Prerequisites of the development environment
---------------------------------------------

Base environments:

* `git <https://git-scm.com/downloads>`_
* `python <https://www.python.org/downloads/>`_ >= 3.6

Third parties libraries:

* flask
* python-dotenv
* flask-wtf
* flask-babel
* pandas
* matplotlib
* beautifulsoup4
* lxml


To install the development environment
----------------------------------------

In cmd::

  git clone https://github.com/l-dfa/flask_covid-1.git
  ren flask_covid-1 flask_covid
  cd flask_covid
  python -m venv venv
  venv\Scripts\activate   # or venv/bin/activate on Linux
  python -m pip install --upgrade pip
  
Then if you wish to get the original project 3rd parties libraries:

  pip install -r requirements.txt
  
Otherwise, if you wish to install 3rd parties libraries from scratch
(it means: updated versions):

  pip install flask
  pip install python-dotenv
  pip install flask-wtf
  pip install flask-babel
  pip install pandas
  pip install matplotlib
  pip install beautifulsoup4
  pip install lxml
  
  
To exec application in development environment
-------------------------------------------------

In cmd, to run the development http server::

  cd flask_covid
  venv\Scripts\activate   # or venv/bin/activate on Linux
  flask run
  
Then, please, use a web browser to show http://localhost:5000

License
----------

`CC BY-SA 4.0 <https://creativecommons.org/licenses/by-sa/4.0/>`_

