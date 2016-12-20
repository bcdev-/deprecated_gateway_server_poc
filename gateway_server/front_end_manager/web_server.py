from flask import Flask, request, Response
from waitress import serve
from common.db import Session
from .wac import WAC
from common.models import Account
import os
import importlib
import logging

logger = logging.getLogger(__name__)

from common.settings import bind_address, bind_port, currencies

template_dir = os.path.abspath('templates')
static_dir = os.path.abspath('static')
flask = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

'''
def verify_auth_hash(wac):
    assert(len(wac['auth_nonce']) == 32)
    assert(len(wac['auth_hash']) == 32)
    assert(len(wac['public_key']) <= base58_public_key_max_length)
    assert(len(wac['asset_id']) <= base58_asset_id_max_length)
    public_key = b58decode(wac['public_key'])
    shared_key = curve25519.shared(cfg.gateway_communication_private_key, public_key)
    out = ""
    for letter in curve25519.public(cfg.gateway_communication_private_key):
        out += str(letter) + ','
    b = blake2b(digest_size=32)
    b.update(shared_key + wac['auth_nonce'] + b58decode(wac['asset_id']) + public_key)

    assert(wac['auth_hash'] == b.digest())
'''
"""
def extract_wac_headers(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        '''
        # TODO: Require timestamp
        # TODO: Require auth hash
        # TODO: Rewrite WAC to a class
        session = Session()
        try:
            wac = dict()
            if 'Session-Id' in request.args:
                # TODO: Respect session's timeout
                # TODO: When timestamp becomes required, just add 1ms to the timestamp
                wac_session = session.query(WACSession).filter_by(session_id=request.args['Session-Id']).first()
                account = session.query(Account).filter_by(address=wac_session.address).first()
                wac['public_key'] = account.public_key
                wac['address'] = account.address
                wac['asset_id'] = wac_session.asset_id
                wac['currency'] = currencies[wac['asset_id']]

            else:
                # TODO: We don't need a timestamp. Let's just settle on nonce+auth_hash
                wac['auth_hash'] = b58decode(request.args['AuthHash'])
                wac['auth_nonce'] = b58decode(request.args['AuthNonce'])

                wac['public_key'] = bytes(request.args['Public-Key'], 'latin-1')
                wac['asset_id'] = request.args['Asset-Id']
                assert(request.args['Address'] == public_key_to_account(wac['public_key']))
                wac['address'] = request.args['Address']
                wac['currency'] = currencies[wac['asset_id']]

                verify_auth_hash(wac)

                wac_session = WACSession(wac['address'], wac['asset_id'])
                session.add(wac_session)
            wac['session_id'] = wac_session.session_id
        except Exception as e:
            logging.exception(e)
            content = {'message': 'WAC header invalid'}
            return json.dumps(content), 403

'''
        return f(wac, session, *args, **kwds)
    return wrapper
"""


@flask.route("/")
def index():
    return "GatewayServer v0.0000"


@flask.route("/v1/forms/<string:form_name>", methods=["GET"])
def forms(form_name):
    session = Session()
    wac = WAC(session, request.args)

    '''
        account = session.query(Account).filter_by(address=wac.address).first()
    if account is None:
#        account = Account(address=wac['address'], public_key=wac['public_key'], deposit_address=get_new_deposit_account())
        import random
        account = Account(address=wac.address, public_key=wac.public_key, deposit_address=str(random.random()))
        session.add(account)
        session.commit()
        logging.debug("Registering new account: " + str(account))
    '''

    if wac.asset_id not in currencies:
        logger.error("Unknown currency: %s" % wac.asset_id)
        return "Unknown currency: %s" % wac.asset_id

    plugin_name = currencies[wac.asset_id]

    plugin_forms = importlib.import_module("plugins.%s.forms" % plugin_name)
    if form_name in plugin_forms.forms:
        result = plugin_forms.forms[form_name](session, wac)
        session.commit()
        return result

    return "Form does not exist", 404


def start_webserver():
    logger.info("Starting webserver on %s:%d" % (bind_address, bind_port))
    # flask.run(host=bind_address, port=bind_port, debug=True)
    serve(flask, host=bind_address, port=bind_port, threads=1)
