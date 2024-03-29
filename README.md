# :shopping_cart: The Emporium: A Mock E-Shop 
An E-commerce Django project created out of curiosity

### What it has:
- Main page / categories / product pages
- Full cycle: cart -> checkout -> purchasing
- Editing cart (changing item quantity, removing item from the cart)

#### What I'm going to add:
- Customer authorisation
- Payment process

### How to install:
- clone this repo 
- create virtual environment ```python3 -m venv -venv```
- install requirments ```pip install -r requirements.txt```
- make sure you are in the same folder where file ```manage.py``` is
- I used built-in DB SQL Lite but if you want to use some other DB make sure it is properly configured in ```settings.py```
- deal with migrations ```python manage.py migrate```
- run server ```python manage.py runserver```

### What was used:
- Python 3
- Django
- Bootstrap 4
- Django Crispy Forms
- Pillow library
