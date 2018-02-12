import csv
import logging

logger = logging.getLogger(__name__)

# Constant for Python's file seek() function.
_FROM_FILE_END = 2


class CsvSerializer(object):
    """Serializes SiaState to a CSV file."""

    def __init__(self, csv_file):
        """Creates a serializer, wriiting to the given file.

        Args:
            csv_file: Output file to write CSV to. If file is empty,
                CsvSerializer will write a header row.
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
                'uploaded_bytes',
                'contract_fee_spending',
                'storage_spending',
                'upload_spending',
                'download_spending',
                'remaining_renter_funds',
                'wallet_siacoin_balance',
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
    return {
        'timestamp': state.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
        'contract_count': state.contract_count,
        'file_count': state.file_count,
        'uploads_in_progress_count': state.uploads_in_progress_count,
        'uploaded_bytes': state.uploaded_bytes,
        'contract_fee_spending': state.contract_fee_spending,
        'storage_spending': state.storage_spending,
        'upload_spending': state.upload_spending,
        'download_spending': state.download_spending,
        'remaining_renter_funds': state.remaining_renter_funds,
        'wallet_siacoin_balance': state.wallet_siacoin_balance,
        'api_latency': state.api_latency,
    }


def console_header():
    return ('  time   latency uploaded  contracts    store $  u/l $   d/l $ \n'
            '-------- ------- -------- ------------- -------- ------- -------')


def as_console_string(state):
    try:
        return _make_console_string(state)
    except Exception as e:
        logger.error('Failed to print to console: %s', e.message)
        return ''


def _make_console_string(state):
    return ('{timestamp} {api_latency:5d}ms {uploaded_bytes}'
            ' {contract_fee_spending}/{contract_count}'
            ' {storage_spending} {upload_spending} {download_spending}').format(
                timestamp=state.timestamp.strftime('%H:%M:%S'),
                api_latency=int(state.api_latency),
                uploaded_bytes=_format_bytes(state.uploaded_bytes),
                contract_fee_spending=_format_hastings(
                    state.contract_fee_spending),
                contract_count=_format_contract_count(state.contract_count),
                storage_spending=_format_hastings(state.storage_spending),
                upload_spending=_format_hastings(state.upload_spending),
                download_spending=_format_hastings(state.download_spending))


def _hastings_to_siacoins(hastings):
    if hastings is None:
        return None
    return hastings * pow(10, -24)


def _format_hastings(hastings):
    if not hastings:
        return '  -  '
    sc = _hastings_to_siacoins(hastings)
    unit_pairs = [(10, 'KS'), (1, 'SC'), (-10, 'mS')]
    for magnitude, suffix in unit_pairs:
        if sc > pow(2, magnitude):
            return '%#03.3f%s' % ((float(sc) / pow(2, magnitude)), suffix)
    return '%#03.1fSC' % sc


def _format_contract_count(contract_count):
    if not contract_count:
        return '-  '
    return ('%d' % contract_count).ljust(3)


def _format_bytes(b):
    if not b:
        return '  - '
    unit_pairs = [(40, 'T'), (30, 'G'), (20, 'M'), (10, 'K')]
    for magnitude, suffix in unit_pairs:
        if b > pow(2, magnitude):
            return '%#03.3f%s' % ((float(b) / pow(2, magnitude)), suffix)
    return '%db' % b
