import datetime
import json
import logging

import pysia

logger = logging.getLogger(__name__)


def make_builder():
    """Makes a Builder using production mode defaults."""
    return Builder(pysia.Sia(), datetime.datetime.utcnow)


class SiaState(object):
    """Represents a set of Sia metrics at a moment in time.

    Note that the timestamp is *roughly* the time these metrics were collected.
    It's accurate to within a few seconds, but shouldn't be trusted beyond that,
    as different metrics come from different API calls made sequentially, each
    with a small amount of latency.
    """

    def __init__(self,
                 timestamp=None,
                 contract_count=None,
                 total_contract_size=None,
                 file_count=None,
                 uploads_in_progress_count=None,
                 uploaded_bytes=None,
                 total_contract_spending=None,
                 contract_fee_spending=None,
                 storage_spending=None,
                 upload_spending=None,
                 download_spending=None,
                 remaining_renter_funds=None,
                 wallet_siacoin_balance=None,
                 api_latency=None):
        """Creates a new SiaState instance.

        Args:
            timestamp: Time at which the metrics were collected.
            contract_count: Number of active Sia contracts.
            total_contract_size: Total size of all Sia contracts (this should be
                equal to uploaded_bytes, but the data come from different
                sources).
            file_count: Number of files known to Sia (either partially or
                fully uploaded).
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
            api_latency: Time (in milliseconds) it took for Sia to respond to
                all API calls.
        """
        self.timestamp = timestamp
        self.contract_count = contract_count
        self.total_contract_size = total_contract_size
        self.file_count = file_count
        self.uploads_in_progress_count = uploads_in_progress_count
        self.uploaded_bytes = uploaded_bytes
        self.total_contract_spending = total_contract_spending
        self.contract_fee_spending = contract_fee_spending
        self.storage_spending = storage_spending
        self.upload_spending = upload_spending
        self.download_spending = download_spending
        self.remaining_renter_funds = remaining_renter_funds
        self.wallet_siacoin_balance = wallet_siacoin_balance
        self.api_latency = api_latency

    def __eq__(self, other):
        return (
            (self.timestamp == other.timestamp) and
            (self.contract_count == other.contract_count) and
            (self.total_contract_size == other.total_contract_size) and
            (self.file_count == other.file_count) and
            (self.uploads_in_progress_count == other.uploads_in_progress_count)
            and (self.uploaded_bytes == other.uploaded_bytes) and
            (self.total_contract_spending == other.total_contract_spending) and
            (self.contract_fee_spending == other.contract_fee_spending) and
            (self.storage_spending == other.storage_spending) and
            (self.upload_spending == other.upload_spending) and
            (self.download_spending == other.download_spending) and
            (self.remaining_renter_funds == other.remaining_renter_funds) and
            (self.wallet_siacoin_balance == other.wallet_siacoin_balance) and
            (self.api_latency == other.api_latency))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return json.dumps({
            'timestamp':
            self.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            'contract_count':
            self.contract_count,
            'total_contract_size':
            self.total_contract_size,
            'file_count':
            self.file_count,
            'uploads_in_progress_count':
            self.uploads_in_progress_count,
            'uploaded_bytes':
            self.uploaded_bytes,
            'total_contract_spending':
            self.total_contract_spending,
            'contract_fee_spending':
            self.contract_fee_spending,
            'storage_spending':
            self.storage_spending,
            'upload_spending':
            self.upload_spending,
            'download_spending':
            self.download_spending,
            'remaining_renter_funds':
            self.remaining_renter_funds,
            'wallet_siacoin_balance':
            self.wallet_siacoin_balance,
            'api_latency':
            self.api_latency,
        })


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
        if not response or not response.has_key(u'contracts'):
            logger.error('Failed to query contracts information: %s',
                         json.dumps(response))
            return
        contracts = response[u'contracts']
        state.contract_count = len(contracts)
        state.total_contract_size = 0
        state.total_contract_spending = 0
        state.contract_fee_spending = 0
        state.storage_spending = 0
        state.upload_spending = 0
        state.download_spending = 0
        state.remaining_renter_funds = 0
        for contract in contracts:
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
        state.file_count = len(files)
        state.uploaded_bytes = 0
        state.uploads_in_progress_count = 0
        for f in files:
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
