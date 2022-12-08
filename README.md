# Erfgoed Leiden en Omstreken: Nexus-vocabulaire

Deze repository bevat de vocabulaire-opzet voor de migratie van de ELO digitale collecties naar Memorix Nexus. 

# Wat staat er in deze repo?
## Voorbeelddata en shape definities
In de map [voorbeelddata](voorbeelddata) staan exports uit Nexus die moeten corresponderen met de 
[shacl definities](shacl). De bestandsnamen van de definities corresponderen in 
[upper CamelCase](https://en.wikipedia.org/wiki/Camel_case) met de bestandsnamen van de voorbeelddata in 
[snake_case](https://en.wikipedia.org/wiki/Snake_case)

## Validatie
Deze repo bevat een data-validatiescript: [validate.py](validate.py). Je kan de requirements voor dit script installeren
met:
```shell
pipenv install --dev
```
Hiervoor heb je een recente Python installatie nodig (3.10 wordt aangeraden) en beschikking over de Python library
[pipenv](https://pypi.org/project/pipenv/). Pipenv installeren gaat met 
```shell
pip install --user pipenv
```
of met [pipx](https://pypi.org/project/pipx/):
```shell
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install pipenv
```

Daarna kan je het validatiescript uitvoeren: met
```shell
pipenv run python validate.py
```

Zie [config.yaml](config.yaml) over hoe je de validatie kan configureren.

### Data shape validatie
Door de corresponderende CamelCase/snake_case van de bestandsnamen van voorbeelddata en shape constraints, kan validatie
worden toegepast van de voorbeelddata tegen de shape constraints. 
