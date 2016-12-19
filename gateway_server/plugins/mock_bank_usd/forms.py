from sqlalchemy.orm.session import Session
from flask import render_template, request
import flask
from front_end_manager.wac import WAC
from common.models import Withdrawal
from functools import wraps


def kyc_required(redirect):
    def decorator(f):
        @wraps(f)
        def wrapper(session: Session, wac: WAC, *args, **kwds):
            if not wac.account.kyc_completed:
                p1, p2, p3 = request.url.partition('?')
                p01, p02, p03 = p1.rpartition('/')
                url = p01 + p02 + redirect + p2 + p3
                return flask.redirect(url, code=302)
            return f(session, wac, *args, **kwds)

        return wrapper

    return decorator


def details(session: Session, wac: WAC):
    '''
    currency = wac['currency']
    format = "%%d.%%.%dd%%s" % currency.decimals
    amount = get_currency_balance(account.address, currency.id)
    balance = format % (int(amount / (10 ** currency.decimals)),
                        int(amount % (10 ** currency.decimals)), currency.suffix)
    '''
    return render_template('details.html', wac=wac)


def kyc(session: Session, wac: WAC):
    if request.args['country'] == 'iran':
        s = "Unfortunately, due to a government embargo, we're currently unable to serve customers from Iran.<br/><br/>"
        s += "<button onclick=\"window.top.postMessage(['gateway_close_form'], '*');\">Close</button>"
        return s
    wac.account.kyc_name = request.args['name']
    wac.account.kyc_completed = True
    return render_template('details.html', wac=wac)


@kyc_required(redirect="details")
def withdraw(session: Session, wac: WAC):
    if 'bank_account' in request.args:
        withdrawal = Withdrawal.to_bank_account(request.args['bank_account'], wac.account)
        session.add(withdrawal)
        session.commit()
        return render_template('withdraw_to_bank.html', wac=wac, withdrawal=withdrawal)

    return render_template('withdraw.html', wac=wac)


def deposit(session: Session, wac: WAC):
    return render_template('deposit.html', wac=wac)


forms = {"details": details, "kyc": kyc, "withdraw": withdraw, "deposit": deposit}
