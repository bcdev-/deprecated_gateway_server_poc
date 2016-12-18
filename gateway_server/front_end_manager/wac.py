from pyblake2 import blake2b
import curve25519
from base58 import b58decode
from common.settings import gateway_private_key
from common.address import public_key_to_account
from common.db import Session
from common.models import UserSession, Account

base58_max_length = 50


class WAC:
    """Wallet Authentication Challenge

    WAC header serves to authenticate the account to the GatewayServer.
    """

    def __init__(self, session: Session, request_args):
        if 'Session-Id' in request_args:
            # TODO: Respect session's timeout
            user_session = session.query(UserSession).filter_by(session_id=request_args['Session-Id']).first()
            self.account = session.query(Account).filter_by(address=user_session.address).first()
            self.public_key = self.account.public_key
            self.address = self.account.address
            self.asset_id = user_session.currency
        else:
            self.asset_id = request_args['Asset-Id']
            self.auth_hash = b58decode(request_args['AuthHash'])
            self.auth_nonce = b58decode(request_args['AuthNonce'])
            self.public_key = bytes(request_args['Public-Key'], 'latin-1')
            self.address = request_args['Address']
            if self.address != public_key_to_account(request_args['Public-Key']):
                raise PermissionError("Public key is and address differ")
            self.account = Account.get_or_create(session, self.address, self.public_key)
            if not self._is_auth_hash_valid(self.public_key, self.auth_hash, self.auth_nonce, self.asset_id):
                raise PermissionError("WAC header is invalid")
            user_session = UserSession(self.address, self.asset_id)
            session.add(user_session)
        self.session_id = user_session.session_id

    @staticmethod
    def _is_auth_hash_valid(public_key, auth_hash, auth_nonce, asset_id):
        if (len(auth_nonce) != 32 or len(auth_hash) != 32 or len(public_key) > base58_max_length or
                    len(asset_id) > base58_max_length):
            return False
        public_key = b58decode(public_key)
        shared_key = curve25519.shared(gateway_private_key, public_key)
        out = ""
        for letter in curve25519.public(gateway_private_key):
            out += str(letter) + ','
        b = blake2b(digest_size=32)
        b.update(shared_key + auth_nonce + b58decode(asset_id) + public_key)

        return auth_hash == b.digest()

    def __eq__(self, other):
        return self.address == other.address and self.asset_id == other.asset_id and self.session_id == other.session_id


from unittest import TestCase
from sqlalchemy import create_engine
from common.db import Base
from sqlalchemy.orm import sessionmaker


class WACTest(TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_wac_incorrect_1(self):
        args = dict()
        args['Public-Key'] = "GKjxK8Q2a88Qes5WDmfmgA5fYXjVfFnyGTfXCzrGsmPP"
        args['Asset-Id'] = "3A2FXAmdSKVGxikERJvC13FG7ADf2sqb8kmzYokUzxm9"
        args['Address'] = "3N4sSM2mDoQ86qLD8LHR49hX2VF8SfWrUae"
        args['AuthHash'] = "ERKzMvUJGx36GKXapihPgJeZTPwrYkU2DpeoHF1Sdxwd"
        args['AuthNonce'] = "dRTyHTrvhH8ue89J6SD2gRuE6uPM9nxJDvyahhoZSGQ"
        global gateway_private_key
        gateway_private_key = b'\x88rz\x037{\xfb\xa1\xb3e\\^\xcb\x97\x8d\xa1q\xe0$\xaa\xd7"\xeeI\xff\xf9!Jt~pb'
        with self.assertRaises(PermissionError):
            WAC(self.session, args)

    def test_wac_incorrect_2(self):
        args = dict()
        args['Public-Key'] = "GKjxK8Q2a88Qes5WDmfmgA5fYXjVfFnyGTfXCzrGsmPP"
        args['Asset-Id'] = "3A2FXAmdSKVGxikERJvC13FG7ADf2sqb8kmzYokUzxm9"
        args['Address'] = "3N4sSM2mDoQ86qLD8LHR49hX2VF8SfWrUaf"
        args['AuthHash'] = "ERKzMvUJGx36GKXapihPgJeZTPwrYkU2DpeoHF1Sdxwd"
        args['AuthNonce'] = "dRTyHTrvhH8ue89J6SD2gRuE6uPM9nxJDvyahhoZSGQ"
        global gateway_private_key
        gateway_private_key = b'\x88rz\x037{\xfb\xa1\xb3e\\^\xcb\x97\x8d\xa1q\xe0$\xaa\xd7"\xeeI\xff\xf9!Jt~pa'
        with self.assertRaises(PermissionError):
            WAC(self.session, args)

    def test_wac_correct(self):
        args = dict()
        args['Public-Key'] = "GKjxK8Q2a88Qes5WDmfmgA5fYXjVfFnyGTfXCzrGsmPP"
        args['Asset-Id'] = "3A2FXAmdSKVGxikERJvC13FG7ADf2sqb8kmzYokUzxm9"
        args['Address'] = "3N4sSM2mDoQ86qLD8LHR49hX2VF8SfWrUae"
        args['AuthHash'] = "ERKzMvUJGx36GKXapihPgJeZTPwrYkU2DpeoHF1Sdxwd"
        args['AuthNonce'] = "dRTyHTrvhH8ue89J6SD2gRuE6uPM9nxJDvyahhoZSGQ"
        global gateway_private_key
        gateway_private_key = b'\x88rz\x037{\xfb\xa1\xb3e\\^\xcb\x97\x8d\xa1q\xe0$\xaa\xd7"\xeeI\xff\xf9!Jt~pa'
        wac = WAC(self.session, args)
        self.assertEqual(wac.asset_id, args['Asset-Id'])
        self.assertEqual(wac.address, args['Address'])
        print(wac.session_id)
        self.session.commit()

        args2 = dict()
        args2['Session-Id'] = wac.session_id
        wac2 = WAC(self.session, args2)
