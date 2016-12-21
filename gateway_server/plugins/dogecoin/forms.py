from sqlalchemy.orm.session import Session
from flask import render_template, request
import flask
from front_end_manager.wac import WAC
from common.models import Withdrawal
from functools import wraps
from .libdogecoin import validate_address


def redirect_to_form(form):
    p1, p2, p3 = request.url.partition('?')
    p01, p02, p03 = p1.rpartition('/')
    url = p01 + p02 + form + p2 + p3
    return flask.redirect(url, code=302)


def kyc_required(redirect):
    def decorator(f):
        @wraps(f)
        def wrapper(session: Session, wac: WAC, *args, **kwds):
            if not wac.account.dogecoin_kyc_completed:
                return redirect_to_form(redirect)
            return f(session, wac, *args, **kwds)

        return wrapper

    return decorator


@kyc_required(redirect="kyc")
def details(session: Session, wac: WAC):
    '''
    currency = wac['currency']
    format = "%%d.%%.%dd%%s" % currency.decimals
    amount = get_currency_balance(account.address, currency.id)
    balance = format % (int(amount / (10 ** currency.decimals)),
                        int(amount % (10 ** currency.decimals)), currency.suffix)
    '''
    return render_template('dogecoin/details.html', wac=wac)


def kyc(session: Session, wac: WAC):
    valid = True
    refund_address = ''
    alert = ''
    refund = ''
    if 'refund_address' in request.args:
        refund_address = request.args['refund_address']
    if 'refund' not in request.args:
        alert += "You must decide what to do when the experiment with the Gateway is over\n"
        valid = False
    if 'refund' in request.args and request.args['refund'] == 'yes':
        if not validate_address(request.args['refund_address']):
            alert += "Your refund DogeCoin address is not valid.\n"
            valid = False
        refund = request.args['refund']

    if 'nohackrefunds' not in request.args or request.args['nohackrefunds'] != 'yes':
        alert += "You must acknowledge that this is an expermiental gateway and " + \
                 "that no refunds will be given in case of a hack.\n"
        valid = False

    if valid:
        wac.account.dogecoin_kyc_completed = True
        wac.account.dogecoin_refund_address = refund_address if len(refund_address) > 0 else None
        return redirect_to_form('details')

    return render_template('dogecoin/kyc.html', wac=wac, refund_address=refund_address, alert=alert.strip(),
                           refund=refund)


@kyc_required(redirect="kyc")
def withdraw(session: Session, wac: WAC):
    alert = ''
    dogecoin_account = ''
    if 'dogecoin_account' in request.args:
        if not validate_address(request.args['dogecoin_account']):
            alert = 'The Dogecoin address you provided is incorrect'
            dogecoin_account = request.args['dogecoin_account']
        else:
            withdrawal = Withdrawal.to_dogecoin_address(request.args['dogecoin_account'], wac.account)
            session.add(withdrawal)
            session.commit()
            return render_template('dogecoin/withdraw_redirect.html', wac=wac, withdrawal=withdrawal)

    return render_template('dogecoin/withdraw.html', wac=wac, alert=alert, dogecoin_account=dogecoin_account)


@kyc_required(redirect="kyc")
def deposit(session: Session, wac: WAC):
    return render_template('dogecoin/deposit.html', wac=wac)


@kyc_required(redirect="kyc")
def game(session: Session, wac: WAC):
    return render_template('dogecoin/game.html', wac=wac)


forms = {"details": details, "kyc": kyc, "withdraw": withdraw, "deposit": deposit, "game": game}
