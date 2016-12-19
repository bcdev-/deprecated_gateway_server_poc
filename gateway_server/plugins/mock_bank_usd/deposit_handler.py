import logging
from .web_interface import BankSim
from common.db import Session
from common.models import Withdrawal
from common.settings import currencies

logger = logging.getLogger(__name__)


class DepositHandler:
    def start(self):
        logger.info("Starting")
        self.bank_sim = BankSim()
        self.bank_sim.start()

    def tick(self):
        self._handle_withdrawals()
        logger.debug("Tick")

    def _handle_withdrawals(self):
        session = Session()

        # TODO: API for this
        plugin_name = __name__.split('.')[1]
        my_currency_ids = [c for c, p in currencies.items() if p == plugin_name]

        # TODO: Create a cutesy API for plugin creators
        print("asdfasdfasdfadsf")
        withdrawals = session.query(Withdrawal).filter_by(accepted=True, executed=False, rejected=False).filter(
            Withdrawal.currency.in_(my_currency_ids))
        for withdrawal in withdrawals:
            logger.info("Executing withdrawal %s" % withdrawal)
            withdrawal.executed = True
            session.commit()
            self.bank_sim.send_money(session, withdrawal.bank_account, withdrawal.amount)
            session.commit()
            session.flush()

        session.commit()
