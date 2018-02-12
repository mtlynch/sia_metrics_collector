#!/usr/bin/python2

import argparse
import datetime
import logging
import time

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
    with open(args.output_file, 'r+') as csv_file:
        _poll_forever(args.poll_frequency, csv_file)


def _poll_forever(frequency, csv_file):
    builder = state.make_builder()
    csv_serializer = serialize.CsvSerializer(csv_file)
    for i in range(100000000000000):
        poll_start = datetime.datetime.utcnow()
        s = builder.build()

        csv_serializer.write_state(s)
        # Print header every 100 lines.
        if i % 100 == 0:
            print serialize.console_header()
        print serialize.as_console_string(s)
        _wait_until(poll_start + datetime.timedelta(seconds=frequency))


def _wait_until(timestamp):
    while datetime.datetime.utcnow() < timestamp:
        time.sleep(0.5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Sia Metrics Collector',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-f',
        '--poll_frequency',
        type=int,
        default=60,
        help='Frequency (in seconds) to poll metrics')
    parser.add_argument(
        '-o', '--output_file', help='Path to file to write metrics')
    main(parser.parse_args())
