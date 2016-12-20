import logging
from common.db import Session
from common.models import Deposit, Account
from common.settings import currencies
import multiprocessing
import time
from .libdogecoin import get_last_transactions
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
            self._handle_deposits()
            time.sleep(1)

    def _tick(self):
        # self._handle_withdrawals()
        logger.debug("Tick")
        self._handle_deposits()

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
                        print(int(transaction['amount'] * (10 ** self.DOGECOIN_DECIMAL_PLACES)))
                        print(type(transaction['amount']))
                        # deposit = Deposit(account.address, my_currency_ids[0], transaction['amount'])
                        # deposit.dogecoin_txid = transaction['txid']
                        # deposit.accepted = True
                        # session.add(deposit)
                        # session.commit()
                        # session.flush()
                        # logger.info("New deposit: %s %s" % (account, deposit))


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
