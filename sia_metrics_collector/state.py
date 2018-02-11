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
                 file_count=None,
                 uploads_in_progress_count=None,
                 uploaded_bytes=None,
                 contract_fee_spending=None,
                 storage_spending=None,
                 upload_spending=None,
                 download_spending=None,
                 remaining_renter_funds=None,
                 wallet_siacoin_balance=None):
        """Creates a new SiaState instance.

        Args:
            timestamp: Time at which the metrics were collected.
            contract_count: Number of active Sia contracts.
            file_count: Number of files known to Sia (either partially or
                fully uploaded).
            uploads_in_progress_count: Number of uploads currently in progress.
            uploaded_bytes: Total number of bytes that have been uploaded
                across all files.
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
        """
        self.timestamp = timestamp
        self.contract_count = contract_count
        self.file_count = file_count
        self.uploads_in_progress_count = uploads_in_progress_count
        self.uploaded_bytes = uploaded_bytes
        self.contract_fee_spending = contract_fee_spending
        self.storage_spending = storage_spending
        self.upload_spending = upload_spending
        self.download_spending = download_spending
        self.remaining_renter_funds = remaining_renter_funds
        self.wallet_siacoin_balance = wallet_siacoin_balance

    def __eq__(self, other):
        return (
            (self.timestamp == other.timestamp) and
            (self.contract_count == other.contract_count) and
            (self.file_count == other.file_count) and
            (self.uploads_in_progress_count == other.uploads_in_progress_count)
            and (self.uploaded_bytes == other.uploaded_bytes) and
            (self.contract_fee_spending == other.contract_fee_spending) and
            (self.storage_spending == other.storage_spending) and
            (self.upload_spending == other.upload_spending) and
            (self.download_spending == other.download_spending) and
            (self.remaining_renter_funds == other.remaining_renter_funds) and
            (self.wallet_siacoin_balance == other.wallet_siacoin_balance))

    def __ne__(self, other):
        return not self.__eq__(other)
