"""
Beancount to Ledger converter
"""

# SPDX-FileCopyrightText: © 2020 Software in the Public Interest, Inc.
# SPDX-FileCopyrightText: © 2020 Martin Michlmayr <tbm@cyrius.com>

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import argparse
import sys

import beancount2ledger


def cli():
    """
    Main function for CLI access.
    """

    if "hledger" in sys.argv[0]:
        default = "hledger"
    else:
        default = "ledger"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-f',
        "--format",
        dest="format",
        action="store",
        choices=("ledger", "hledger"),
        default=default,
        help=f"output format (default: {default})")
    parser.add_argument(
        'file', help='beancount file', type=argparse.FileType('r'))
    parser.add_argument(
        '-V',
        "--version",
        action="version",
        version=f"%(prog)s {beancount2ledger.__version__}")
    args = parser.parse_args()

    print(beancount2ledger.convert_file(args.file.name, args.format))


if __name__ == "__main__":
    cli()
