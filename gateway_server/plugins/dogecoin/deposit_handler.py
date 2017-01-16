import logging
from common.db import Session
from common.models import Deposit, Withdrawal, Account
from common.settings import currencies
import multiprocessing
import time
from .libdogecoin import get_last_transactions, send_dogecoin
from common.settings import dogecoin_confirmations, dogecoin_withdrawal_fee

logger = logging.getLogger(__name__)


class DepositHandler(multiprocessing.Process):
    DOGECOIN_DECIMAL_PLACES = 8

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self._scanned_transactions = 0

    def run(self):
        while True:
            self._tick()
            time.sleep(1)

    def _tick(self):
        # self._handle_withdrawals()
        logger.debug("Tick")
        self._handle_deposits()
        self._handle_withdrawals()

    def _handle_deposits(self):
        session = Session()

        plugin_name = __name__.split('.')[1]
        my_currency_ids = [c for c, p in currencies.items() if p == plugin_name]

        # TODO: List unconfirmed deposits
        for transaction in get_last_transactions():
            if transaction['category'] == 'receive' and transaction['confirmations'] >= dogecoin_confirmations:
                account = session.query(Account).filter_by(dogecoin_deposit_address=transaction['address']).first()
                if account is not None:
                    deposit = session.query(Deposit).filter_by(dogecoin_txid=transaction['txid']).first()
                    if deposit is None:
                        real_amount = transaction['amount']
                        if real_amount <= 0:
                            amount = 0
                        amount = int(real_amount * (10 ** self.DOGECOIN_DECIMAL_PLACES))
                        deposit = Deposit(account.address, my_currency_ids[0], amount)
                        deposit.dogecoin_txid = transaction['txid']
                        deposit.accepted = True
                        logger.info("New deposit: %s %s" % (account, deposit))
                        session.add(deposit)
                        session.commit()
                        session.flush()

        session.commit()

    def _handle_withdrawals(self):
        session = Session()

        plugin_name = __name__.split('.')[1]
        my_currency_ids = [c for c, p in currencies.items() if p == plugin_name]

        pending_withdrawals = session.query(Withdrawal).filter_by(currency=my_currency_ids[0], accepted=True,
                                                                  executed=False, rejected=False)
        for withdrawal in pending_withdrawals:
            account = session.query(Account).filter_by(address=withdrawal.address).first()
            logger.info("New withdrawal: %s %s" % (account, withdrawal))
            withdrawal.executed = True
            session.commit()
            session.flush()
            real_amount = withdrawal.amount - dogecoin_withdrawal_fee * (10 ** self.DOGECOIN_DECIMAL_PLACES)
            withdrawal.dogecoin_txid = send_dogecoin(withdrawal.dogecoin_address, real_amount)
            session.commit()
            session.flush()

        session.commit()
