"""
Convert Beancount entries to hledger
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais

# SPDX-License-Identifier: GPL-2.0-only

__license__ = "GPL-2.0-only"

from beancount.core.amount import Amount
from beancount.core import position
from beancount.core import interpolate

from .common import ROUNDING_ACCOUNT
from .common import quote_currency
from .ledger import LedgerPrinter


class HLedgerPrinter(LedgerPrinter):
    "Multi-method for printing directives in HLedger format."

    def Transaction(self, entry, oss):
        strings = []

        # Insert a posting to absorb the residual if necessary. This is
        # sometimes needed because Ledger bases its balancing precision on the
        # *last* number of digits used on that currency. This is believed to be
        # a bug, so instead, we simply insert a rounding account to absorb the
        # residual and precisely balance the transaction.
        entry = interpolate.fill_residual_posting(entry, ROUNDING_ACCOUNT)

        # Compute the string for the payee and narration line.
        if entry.payee:
            strings.append('{} |'.format(entry.payee))
        if entry.narration:
            strings.append(entry.narration)

        oss.write('{e.date:%Y-%m-%d} {flag} {}\n'.format(' '.join(strings),
                                                         flag=entry.flag or '',
                                                         e=entry))

        if entry.tags:
            oss.write('  ; {}:\n'.format(':, '.join(sorted(entry.tags))))
        if entry.links:
            oss.write('  ; Link: {}\n'.format(' '.join(sorted(entry.links))))

        for posting in entry.postings:
            self.Posting(posting, entry, oss)

    def Posting(self, posting, entry, oss):
        flag = '{} '.format(posting.flag) if posting.flag else ''
        assert posting.account is not None

        flag_posting = '{:}{:62}'.format(flag, posting.account)

        pos_str = (position.to_string(posting, self.dformat, detail=False)
                   if isinstance(posting.units, Amount)
                   else '')
        if pos_str:
            # Convert the cost as a price entry, that's what HLedger appears to want.
            pos_str = pos_str.replace('{', '@ ').replace('}', '')

        price_str = ('@ {}'.format(posting.price.to_string(self.dformat_max))
                     if posting.price is not None
                     else '')

        posting_str = '  {:64} {:>16} {:>16}'.format(flag_posting,
                                                     quote_currency(pos_str),
                                                     quote_currency(price_str))
        oss.write(posting_str.rstrip())

        oss.write('\n')

    def Open(_, entry, oss):
        # Not supported by HLedger AFAIK.
        oss.write(';; Open: {e.date:%Y-%m-%d} close {e.account}\n'.format(e=entry))
