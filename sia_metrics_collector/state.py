import recordtype
import datetime
import json
import logging

import pysia

logger = logging.getLogger(__name__)


def make_builder(sia_hostname, sia_port):
    """Makes a Builder using production mode defaults."""
    return Builder(pysia.Sia(sia_hostname, sia_port), datetime.datetime.utcnow)


"""Represents a set of Sia metrics at a moment in time.

Note that the timestamp is *roughly* the time these metrics were collected.
It's accurate to within a few seconds, but shouldn't be trusted beyond that,
as different metrics come from different API calls made sequentially, each
with a small amount of latency.

Fields:
    timestamp: Time at which the metrics were collected.
    contract_count: Number of active Sia contracts.
    total_contract_size: Total size of all Sia contracts (this should be
        equal to uploaded_bytes, but the data come from different
        sources).
    file_count: Number of files known to Sia (either partially or
        fully uploaded).
    total_file_bytes: Total size of all files files known to Sia. Not
        all bytes have necessarily been uploaded to Sia yet.
    uploads_in_progress_count: Number of uploads currently in progress.
    uploaded_bytes: Total number of bytes that have been uploaded
        across all files.
    total_contract_spending: Total amount of money (in hastings) spent
        on storage contracts.
    contract_fee_spending: Total amount of money (in hastings) spent on
        contract fees.
    storage_spending: Total amount of money (in hastings) spent on
        storage.
    upload_spending: Total amount of money (in hastings) spent on upload
        bandwidth.
    download_spending: Total amount of money (in hastings) spent on
        download bandwidth.
    wallet_siacoin_balance: Current wallet balance of Siacoins (in
        hastings).
    wallet_outgoing_siacoins: Unconfirmed outgoing Siacoins (in hastings).
    wallet_incoming_siacoins: Unconfirmed incoming Siacoins (in hastings).
    api_latency: Time (in milliseconds) it took for Sia to respond to
        all API calls.
"""
SiaState = recordtype.recordtype(
    'SiaState', [
        'timestamp',
        'contract_count',
        'total_contract_size',
        'file_count',
        'total_file_bytes',
        'uploads_in_progress_count',
        'uploaded_bytes',
        'total_contract_spending',
        'contract_fee_spending',
        'storage_spending',
        'upload_spending',
        'download_spending',
        'remaining_renter_funds',
        'wallet_siacoin_balance',
        'wallet_outgoing_siacoins',
        'wallet_incoming_siacoins',
        'api_latency',
    ],
    default=None)
SiaState.as_dict = SiaState._asdict


class Builder(object):
    """Builds a SiaState object by querying the Sia API."""

    def __init__(self, sia_api, time_fn):
        """Creates a new Builder instance.

        Args:
            sia_api: An implementation of the Sia client API.
            time_fn: A function that returns the current time.
        """
        self._sia_api = sia_api
        self._time_fn = time_fn

    def build(self):
        """Builds a SiaState object representing the current state of Sia."""
        state = SiaState()
        queries_start_time = self._time_fn()
        state_population_fns = (self._populate_contract_metrics,
                                self._populate_file_metrics,
                                self._populate_wallet_metrics,
                                self._populate_timestamp)
        for fn in state_population_fns:
            try:
                fn(state)
            except Exception as e:
                logging.error('Error when calling %s: %s', fn.__name__,
                              e.message)
                continue
        state.api_latency = (
            self._time_fn() - queries_start_time).total_seconds() * 1000.0
        return state

    def _populate_timestamp(self, state):
        state.timestamp = self._time_fn()

    def _populate_contract_metrics(self, state):
        response = self._sia_api.get_renter_contracts()
        if not response or not response.has_key(u'activecontracts'):
            logger.error("response.has_key(u'activecontracts'): %s",
                         json.dumps(response.has_key(u'activecontracts')))
            logger.error('Failed to query contracts information: %s',
                         json.dumps(response))
            return
        active_contracts = response[u'activecontracts']
        inactive_contracts = response[u'inactivecontracts']
        state.contract_count = len(active_contracts) + len(inactive_contracts)
        state.total_contract_size = 0
        state.total_contract_spending = 0
        state.contract_fee_spending = 0
        state.storage_spending = 0
        state.upload_spending = 0
        state.download_spending = 0
        state.remaining_renter_funds = 0
        for contract in (active_contracts + inactive_contracts):
            state.total_contract_size += long(contract[u'size'])
            state.total_contract_spending += long(contract[u'totalcost'])
            state.contract_fee_spending += long(contract[u'fees'])
            state.storage_spending += long(contract[u'StorageSpending'])
            state.upload_spending += long(contract[u'uploadspending'])
            state.download_spending += long(contract[u'downloadspending'])
            state.remaining_renter_funds += long(contract[u'renterfunds'])

    def _populate_file_metrics(self, state):
        response = self._sia_api.get_renter_files()
        if not response or not response.has_key(u'files'):
            logger.error('Failed to query file information: %s',
                         json.dumps(response))
            return
        files = response[u'files']
        state.file_count = 0
        state.total_file_bytes = 0
        state.uploaded_bytes = 0
        state.uploads_in_progress_count = 0
        if not files:
            return
        for f in files:
            state.file_count += 1
            state.total_file_bytes += long(f[u'filesize']) * (
                f[u'uploadprogress'] / 100.0)
            state.uploaded_bytes += f[u'uploadedbytes']
            if f[u'uploadprogress'] < 100:
                state.uploads_in_progress_count += 1

    def _populate_wallet_metrics(self, state):
        response = self._sia_api.get_wallet()
        if not response or not response.has_key(u'confirmedsiacoinbalance'):
            logger.error('Failed to query wallet information: %s',
                         json.dumps(response))
            return
        state.wallet_siacoin_balance = long(
            response[u'confirmedsiacoinbalance'])
        state.wallet_outgoing_siacoins = long(
            response[u'unconfirmedoutgoingsiacoins'])
        state.wallet_incoming_siacoins = long(
            response[u'unconfirmedincomingsiacoins'])
