"""
Beancount to Ledger converter
"""

# SPDX-FileCopyrightText: © 2020 Software in the Public Interest, Inc.

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

from beancount import loader
from beancount.core import display_context
from beancount.core.data import filter_txns
from pkg_resources import DistributionNotFound
from pkg_resources import get_distribution

from .ledger import LedgerPrinter
from .hledger import HLedgerPrinter

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = "undistributed"


def convert(entries, output_format="ledger", dcontext=None, config={}):
    """
    Convert beancount entries to ledger output
    """

    if not dcontext:
        dcontext = display_context.DisplayContext()
        for entry in filter_txns(entries):
            for posting in entry.postings:
                if posting.units is None:
                    continue
                if (posting.meta and '__automatic__' in posting.meta
                        and not '__residual__' in posting.meta):
                    continue
                dcontext.update(posting.units.number, posting.units.currency)

    if output_format == "hledger":
        printer = HLedgerPrinter(dcontext=dcontext, config=config)
    else:
        printer = LedgerPrinter(dcontext=dcontext, config=config)
    return '\n'.join(printer(entry) for entry in entries)


def convert_file(file, output_format="ledger", dcontext=None, config={}):
    """
    Convert beancount file to ledger output
    """

    entries, _, __ = loader.load_file(file)
    return convert(entries, output_format, dcontext=dcontext, config=config)
