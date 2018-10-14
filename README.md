# p3_limpando_dados_OpenStreetMap

Linguagem: Python
Versão: 3.6
Environment: Anaconda
Dependencias: jupyter, pymongo, zipfile36

Análise será desenvolvida para área de Manhattan em New York USA:

https://www.openstreetmap.org/relation/8398124

Cordenadas do quandrante de Manhattan selecionado manualmente
<bounds minlat="40.6827000" minlon="-74.0486000" maxlat="40.8808000" maxlon="-73.9043000"/>

após a limpeza de dados irei analizar a relation = 8398124 e todas as suas referencias e subreferencias.

Para baixar os dados, que está compactado na pasta /data/mapa.osm.zip:

http://overpass-api.de/query_form.html

com a query:

(
node(40.6827000, -74.0486000, 40.8808000, -73.9043000);
<;
);out meta;

Mapa de features dos dados:

https://wiki.openstreetmap.org/wiki/Map_Features

Documentação do Tiger (Topologically Integrated Geographic Encoding and Referencing):
https://wiki.openstreetmap.org/wiki/TIGER
https://wiki.openstreetmap.org/wiki/TIGER_to_OSM_Attribute_Map