"""
Convert Beancount entries to hledger
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

from beancount.core.amount import Amount
from beancount.core import position
from beancount.core import interpolate

from .common import ROUNDING_ACCOUNT
from .common import ledger_flag, ledger_str, quote_currency
from .ledger import LedgerPrinter


class HLedgerPrinter(LedgerPrinter):
    "Multi-method for printing directives in HLedger format."

    def Transaction(self, entry):
        strings = []

        # Insert a posting to absorb the residual if necessary. This is
        # sometimes needed because Ledger bases its balancing precision on the
        # *last* number of digits used on that currency. This is believed to be
        # a bug, so instead, we simply insert a rounding account to absorb the
        # residual and precisely balance the transaction.
        entry = interpolate.fill_residual_posting(entry, ROUNDING_ACCOUNT)

        # Compute the string for the payee and narration line.
        if entry.payee:
            strings.append(f"{ledger_str(entry.payee)} |")
        if entry.narration:
            strings.append(ledger_str(entry.narration))

        flag = f"{ledger_flag(entry.flag)} " if ledger_flag(entry.flag) else ''
        self.io.write('{e.date:%Y-%m-%d} {flag}{}\n'.format(
            ' '.join(strings), flag=flag or '', e=entry))

        if entry.tags:
            self.io.write('  ; {}:\n'.format(':, '.join(sorted(entry.tags))))
        if entry.links:
            self.io.write('  ; Link: {}\n'.format(' '.join(
                sorted(entry.links))))

        for posting in entry.postings:
            self.Posting(posting, entry)

    def Posting(self, posting, entry):
        assert posting.account is not None
        flag = f"{ledger_flag(posting.flag)} " if ledger_flag(
            posting.flag) else ''
        flag_posting = f"{flag}{posting.account}"

        pos_str = (position.to_string(posting, self.dformat, detail=False)
                   if isinstance(posting.units, Amount) else '')
        if pos_str:
            # Convert the cost as a price entry, that's what HLedger appears to want.
            pos_str = pos_str.replace('{', '@ ').replace('}', '')

        price_str = ('@ {}'.format(posting.price.to_string(self.dformat_max))
                     if posting.price is not None and posting.cost is None else
                     '')
        if posting.meta and '__automatic__' in posting.meta and not '__residual__' in posting.meta:
            posting_str = f'  {flag_posting}'
        else:
            # Width we have available for the amount: take width of
            # flag_posting add 2 for the indentation of postings and
            # add 2 to separate account from amount
            len_amount = max(0, 76 - (len(flag_posting) + 2 + 2))
            posting_str = f'  {flag_posting}  {quote_currency(pos_str):>{len_amount}} {quote_currency(price_str)}'
        self.io.write(posting_str.rstrip())

        self.io.write('\n')
