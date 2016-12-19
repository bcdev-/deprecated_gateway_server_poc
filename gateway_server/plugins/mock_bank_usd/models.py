from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Boolean
from common.db import Base
from unittest import TestCase
import random
import string


class Account:
    def __init__(self):
        self.deposit_iban = self._create_mock_iban_account()

    def _create_mock_iban_account(self) -> str:
        return "MOCK" + ''.join(random.choice(string.digits) for _ in range(15))

    kyc_name = Column(String, nullable=True, default=None)
    kyc_completed = Column(Boolean, default=False)
    deposit_iban = Column(String, index=True)


class Withdrawal:
    bank_account = Column(String, nullable=True, default=None)

    @classmethod
    def to_bank_account(cls, bank_account: str, account: Account):
        withdrawal = cls()
        withdrawal.bank_account = bank_account
        withdrawal.address = account.deposit_address
        return withdrawal


########################
# Miscellaneous models #
########################


class BankSimBalances(Base):
    __tablename__ = "banksim_balances"

    def __init__(self, account, amount):
        self.bank_account = account
        self.balance = amount

    bank_account = Column(String, primary_key=True)
    balance = Column(Integer, default=0)


##############
# Unit tests #
##############


class TestModels(TestCase):
    def test_create(self):
        from common.models import Withdrawal, Account
        # Here I am testing if combine-all-models-onto-one-giant-class works.
        withdrawal = Withdrawal.to_bank_account("bank_account", Account("address", "public_key", "deposit_address"))

        self.assertEqual(withdrawal.address, "address")
