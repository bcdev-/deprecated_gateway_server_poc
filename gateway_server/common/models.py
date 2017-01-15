import logging
import datetime
import time
import random
import string
import json
import importlib
from .db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm.session import Session
from .settings import currencies, session_timeout
from .currencies import currencies as currencies_fancy
from .node import get_new_deposit_account

logger = logging.getLogger(__name__)

AccountExt = []
DepositExt = []
WithdrawalExt = []

plugins_models = [importlib.import_module("plugins.%s.models" % p) for p in currencies.values()]
for plugin_model in plugins_models:
    if hasattr(plugin_model, 'Account'):
        AccountExt.append(plugin_model.Account)
    if hasattr(plugin_model, 'Deposit'):
        DepositExt.append(plugin_model.Deposit)
    if hasattr(plugin_model, 'Withdrawal'):
        WithdrawalExt.append(plugin_model.Withdrawal)


class Account(Base, *AccountExt):
    __tablename__ = 'accounts'

    def __init__(self, address, public_key, deposit_address, *args, **kwargs):
        self.address = address
        self.public_key = public_key
        self.deposit_address = deposit_address
        for account_extension in AccountExt:
            account_extension.__init__(self)

    @staticmethod
    def get_or_create(session, address, public_key):
        account = session.query(Account).filter_by(address=address).first()
        if account is None:
            # TODO: Deposit address
            account = Account(address, public_key, deposit_address=get_new_deposit_account())
            logger.info("Registering new account: " + str(account))
            session.add(account)
        return account

    # TODO: Active&Inactive account
    # TODO: Created date for purging useless
    address = Column(String, unique=True, primary_key=True)
    public_key = Column(String, unique=True)
    deposit_address = Column(String, unique=True)

    def __repr__(self):
        return "<Account(public_key='%s', address='%s')>" % (
            self.public_key, self.address)


# if incoming_blockchain_transaction->attachment == bank_withdrawal->attachment:
#   process_withdrawal
# else:
#   send_back_refund
# TODO: Rename to IncomingTransaction... Or WithdrawalTransaction
class BlockchainTransaction(Base):
    __tablename__ = 'blockchain_transactions'

    def __init__(self, transaction_id, address, type, timestamp, attachment, currency=None, amount=None):
        self.transaction_id = transaction_id
        self.address = address
        self.type = type
        self.currency = currency
        self.amount = amount
        self.timestamp = timestamp
        self.attachment = attachment

    # TODO: Block [confirmations]
    transaction_id = Column(String, primary_key=True)
    # TODO: Rename address to user
    address = Column(String, ForeignKey('accounts.address'), index=True)
    type = Column(Integer)
    timestamp = Column(BigInteger)
    currency = Column(String, nullable=True)
    amount = Column(BigInteger, nullable=True)
    attachment = Column(String, index=True)

    already_accounted = Column(Boolean, default=False, index=True)

    @property
    def timestamp_readable(self):
        return datetime.datetime.fromtimestamp(self.timestamp / 1000.).strftime('%d.%m.%Y %H:%M:%S')

    @staticmethod
    def get_all_transactions(session: Session, account: Account):
        return session.query(BlockchainTransaction).filter_by(address=account.address).all()


