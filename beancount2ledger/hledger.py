"""
Convert Beancount entries to hledger
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import datetime

from beancount.core.amount import Amount
from beancount.core import position
from beancount.core import interpolate

from .common import ROUNDING_ACCOUNT
from .common import ledger_flag, ledger_str, quote_currency, user_meta
from .ledger import LedgerPrinter


class HLedgerPrinter(LedgerPrinter):
    "Multi-method for printing directives in HLedger format."

    def format_meta(self, key, val):
        """"
        Format metadata
        """

        if val is None:
            return f"{key}:"
        return f"{key}: {val}"


    def Transaction(self, entry):
        # Insert a posting to absorb the residual if necessary. This is
        # sometimes needed because Ledger bases its balancing precision on the
        # *last* number of digits used on that currency. This is believed to be
        # a bug, so instead, we simply insert a rounding account to absorb the
        # residual and precisely balance the transaction.
        entry = interpolate.fill_residual_posting(entry, ROUNDING_ACCOUNT)

        # Compute the string for the payee and narration line.
        strings = []
        if entry.payee:
            strings.append(f"{ledger_str(entry.payee)} |")
        if entry.narration:
            strings.append(ledger_str(entry.narration))

        meta = user_meta(entry.meta or {})
        self.io.write(f"{entry.date:%Y-%m-%d}")
        auxdate_key = self.config.get("auxdate")
        if auxdate_key and isinstance(meta.get(auxdate_key), datetime.date):
            self.io.write(f"={meta[auxdate_key]:%Y-%m-%d}")
            del meta[auxdate_key]
        flag = ledger_flag(entry.flag)
        if flag:
            self.io.write(' ' + flag)
        payee = ' '.join(strings)
        if payee:
            self.io.write(' ' + payee)
        self.io.write('\n')

        indent = ' ' * self.config["indent"]

        if entry.tags:
            self.io.write(indent +
                          '; {}:\n'.format(':, '.join(sorted(entry.tags))))
        if entry.links:
            self.io.write(indent +
                          '; Link: {}\n'.format(' '.join(sorted(entry.links))))

        for key, val in meta.items():
            meta = self.format_meta(key, val)
            if meta:
                self.io.write(indent + f'; {meta}\n')

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
            posting_str = f'{flag_posting}'
        else:
            # Width we have available for the amount: take width of
            # flag_posting add config["indent"] for the indentation
            # of postings and add 2 to separate account from amount
            len_amount = max(0, 76 - (len(flag_posting) + 2 + 2))
            posting_str = f'{flag_posting}  {quote_currency(pos_str):>{len_amount}} {quote_currency(price_str)}'
        indent = ' ' * self.config["indent"]
        self.io.write(indent + posting_str.rstrip())
        self.io.write('\n')

        meta = user_meta(posting.meta or {})
        postdate_key = self.config.get("postdate")
        if postdate_key and isinstance(meta.get(postdate_key), datetime.date):
            postdate = meta[postdate_key]
            del meta[postdate_key]
            meta["date"] = postdate
        auxdate_key = self.config.get("auxdate")
        if auxdate_key and isinstance(meta.get(auxdate_key), datetime.date):
            auxdate = meta[auxdate_key]
            del meta[auxdate_key]
            meta["date2"] = auxdate

        for key, val in meta.items():
            formatted_meta = self.format_meta(key, val)
            if meta:
                self.io.write(2 * indent + f'; {formatted_meta}\n')
