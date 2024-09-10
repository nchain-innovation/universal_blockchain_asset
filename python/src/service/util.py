import sys
from tx_engine import Tx, TxIn


def is_unit_test() -> bool:
    """ Returns true if we are in a unit test
    """
    return 'unittest' in sys.modules.keys()


def hexstr_to_tx(tx_as_hexstr: str | None) -> Tx | None:
    """ Given a hexstr return the associated Tx
    """
    if tx_as_hexstr is None:
        return None
    else:
        return Tx.parse_hexstr(tx_as_hexstr)


def hexstr_to_txid(tx_as_hexstr: str | None) -> str | None:
    """ Given a hexstr return the associated Tx
    """
    if tx_as_hexstr is None:
        return None
    else:
        tx = Tx.parse_hexstr(tx_as_hexstr)
        return tx.id()


def tx_to_hexstr(tx: Tx | None) -> str | None:
    if tx is None:
        return None
    else:
        return tx.serialize().hex()


def hexstr_to_txin(txin_as_hexstr: str) -> TxIn:
    input = txin_as_hexstr.split(':')
    return TxIn(prev_tx = input[0], prev_index=int(input[1]))

