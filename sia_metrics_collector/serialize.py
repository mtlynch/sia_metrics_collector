import csv

# Constant for Python's file seek() function.
_FROM_FILE_END = 2


class CsvSerializer(object):
    """Serializes SiaState to a CSV file."""

    def __init__(self, csv_file):
        """Creates a serializer, wriiting to the given file.

        Args:
            csv_file: Output file to write CSV to. If file is empty,
                CsvSerializer will write a header row. Caller must open the file
                in either 'w' or 'r+' mode, as 'a' will not let us detect
                whether to write a header on Windows.
        """
        _seek_to_end_of_file(csv_file)
        is_empty_file = _is_empty_file(csv_file)
        self._csv_file = csv_file
        self._csv_writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                'timestamp',
                'contract_count',
                'file_count',
                'uploads_in_progress_count',
                'total_contract_size',
                'total_file_bytes',
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
            lineterminator='\n')
        if is_empty_file:
            self._csv_writer.writeheader()

    def write_state(self, state):
        self._csv_writer.writerow(_state_to_dict(state))
        self._csv_file.flush()


def _seek_to_end_of_file(file_handle):
    file_handle.seek(0, _FROM_FILE_END)


def _is_empty_file(file_handle):
    return file_handle.tell() == 0


def _state_to_dict(state):
    d = state.as_dict()
    d['timestamp'] = state.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
    return d
