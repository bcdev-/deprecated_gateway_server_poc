from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Boolean
from .libdogecoin import get_new_address
from common.db import Base


class Account:
    def __init__(self):
        self.dogecoin_deposit_address = get_new_address()

    dogecoin_deposit_address = Column(String, index=True)
    dogecoin_kyc_completed = Column(Boolean, default=False)
    dogecoin_refund_address = Column(String, nullable=True, default=None)


class Withdrawal:
    dogecoin_address = Column(String, nullable=True, default=None)
    dogecoin_txid = Column(String)

    @classmethod
    def to_dogecoin_address(cls, dogecoin_address: str, account: Account):
        withdrawal = cls()
        withdrawal.dogecoin_address = dogecoin_address
        withdrawal.address = account.deposit_address
        return withdrawal


class Deposit:
    dogecoin_txid = Column(String, nullable=True, default=None, index=True)
    dogecoin_block = Column(Integer, nullable=True, default=None)

########################
# Miscellaneous models #
########################


##############
# Unit tests #
##############


# class TestModels(TestCase):
#     def test_create(self):
#         from common.models import Withdrawal, Account
#         # Here I am testing if combine-all-models-onto-one-giant-class works.
#         withdrawal = Withdrawal.to_bank_account("bank_account", Account("address", "public_key", "deposit_address"))
#
#         self.assertEqual(withdrawal.address, "address")
