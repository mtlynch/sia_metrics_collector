import datetime
import unittest

import mock

from sia_metrics_collector import state

_DUMMY_START_TIMESTAMP = datetime.datetime(2018, 2, 12, 18, 5, 55, 0)
_DUMMY_END_TIMESTAMP = datetime.datetime(2018, 2, 12, 18, 5, 55, 207000)


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
        self.assertEqual(a.as_dict(), b.as_dict())

    def test_builds_empty_state_when_all_api_calls_raise_exceptions(self):
        self.mock_sia_api.get_renter_contracts.side_effect = ValueError(
            'dummy get_renter_contracts exception')
        self.mock_sia_api.get_renter_files.side_effect = ValueError(
            'dummy get_renter_files exception')
        self.mock_sia_api.get_wallet.side_effect = ValueError(
            'dummy get_wallet exception')

        self.assertSiaStateEqual(
            state.SiaState(timestamp=_DUMMY_END_TIMESTAMP, api_latency=207.0),
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
            state.SiaState(timestamp=_DUMMY_END_TIMESTAMP, api_latency=207.0),
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
                timestamp=_DUMMY_END_TIMESTAMP,
                contract_count=None,
                file_count=0,
                total_file_bytes=0,
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
            u'activecontracts': [
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
            ],
            u'inactivecontracts': [
                {
                    u'totalcost': u'100000',
                    u'fees': u'5000',
                    u'StorageSpending': u'1000',
                    u'uploadspending': u'400',
                    u'downloadspending': u'30',
                    u'renterfunds': u'1',
                    u'size': 11,
                },
                {
                    u'totalcost': u'250000',
                    u'fees': u'35000',
                    u'StorageSpending': u'2500',
                    u'uploadspending': u'50',
                    u'downloadspending': u'5',
                    u'renterfunds': u'3',
                    u'size': 33,
                },
            ]
        }
        self.mock_sia_api.get_renter_files.return_value = {
            u'files': [
                {
                    u'filesize': 900,
                    u'uploadedbytes': 50,
                    u'uploadprogress': 90,
                },
                {
                    u'filesize': 800,
                    u'uploadedbytes': 100,
                    u'uploadprogress': 100,
                },
                {
                    u'filesize': 100,
                    u'uploadedbytes': 5,
                    u'uploadprogress': 90,
                },
            ],
        }
        self.mock_sia_api.get_wallet.return_value = {
            u'confirmedsiacoinbalance': u'900',
            u'unconfirmedoutgoingsiacoins': u'35',
            u'unconfirmedincomingsiacoins': u'92',
        }

        self.assertSiaStateEqual(
            state.SiaState(
                timestamp=_DUMMY_END_TIMESTAMP,
                contract_count=4,
                file_count=3,
                total_file_bytes=((900 * .9) + (800 * 1.0) + (100 * .9)),
                total_contract_size=143L,
                uploads_in_progress_count=2,
                uploaded_bytes=155,
                total_contract_spending=1050000L,
                contract_fee_spending=120000L,
                upload_spending=1350L,
                download_spending=105L,
                remaining_renter_funds=9L,
                storage_spending=10500L,
                wallet_siacoin_balance=900L,
                wallet_outgoing_siacoins=35L,
                wallet_incoming_siacoins=92L,
                api_latency=207.0), self.builder.build())

    def test_builds_partial_state_when_one_api_call_fails(self):
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'activecontracts': [
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
            ],
            u'inactivecontracts': [
                {
                    u'totalcost': u'100000',
                    u'fees': u'5000',
                    u'StorageSpending': u'1000',
                    u'uploadspending': u'400',
                    u'downloadspending': u'30',
                    u'renterfunds': u'1',
                    u'size': 11,
                },
                {
                    u'totalcost': u'250000',
                    u'fees': u'35000',
                    u'StorageSpending': u'2500',
                    u'uploadspending': u'50',
                    u'downloadspending': u'5',
                    u'renterfunds': u'3',
                    u'size': 33,
                },
            ]
        }
        self.mock_sia_api.get_renter_files.return_value = {
            u'message': u'dummy get_renter_files error'
        }
        self.mock_sia_api.get_wallet.return_value = {
            u'confirmedsiacoinbalance': u'900',
            u'unconfirmedoutgoingsiacoins': u'35',
            u'unconfirmedincomingsiacoins': u'92',
        }

        self.assertSiaStateEqual(
            state.SiaState(
                timestamp=_DUMMY_END_TIMESTAMP,
                contract_count=4,
                total_contract_size=143L,
                file_count=None,
                total_file_bytes=None,
                uploads_in_progress_count=None,
                uploaded_bytes=None,
                total_contract_spending=1050000L,
                contract_fee_spending=120000L,
                upload_spending=1350L,
                download_spending=105L,
                remaining_renter_funds=9L,
                storage_spending=10500L,
                wallet_siacoin_balance=900L,
                wallet_outgoing_siacoins=35L,
                wallet_incoming_siacoins=92L,
                api_latency=207.0), self.builder.build())
