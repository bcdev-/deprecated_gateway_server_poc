from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Boolean


class Account:
    kyc_name = Column(String, nullable=True, default=None)
    kyc_completed = Column(Boolean, default=False)


class Withdrawal:
    bank_account = Column(String, nullable=True, default=None)

    @classmethod
    def to_bank_account(cls, bank_account: str, account: Account):
        withdrawal = cls()
        withdrawal.bank_account = bank_account
        withdrawal.address = account.address
        return withdrawal


from unittest import TestCase


class TestModels(TestCase):
    def test_create(self):
        from common.models import Withdrawal, Account
        # Here I am testing if combine-all-models-onto-one-giant-class works.
        withdrawal = Withdrawal.to_bank_account("bank_account", Account("address", "public_key", "deposit_address"))

        self.assertEqual(withdrawal.address, "address")
