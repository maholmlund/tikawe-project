# Koodinpätkien jakaminen

## Sovelluksen nykytila
Käyttäjä pystyy:
- Luomaan tunnuksen
- Kirjautumaan sisään
- Julkaisemaan uuden lyhyen koodinpätkän (max n. 20 riviä)
- Valitsemaan koodikielen julkaistavaan koodipätkään
- Näkemään toisten käyttäjien julkaisuja
- Tykkäämään ja kommentoimaan toisten julkaisuja
- Poistamaan oman julkaisunsa
- Hakemaan julkaisuja hakusanan perusteella
- Tarkastelemaan käyttäjien profiileja ja näkemään julkaisut, niiden määrä, yms.
- Näkemään julkaisujen kommentit ja tykkäysten määrät

## Käyttö

Asenna flask-kirjasto:

```
$ pip install flask
```

Alusta tietokanta:

```
$ python3 database_init.py
```

Suorita sovellus:

```
$ flask --app src/pages.py run
```

Tietokannan alustus luo järjestelmään valmiiksi suuren määrän käyttäjiä, postauksia, tykkäyksiä ja kommentteja. Tietokannan alustuksessa voi kestää yli minuutti heikoimmilla koneilla. Kaikkien käyttäjäien käyttäjänimet ovat muotoa userX ja salasana "salasana".

SVG-kuvat: [tablericons.com](https://tablericons.com)
