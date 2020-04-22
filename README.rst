prerequisiti
-------------

* sistema windows
* python >= 3.6

installazione
--------------

da cmd::

  cd flask_covid
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  
esecuzione
-----------

da cmd::

  cd all_we_can_sea
  venv\Scripts\activate
  flask run
  
usare il browser per consultare http://localhost:5000

commenti
----------

il codice per avviare una applicazione flask (come questa) non è standard di python. è dovuto
al fatto che dovrà essere installata su un server per essere richiamata da un 
servizio httpd di qualche genere. Per ora ignoriamola.

ci basta sapere che il comando ``flask run`` legge un ambiente ripreso da 
``.flaskenv`` che lo pilota al caricamento di ``seasite.py``.

quest'ultimo importa dal package (alias directory) ``seasite`` l'applicazione
``app``.

``app`` viene creata automaticamente da ``__init__.py`` che a sua volta carica 
(importa) ``routes.py`` che contiene la logica di controllo.

la logica di controllo ha solo due entry:

* index risponde alle URL root (/) e /index visualizzando il template ``index.html``
  (posizionato nella subdir template)
* login risponde alla URL /login (incluso il metodo http POST); se la form
  di login è correttamente compilata, la processa e ritorna a /index; se la form
  non è compilata, allora visualizza il template di login, che la contiene.
  
la parte di visualizzazione è implementata con tre template:

* base.html, utilizzato come base per la costruzione delle videate. contiene
  l'header html. in testa al body vi è il menù. e in coda vi è il footer della
  pagina. Al centro il blocco ``{% block content %}{% endblock %}`` è
  il placeholder per mettere il contenuto principale della finestra.
* index.html pone nel blocco dei contenuti una divisione junbotron seguita da 
  una divisione composta da due colonne.
* login.html invece mette nei contenuti la form per effettuare il login


Tutto qui! le difficoltà sono due: 

* conoscere python in modo sufficiente per capire le chiamate a classi ed istanze di classi;
* conoscere il linguaggio usato per il templating (Jingja2). solo che chiamare 
  "linguaggio" il templating di jingja è veramente eccessivo: è tanto potente,
  quanto semplice da capire ed utilizzare.
  