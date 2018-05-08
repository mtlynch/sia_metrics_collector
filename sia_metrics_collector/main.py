#!/usr/bin/python2

import argparse
import datetime
import logging
import os
import time

import cli
import serialize
import state

logger = logging.getLogger(__name__)


def configure_logging():
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-15s %(levelname)-4s %(message)s',
        '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def main(args):
    configure_logging()
    logger.info('Started runnning')
    with _open_output_file(args.output_file) as csv_file:
        _poll_forever(args.hostname, args.sia_port, args.poll_frequency,
                      csv_file)


def _open_output_file(output_path):
    """Opens the output file and seeks to the end.

    CsvWriter needs the mode to either be 'r+' or 'w'.

    Args:
        output_path: Path to output file to open or create.
    """
    if os.path.exists(output_path):
        return open(output_path, 'r+')
    else:
        return open(output_path, 'w')


def _poll_forever(sia_hostname, sia_port, frequency, csv_file):
    builder = state.make_builder()
    csv_serializer = serialize.CsvSerializer(csv_file)
    next_poll_time = datetime.datetime.utcnow()
    for i in xrange(1000000000):
        s = builder.build()

        csv_serializer.write_state(s)
        # Print header every 100 lines.
        if i % 100 == 0:
            cli.print_header()
        cli.print_state(s)
        next_poll_time += datetime.timedelta(seconds=frequency)
        _wait_until(next_poll_time)


def _wait_until(timestamp):
    while datetime.datetime.utcnow() < timestamp:
        time.sleep(0.5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Sia Metrics Collector',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-h',
        '--hostname',
        default='http://localhost',
        help='Hostname of Sia node to poll for metrics')
    parser.add_argument(
        '-p',
        '--port',
        type=int,
        default=9980,
        help='Siad API port of Sia node to poll for metrics')
    parser.add_argument(
        '-f',
        '--poll_frequency',
        type=int,
        default=60,
        help='Frequency (in seconds) to poll metrics')
    parser.add_argument(
        '-o',
        '--output_file',
        required=True,
        help='Path to file to write metrics')
    main(parser.parse_args())
