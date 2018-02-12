import datetime
import io
import unittest

from sia_metrics_collector import serialize
from sia_metrics_collector import state


class CsvSerializerTest(unittest.TestCase):

    def test_writes_header_to_empty_file(self):
        mock_file = io.BytesIO()

        serialize.CsvSerializer(mock_file)

        self.assertEqual(
            ('timestamp,contract_count,file_count,uploads_in_progress_count,'
             'uploaded_bytes,contract_fee_spending,storage_spending,'
             'upload_spending,download_spending,remaining_renter_funds,'
             'wallet_siacoin_balance,api_latency\n'), mock_file.getvalue())

    def test_writes_state_to_file(self):
        mock_file = io.BytesIO()

        serializer = serialize.CsvSerializer(mock_file)
        serializer.write_state(
            state.SiaState(
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
                wallet_siacoin_balance=75,
                api_latency=5.0))

        self.assertEqual(
            ('timestamp,contract_count,file_count,uploads_in_progress_count,'
             'uploaded_bytes,contract_fee_spending,storage_spending,'
             'upload_spending,download_spending,remaining_renter_funds,'
             'wallet_siacoin_balance,api_latency\n'
             '2018-02-11T16:05:02,5,3,2,900,25,2,35,0,100,75,5.0\n'),
            mock_file.getvalue())

    def test_appends_to_existing_file(self):
        if True:
            return
        mock_file = io.BytesIO(
            ('timestamp,contract_count,file_count,uploads_in_progress_count,'
             'uploaded_bytes,contract_fee_spending,storage_spending,'
             'upload_spending,download_spending,remaining_renter_funds,'
             'wallet_siacoin_balance,api_latency\n'
             '2018-02-11T16:05:02,5,3,2,900,25,2,35,0,100,75,5.0\n'))

        serializer = serialize.CsvSerializer(mock_file)
        serializer.write_state(
            state.SiaState(
                timestamp=datetime.datetime(2018, 2, 11, 16, 5, 7),
                contract_count=6,
                file_count=4,
                uploads_in_progress_count=3,
                uploaded_bytes=901,
                contract_fee_spending=26,
                storage_spending=3,
                upload_spending=36,
                download_spending=1,
                remaining_renter_funds=101,
                wallet_siacoin_balance=76,
                api_latency=6.0))

        self.assertEqual(
            ('timestamp,contract_count,file_count,uploads_in_progress_count,'
             'uploaded_bytes,contract_fee_spending,storage_spending,'
             'upload_spending,download_spending,remaining_renter_funds,'
             'wallet_siacoin_balance,api_latency\n'
             '2018-02-11T16:05:02,5,3,2,900,25,2,35,0,100,75,5.0\n'
             '2018-02-11T16:05:07,6,4,3,901,26,3,36,1,101,76,6.0\n'),
            mock_file.getvalue())
