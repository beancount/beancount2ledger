"""
Convert Beancount entries to hledger
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais

# SPDX-License-Identifier: GPL-2.0-only

__license__ = "GPL-2.0-only"

import io

from beancount.core.amount import Amount
from beancount.core import position
from beancount.core import amount
from beancount.core import interpolate
from beancount.core import display_context

from .common import ROUNDING_ACCOUNT
from .common import quote_currency, postings_by_type


class LedgerPrinter:
    "Multi-method for printing directives in Ledger format."

    # pylint: disable=invalid-name

    def __init__(self, dcontext=None):
        self.dcontext = dcontext or display_context.DEFAULT_DISPLAY_CONTEXT
        self.dformat = self.dcontext.build(precision=display_context.Precision.MOST_COMMON)
        self.dformat_max = self.dcontext.build(precision=display_context.Precision.MAXIMUM)

    def __call__(self, obj):
        oss = io.StringIO()
        method = getattr(self, obj.__class__.__name__)
        method(obj, oss)
        return oss.getvalue()

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
            oss.write('  ; :{}:\n'.format(':'.join(sorted(entry.tags))))
        if entry.links:
            oss.write('  ; Link: {}\n'.format(', '.join(sorted(entry.links))))

        for posting in entry.postings:
            self.Posting(posting, entry, oss)

    def Posting(self, posting, entry, oss):
        flag = '{} '.format(posting.flag) if posting.flag else ''
        assert posting.account is not None

        flag_posting = '{:}{:62}'.format(flag, posting.account)

        pos_str = (position.to_string(posting, self.dformat, detail=False)
                   if isinstance(posting.units, Amount)
                   else '')

        if posting.price is not None:
            price_str = '@ {}'.format(posting.price.to_string(self.dformat_max))
        else:
            # Figure out if we need to insert a price on a posting held at cost.
            # See https://groups.google.com/d/msg/ledger-cli/35hA0Dvhom0/WX8gY_5kHy0J
            (postings_simple,
             postings_at_price,
             postings_at_cost) = postings_by_type(entry)

            cost = posting.cost
            if postings_at_price and postings_at_cost and cost:
                price_str = '@ {}'.format(
                    amount.Amount(cost.number,
                                  cost.currency).to_string(self.dformat))
            else:
                price_str = ''

        posting_str = '  {:64} {} {}'.format(flag_posting,
                                             quote_currency(pos_str),
                                             quote_currency(price_str))
        oss.write(posting_str.rstrip())

        oss.write('\n')

    def Balance(_, entry, oss):
        # We cannot output balance directive equivalents because Ledger only
        # supports file assertions and not dated assertions. See "Balance
        # Assertions for Beancount" for details:
        # https://docs.google.com/document/d/1vyemZFox47IZjuBrT2RjhSHZyTgloYOUeJb73RxMRD0/
        pass

    def Note(_, entry, oss):
        oss.write(';; Note: {e.date:%Y-%m-%d} {e.account} {e.comment}\n'.format(e=entry))

    def Document(_, entry, oss):
        oss.write(';; Document: {e.date:%Y-%m-%d} {e.account} {e.filename}\n'.format(
            e=entry))

    def Pad(_, entry, oss):
        # Note: We don't need to output these because when we're loading the
        # Beancount file explicit padding entries will be generated
        # automatically, thus balancing the accounts. Ledger does not support
        # automatically padding, so we can just output this as a comment.
        oss.write(';; Pad: {e.date:%Y-%m-%d} {e.account} {e.source_account}\n'.format(
            e=entry))

    def Commodity(_, entry, oss):
        # No need for declaration.
        oss.write('commodity {e.currency}\n'.format(e=entry))

    def Open(_, entry, oss):
        oss.write('account {e.account:47}\n'.format(e=entry))
        if entry.currencies:
            oss.write('  assert {}\n'.format(' | '.join('commodity == "{}"'.format(currency)
                                                        for currency in entry.currencies)))

    def Close(_, entry, oss):
        oss.write(';; Close: {e.date:%Y-%m-%d} close {e.account}\n'.format(e=entry))

    def Price(_, entry, oss):
        oss.write(
            'P {:%Y-%m-%d} 00:00:00 {:<16} {:>16}\n'.format(
            entry.date, quote_currency(entry.currency), str(entry.amount)))

    def Event(_, entry, oss):
        oss.write(
            ';; Event: {e.date:%Y-%m-%d} "{e.type}" "{e.description}"\n'.format(e=entry))

    def Query(_, entry, oss):
        oss.write(
            ';; Query: {e.date:%Y-%m-%d} "{e.name}" "{e.query_string}"\n'.format(e=entry))

    def Custom(_, entry, oss):
        pass  # Don't render anything.
