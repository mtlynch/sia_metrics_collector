import datetime
import unittest

from sia_metrics_collector import state


class SiaStateTest(unittest.TestCase):

    def test_equality(self):
        a = state.SiaState(
            timestamp=datetime.datetime(2018, 2, 11, 16, 5, 2),
            contract_count=5,
            file_count=3,
            uploads_in_progress_count=2,
            uploaded_bytes=900,
            contract_fee_spending=25,
            storage_spending=2,
            upload_spending=35,
            download_spending=0,
            remaining_renter_funds=100,
            wallet_siacoin_balance=75)
        a_copy = state.SiaState(
            timestamp=datetime.datetime(2018, 2, 11, 16, 5, 2),
            contract_count=5,
            file_count=3,
            uploads_in_progress_count=2,
            uploaded_bytes=900,
            contract_fee_spending=25,
            storage_spending=2,
            upload_spending=35,
            download_spending=0,
            remaining_renter_funds=100,
            wallet_siacoin_balance=75)
        b = state.SiaState(
            timestamp=datetime.datetime(2017, 10, 15, 12, 15, 56),
            contract_count=1,
            file_count=9,
            uploads_in_progress_count=1,
            uploaded_bytes=1800,
            contract_fee_spending=22,
            storage_spending=18,
            upload_spending=9,
            download_spending=2,
            remaining_renter_funds=105,
            wallet_siacoin_balance=85)
        self.assertEqual(a, a_copy)
        self.assertNotEqual(a, b)
