import logging
from common.db import Session
from common.models import Deposit, Withdrawal, Account
from common.settings import currencies
import multiprocessing
import time
from .libdogecoin import get_last_transactions, send_dogecoin
from common.settings import dogecoin_confirmations

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
                        amount = int(transaction['amount'] * (10 ** self.DOGECOIN_DECIMAL_PLACES))
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
            withdrawal.dogecoin_txid = send_dogecoin(withdrawal.dogecoin_address, withdrawal.amount)
            session.commit()
            session.flush()

        session.commit()

        # def _handle_withdrawals(self):
        #     session = Session()
        #
        #     # TODO: API for this
        #     plugin_name = __name__.split('.')[1]
        #     my_currency_ids = [c for c, p in currencies.items() if p == plugin_name]
        #
        #     # TODO: Create a cutesy API for plugin creators
        #     print("asdfasdfasdfadsf")
        #     withdrawals = session.query(Withdrawal).filter_by(accepted=True, executed=False, rejected=False).filter(
        #         Withdrawal.currency.in_(my_currency_ids))
        #     for withdrawal in withdrawals:
        #         logger.info("Executing withdrawal %s" % withdrawal)
        #         withdrawal.executed = True
        #         session.commit()
        #         self.bank_sim.send_money(session, withdrawal.bank_account, withdrawal.amount)
        #         session.commit()
        #         session.flush()
        #
        #     session.commit()
