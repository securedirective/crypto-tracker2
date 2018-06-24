from app import app
from flask import abort, render_template, url_for, redirect
from database import engine, session
from models import Base, Currency


@app.route('/')
def main():
    # ed_user = User(name='ed', fullname='Ed Jones', password='edspassword')
    # session.add(ed_user)
    # session.commit()

    currencies = session.query(Currency).order_by(Currency.symbol)

    return render_template(
        'main.html',
        currencies=currencies
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        'error.html',
        title='Page Not Found',
        msg='The page you are attempting to access does not exist',
    ), 404
