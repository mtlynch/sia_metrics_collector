import datetime
import unittest

import mock

from sia_metrics_collector import state

_DUMMY_TIMESTAMP = datetime.datetime(2018, 2, 12, 18, 5, 55)


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


class StateBuilderTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_api = mock.Mock()
        self.mock_time_fn = lambda: _DUMMY_TIMESTAMP
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
            })

    def test_builds_empty_state_when_all_api_calls_raise_exceptions(self):
        self.mock_sia_api.get_renter_contracts.side_effect = ValueError(
            'dummy get_renter_contracts exception')
        self.mock_sia_api.get_renter_files.side_effect = ValueError(
            'dummy get_renter_files exception')
        self.mock_sia_api.get_wallet.side_effect = ValueError(
            'dummy get_wallet exception')

        self.assertSiaStateEqual(
            state.SiaState(timestamp=_DUMMY_TIMESTAMP), self.builder.build())

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
            state.SiaState(timestamp=_DUMMY_TIMESTAMP), self.builder.build())

    def test_builds_full_state_when_all_api_calls_return_successfully(self):
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'contracts': [
                {
                    u'fees': u'10000',
                    u'StorageSpending': u'2000',
                    u'uploadspending': u'800',
                    u'downloadspending': u'60',
                    u'renterfunds': u'3',
                },
                {
                    u'fees': u'70000',
                    u'StorageSpending': u'5000',
                    u'uploadspending': u'100',
                    u'downloadspending': u'10',
                    u'renterfunds': u'2',
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
                timestamp=_DUMMY_TIMESTAMP,
                contract_count=2,
                file_count=3,
                uploads_in_progress_count=2,
                uploaded_bytes=155,
                contract_fee_spending=80000L,
                upload_spending=900L,
                download_spending=70L,
                remaining_renter_funds=5L,
                storage_spending=7000L,
                wallet_siacoin_balance=900L), self.builder.build())

    def test_builds_partial_state_when_one_api_call_fails(self):
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'contracts': [
                {
                    u'fees': u'10000',
                    u'StorageSpending': u'2000',
                    u'uploadspending': u'800',
                    u'downloadspending': u'60',
                    u'renterfunds': u'3',
                },
                {
                    u'fees': u'70000',
                    u'StorageSpending': u'5000',
                    u'uploadspending': u'100',
                    u'downloadspending': u'10',
                    u'renterfunds': u'2',
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
                timestamp=_DUMMY_TIMESTAMP,
                contract_count=2,
                file_count=None,
                uploads_in_progress_count=None,
                uploaded_bytes=None,
                contract_fee_spending=80000L,
                upload_spending=900L,
                download_spending=70L,
                remaining_renter_funds=5L,
                storage_spending=7000L,
                wallet_siacoin_balance=900L), self.builder.build())
