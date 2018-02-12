import datetime
import unittest

import mock

from sia_metrics_collector import state

_DUMMY_START_TIMESTAMP = datetime.datetime(2018, 2, 12, 18, 5, 55, 0)
_DUMMY_END_TIMESTAMP = datetime.datetime(2018, 2, 12, 18, 5, 55, 207000)


class SiaStateTest(unittest.TestCase):

    def test_equality(self):
        a = state.SiaState(
            timestamp=datetime.datetime(2018, 2, 11, 16, 5, 2),
            contract_count=5,
            total_contract_size=5000,
            file_count=3,
            uploads_in_progress_count=2,
            uploaded_bytes=900,
            total_contract_spending=10000,
            contract_fee_spending=25,
            storage_spending=2,
            upload_spending=35,
            download_spending=0,
            remaining_renter_funds=100,
            wallet_siacoin_balance=75,
            api_latency=5.0)
        a_copy = state.SiaState(
            timestamp=datetime.datetime(2018, 2, 11, 16, 5, 2),
            contract_count=5,
            total_contract_size=5000,
            file_count=3,
            uploads_in_progress_count=2,
            uploaded_bytes=900,
            total_contract_spending=10000,
            contract_fee_spending=25,
            storage_spending=2,
            upload_spending=35,
            download_spending=0,
            remaining_renter_funds=100,
            wallet_siacoin_balance=75,
            api_latency=5.0)
        b = state.SiaState(
            timestamp=datetime.datetime(2017, 10, 15, 12, 15, 56),
            contract_count=1,
            total_contract_size=4000,
            file_count=9,
            uploads_in_progress_count=1,
            uploaded_bytes=1800,
            total_contract_spending=70000,
            contract_fee_spending=22,
            storage_spending=18,
            upload_spending=9,
            download_spending=2,
            remaining_renter_funds=105,
            wallet_siacoin_balance=85,
            api_latency=85.0)
        self.assertEqual(a, a_copy)
        self.assertNotEqual(a, b)


class StateBuilderTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.mock_sia_api = mock.Mock()
        self.times = [_DUMMY_START_TIMESTAMP, _DUMMY_END_TIMESTAMP]

        def mock_time_fn():
            timestamp = self.times[0]
            if len(self.times) > 1:
                self.times.pop(0)
            return timestamp

        self.mock_time_fn = mock_time_fn
        self.builder = state.Builder(self.mock_sia_api, self.mock_time_fn)

    def assertSiaStateEqual(self, a, b):
        self.assertEqual(
            {
                'timestamp': a.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                'contract_count': a.contract_count,
                'file_count': a.file_count,
                'uploads_in_progress_count': a.uploads_in_progress_count,
                'uploaded_bytes': a.uploaded_bytes,
                'contract_fee_spending': a.contract_fee_spending,
                'upload_spending': a.upload_spending,
                'download_spending': a.download_spending,
                'storage_spending': a.storage_spending,
                'remaining_renter_funds': a.remaining_renter_funds,
                'wallet_siacoin_balance': a.wallet_siacoin_balance,
                'api_latency': a.api_latency,
            }, {
                'timestamp': b.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                'contract_count': b.contract_count,
                'file_count': b.file_count,
                'uploads_in_progress_count': b.uploads_in_progress_count,
                'uploaded_bytes': b.uploaded_bytes,
                'contract_fee_spending': b.contract_fee_spending,
                'upload_spending': b.upload_spending,
                'download_spending': b.download_spending,
                'storage_spending': b.storage_spending,
                'remaining_renter_funds': b.remaining_renter_funds,
                'wallet_siacoin_balance': b.wallet_siacoin_balance,
                'api_latency': b.api_latency,
            })

    def test_builds_empty_state_when_all_api_calls_raise_exceptions(self):
        self.mock_sia_api.get_renter_contracts.side_effect = ValueError(
            'dummy get_renter_contracts exception')
        self.mock_sia_api.get_renter_files.side_effect = ValueError(
            'dummy get_renter_files exception')
        self.mock_sia_api.get_wallet.side_effect = ValueError(
            'dummy get_wallet exception')

        self.assertSiaStateEqual(
            state.SiaState(timestamp=_DUMMY_START_TIMESTAMP, api_latency=207.0),
            self.builder.build())

    def test_builds_empty_state_when_all_api_calls_return_errors(self):
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'message': u'dummy get_renter_contracts error'
        }
        self.mock_sia_api.get_renter_files.return_value = {
            u'message': u'dummy get_renter_files error'
        }
        self.mock_sia_api.get_wallet.return_value = {
            u'message': u'dummy get_wallet error'
        }

        self.assertSiaStateEqual(
            state.SiaState(timestamp=_DUMMY_START_TIMESTAMP, api_latency=207.0),
            self.builder.build())

    def test_builds_zero_metrics_when_files_is_None(self):
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'message': u'dummy get_renter_contracts error'
        }
        # 'files' is set to None when there are zero files.
        self.mock_sia_api.get_renter_files.return_value = {u'files': None}
        self.mock_sia_api.get_wallet.return_value = {
            u'message': u'dummy get_wallet error'
        }

        self.assertSiaStateEqual(
            state.SiaState(
                timestamp=_DUMMY_START_TIMESTAMP,
                contract_count=None,
                file_count=0,
                total_contract_size=None,
                uploads_in_progress_count=0,
                uploaded_bytes=0,
                total_contract_spending=None,
                contract_fee_spending=None,
                upload_spending=None,
                download_spending=None,
                remaining_renter_funds=None,
                storage_spending=None,
                wallet_siacoin_balance=None,
                api_latency=207.0), self.builder.build())

    def test_builds_full_state_when_all_api_calls_return_successfully(self):
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'contracts': [
                {
                    u'totalcost': u'200000',
                    u'fees': u'10000',
                    u'StorageSpending': u'2000',
                    u'uploadspending': u'800',
                    u'downloadspending': u'60',
                    u'renterfunds': u'3',
                    u'size': 22,
                },
                {
                    u'totalcost': u'500000',
                    u'fees': u'70000',
                    u'StorageSpending': u'5000',
                    u'uploadspending': u'100',
                    u'downloadspending': u'10',
                    u'renterfunds': u'2',
                    u'size': 77,
                },
            ]
        }
        self.mock_sia_api.get_renter_files.return_value = {
            u'files': [
                {
                    u'uploadedbytes': 50,
                    u'uploadprogress': 90,
                },
                {
                    u'uploadedbytes': 100,
                    u'uploadprogress': 100,
                },
                {
                    u'uploadedbytes': 5,
                    u'uploadprogress': 90,
                },
            ],
        }
        self.mock_sia_api.get_wallet.return_value = {
            u'confirmedsiacoinbalance': u'900',
        }

        self.assertSiaStateEqual(
            state.SiaState(
                timestamp=_DUMMY_START_TIMESTAMP,
                contract_count=2,
                file_count=3,
                total_contract_size=99,
                uploads_in_progress_count=2,
                uploaded_bytes=155,
                total_contract_spending=700000L,
                contract_fee_spending=80000L,
                upload_spending=900L,
                download_spending=70L,
                remaining_renter_funds=5L,
                storage_spending=7000L,
                wallet_siacoin_balance=900L,
                api_latency=207.0), self.builder.build())

    def test_builds_partial_state_when_one_api_call_fails(self):
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'contracts': [
                {
                    u'totalcost': u'200000',
                    u'fees': u'10000',
                    u'StorageSpending': u'2000',
                    u'uploadspending': u'800',
                    u'downloadspending': u'60',
                    u'renterfunds': u'3',
                    u'size': 22,
                },
                {
                    u'totalcost': u'500000',
                    u'fees': u'70000',
                    u'StorageSpending': u'5000',
                    u'uploadspending': u'100',
                    u'downloadspending': u'10',
                    u'renterfunds': u'2',
                    u'size': 77,
                },
            ]
        }
        self.mock_sia_api.get_renter_files.return_value = {
            u'message': u'dummy get_renter_files error'
        }
        self.mock_sia_api.get_wallet.return_value = {
            u'confirmedsiacoinbalance': u'900',
        }

        self.assertSiaStateEqual(
            state.SiaState(
                timestamp=_DUMMY_START_TIMESTAMP,
                contract_count=2,
                total_contract_size=99,
                file_count=None,
                uploads_in_progress_count=None,
                uploaded_bytes=None,
                total_contract_spending=700000L,
                contract_fee_spending=80000L,
                upload_spending=900L,
                download_spending=70L,
                remaining_renter_funds=5L,
                storage_spending=7000L,
                wallet_siacoin_balance=900L,
                api_latency=207.0), self.builder.build())
