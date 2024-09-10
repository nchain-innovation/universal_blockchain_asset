from typing import Any, Dict, Optional, List

from tx_engine import MockInterface
from service.util import hexstr_to_txid


class MockFinancingService:
    """ This class represents a Mock Financing Service interface
    """
    def __init__(self, mock_bsv_client: MockInterface, funds: List[str]):
        self.mock_bsv_client = mock_bsv_client
        self.funds_count = 0
        self.funds = funds

    def get_status(self) -> None | Dict[str, Any]:
        # print("mock financing service - get_status")
        return {}

    def get_funds(self, fee_estimate: int, locking_script: str) -> Optional[Dict[str, Any]]:
        # print(f"mock financing service - get_funds({fee_estimate}, {locking_script})")
        tx_str = self.funds[self.funds_count]
        # Broadcast tx
        self.mock_bsv_client.broadcast_tx(tx_str)
        txid = hexstr_to_txid(tx_str)
        assert isinstance(txid, str)
        retval = {
            'status': 'Success',
            'outpoints': [{'hash': txid, 'index': 1}],
            'tx': tx_str,
        }
        self.funds_count += 1
        return retval
