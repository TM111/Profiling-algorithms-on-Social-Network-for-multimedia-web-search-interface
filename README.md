# ALGORITMI DI PROFILAZIONE SU SOCIAL NETWORK PER INTERFACCE DI RICERCA WEB MULTIMEDIALI (tesi 2018)

L’obiettivo della tesi consiste nella realizzazione di un sistema che permetta, sfruttando i dati dei Social Network degli utenti, di aiutare i motori di ricerca nel loro lavoro di espansione di query, ordinamento dei risultati, suggerimenti di ricerca e tutte quelle cose che hanno come scopo quello di andare in contro il più
possibile agli interessi dell’utente. É stata creato un motore di ricerca su contenuti Facebook di utenti che, attraverso una profilazione, restituisce per prima i contenuti che possono essere più utili per l’utente stesso.

[Documento tesi](https://github.com/TM111/Profiling-algorithms-on-Social-Network-for-multimedia-web-search-interface/blob/master/Tesi.pdf)

## Requisiti

- Java
- Python 2.7
- Django

## Guida

1) Go to http://lucene.apache.org/solr/downloads.html and download apache Solr
2) Run apache Solr with command "bin/solr start"
3) Go to the project folder and open app/views.py
4) At the beginning set solr_string with you solr url
5) Start app with the command "python manage.py runserver"
