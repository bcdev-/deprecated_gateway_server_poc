import multiprocessing
import time
import logging
from common.db import Session
from common.models import Deposit, Account, BlockchainTransaction, Withdrawal
from common.node import send_currency, get_waves_balance
from common.settings import start_from_block, required_confirmations
from common.node import get_current_height, get_transactions_for_block
from base58 import b58decode

logger = logging.getLogger(__name__)


class WavesManager(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.current_block = min(start_from_block, get_current_height())

    def run(self):
        logger.info("Started")

        while True:
            self._handle_deposits()
            self._handle_withdrawals()
            self._scan_blockchain()
            time.sleep(1)

    def _handle_deposits(self):
        session = Session()

        pending_deposits = session.query(Deposit).filter_by(accepted=True, executed=False, rejected=False)
        for deposit in pending_deposits:
            logger.info("Handling deposit %s" % deposit)
            # TODO: Double verify deposits [check for amount of confirmations] ???
            # TODO: Use two phased transactions here to protect against two WavesManagers running at once

            deposit.executed = True
            session.commit()
            deposit.waves_transaction_id = send_currency(deposit.currency, deposit.address, deposit.amount)
            session.commit()
            session.flush()
            # Send 0.1 Waves for transaction fees if the client has less than 0.01
            if get_waves_balance(deposit.address) < 1000000:
                send_currency(None, deposit.address, 10000000)

        session.commit()
        session.flush()

    def _handle_withdrawals(self):
        session = Session()

        # TODO: Optimize this query to use relations
        pending_withdrawals = session.query(Withdrawal).filter_by(accepted=False, executed=False, rejected=False)
        for withdrawal in pending_withdrawals:
            transaction = session.query(BlockchainTransaction).filter_by(attachment=withdrawal.attachment).first()
            if transaction is not None:
                withdrawal.accept(transaction)
                session.commit()
                session.flush()
        session.commit()
        session.flush()

    def _scan_blockchain(self):
        session = Session()
        # TODO: Handle forks properly.
        while self.current_block <= get_current_height() - required_confirmations:
            logging.info("Scanning block %d" % self.current_block)
            self._scan_block(session, self.current_block)
            self.current_block += 1
        session.commit()

    def _scan_block(self, session: Session, block_number: int):
        transactions = get_transactions_for_block(block_number)
        for tx in transactions:
            if tx["type"] == 4:  # Asset transfer transaction
                account = session.query(Account).filter_by(deposit_address=tx["recipient"]).first()
                if account and session.query(BlockchainTransaction).get(tx["id"]) is None:
                    attachment = ''.join(chr(x) for x in b58decode(tx["attachment"]))
                    logging.info("\t❤❤❤❤ A new withdrawal transaction received. - %s" % tx["id"])
                    logging.info("\tFrom %s" % account.address)
                    logging.info("\tTo %s" % tx["recipient"])
                    logging.info("\tAsset %s" % tx["assetId"])
                    logging.info("\tAmount %d" % tx["amount"])
                    logging.info("\tAttachment %s" % attachment)
                    # TODO: Check if currency is defined
                    blockchain_transaction = BlockchainTransaction(tx["id"], account.address, tx["type"],
                                                                   tx["timestamp"], attachment, tx["assetId"],
                                                                   tx["amount"])
                    session.add(blockchain_transaction)
