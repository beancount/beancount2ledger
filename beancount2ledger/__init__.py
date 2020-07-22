"""
Beancount to Ledger converter
"""

# SPDX-FileCopyrightText: © 2020 Software in the Public Interest, Inc.

# SPDX-License-Identifier: GPL-2.0-only

__license__ = "GPL-2.0-only"

from beancount import loader

from .ledger import LedgerPrinter, HLedgerPrinter


def convert(entries, output_format="ledger"):
    """
    Convert beancount entries to ledger output
    """

    if output_format == "hledger":
        printer = HLedgerPrinter()
    else:
        printer = LedgerPrinter()
    return '\n'.join(printer(entry) for entry in entries)


def convert_file(file, output_format="ledger"):
    """
    Convert beancount file to ledger output
    """

    entries, _, __ = loader.load_file(file)
    return convert(entries, output_format)