class Deposit(Base, *DepositExt):
    __tablename__ = 'deposit'

    def __init__(self, address, currency, amount, *args, **kwargs):
        self.address = address
        self.currency = currency
        self.amount = amount
        [deposit_ext.__init__(self, *args, **kwargs) for deposit_ext in DepositExt]

    def __str__(self):
        return "<Deposit %s %s %d>" % (self.address, self.currency, self.amount)

    @staticmethod
    def get_all(session: Session, account: Account) -> list:
        return session.query(Deposit).filter_by(address=account.address).all()

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String, ForeignKey('accounts.address'), index=True)
    currency = Column(String)
    """Blockchain asset ID"""

    amount = Column(BigInteger)

    accepted = Column(Boolean, default=False, index=True)
    """Transaction is accepted for execution - it's confirmed&accounted [in case of banking transactions]
    or has sufficient amount of confirmations [in case of blockchain transactions]"""

    executed = Column(Boolean, default=False, index=True)
    """Transaction was executed. It doesn't matter what kind of execution it is [it may be a refund, a deposit or
    really anything else]"""

    rejected = Column(Boolean, default=False, index=True)
    """Deposit was rejected"""

    waves_transaction_id = Column(String, nullable=True, default=None)
    # TODO: Add timestamp

    @property
    def currency_name(self) -> str:
        if self.currency in currencies_fancy:
            return currencies[self.currency].name
        return "UnknownCurrency<%s>" % self.currency

    @property
    def amount_formatted(self) -> str:
        currency = currencies_fancy[self.currency]

        str_format = "%%d.%%.%dd%%s" % currency.decimals
        return str_format % (int(self.amount / (10 ** currency.decimals)),
                             int(self.amount % (10 ** currency.decimals)), currency.suffix)


class Withdrawal(Base, *WithdrawalExt):
    __tablename__ = 'withdrawal'
    WITHDRAWAL_ID_LENGTH = 32

    def __init__(self, *args, **kwargs):
        self.attachment = ''.join(random.choice(string.digits + string.ascii_uppercase + string.ascii_lowercase)
                                  for _ in range(self.WITHDRAWAL_ID_LENGTH))

    def accept(self, transaction: BlockchainTransaction):
        assert(self.accepted is False)
        self.currency = transaction.currency
        self.amount = transaction.amount
        self.transaction_id = transaction.transaction_id
        self.address = transaction.address
        self.accepted = True

    @property
    def attachment_javascript_array(self):
        return str([ord(c) for c in self.attachment])

    address = Column(String, ForeignKey('accounts.address'), index=True)
    attachment = Column(String, primary_key=True)
    """Attachment is a withdrawal's ID."""

    currency = Column(String, index=True)  # Asset ID
    amount = Column(BigInteger)
    transaction_id = Column(String, ForeignKey('blockchain_transactions.transaction_id'), nullable=True)
    # TODO: Timestamp to purge old failed withdrawals.
    accepted = Column(Boolean, default=False, index=True)
    executed = Column(Boolean, default=False, index=True)
    rejected = Column(Boolean, default=False, index=True)

    @property
    def currency_name(self) -> str:
        if self.currency in currencies_fancy:
            return currencies[self.currency].name
        return "UnknownCurrency<%s>" % self.currency

    @property
    def amount_formatted(self) -> str:
        currency = currencies_fancy[self.currency]

        str_format = "%%d.%%.%dd%%s" % currency.decimals
        return str_format % (int(self.amount / (10 ** currency.decimals)),
                             int(self.amount % (10 ** currency.decimals)), currency.suffix)


class UserSession(Base):
    __tablename__ = 'user_sessions'
    SESSION_ID_LENGTH = 32

    def __init__(self, address, currency):
        self.address = address
        self.currency = currency
        self.timeout = int(time.time()) + session_timeout
        # TODO: Make sure to use a secure source of randomness here
        self.session_id = ''.join(random.choice(string.digits + string.ascii_uppercase + string.ascii_lowercase)
                                  for _ in range(self.SESSION_ID_LENGTH))

    session_id = Column(String, primary_key=True)
    address = Column(String, ForeignKey('accounts.address'))
    timeout = Column(BigInteger, index=True)
    currency = Column(String)


class Parameters(Base):
    __tablename__ = 'parameters'

    def __init__(self, key: str, value):
        self.key = key
        self.value = json.dumps(value)

    key = Column(String, primary_key=True)
    value = Column(String)

    @classmethod
    def get(cls, session: Session, key: str, default_value=None):
        param = session.query(cls).get(key)
        if param is None:
            param = Parameters(key, default_value)
            session.add(param)
            session.commit()
        return default_value
        return json.loads(param.value)

    @classmethod
    def set(cls, session: Session, key: str, value):
        param = session.query(cls).get(key)
        if param is None:
            param = Parameters(key, value)
            session.add(param)
        else:
            param.value = json.dumps(value)
        session.commit()
