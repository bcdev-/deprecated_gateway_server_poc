# Front end settings
bind_address = "127.0.0.1"
bind_port = 6771

db_url = "sqlite:///gateway.db"

waves_api_url = "http://127.0.0.1:6869"
waves_api_key = "evik904i5v9mgoupgsnio"

testnet = True

gateway_address = "3N3qmHa1MBo3ZjDYJZbHNezY4RfhtTFxjXG"
gateway_private_key = b'\x88rz\x037{\xfb\xa1\xb3e\\^\xcb\x97\x8d\xa1q\xe0$\xaa\xd7"\xeeI\xff\xf9!Jt~pa'
import curve25519, base58
gateway_public_key = curve25519.public(gateway_private_key)
print("Gateway's public key:", gateway_public_key, base58.b58encode(gateway_public_key))

default_fee = 100000

#currencies = {"3k2qVm2BSGvjCXNBGdFwq5mYSrd4LJmVgfBGro4qRQ1W": "mock_bank_usd"}
currencies = {"CcvuevJVhadmRipPQgWkGDreUcdnRGWjBJ2ey7mzop9g": "dogecoin"}

required_confirmations = 0

start_from_block = 3301
rescan_blockchain = False

import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

session_timeout = 600  # 10 minutes

dogecoin_api_username = 'dogecoinrpc'
dogecoin_api_password = 'Fwotyfs1PcBw4WThocUZwjkaqYoryD4LEyBm7PuBqwX3'
dogecoin_api_url = 'http://127.0.0.1:22555'
dogecoin_main_address = 'DEYtqoRfH2MWytHskuvWFrrWZP1qH9H3vN'
dogecoin_confirmations = 0
dogecoin_withdrawal_fee = 1
