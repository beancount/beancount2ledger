"""
Convert Beancount entries to hledger
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais
# SPDX-FileCopyrightText: © 2020 Software in the Public Interest, Inc.

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import datetime
import io

from beancount.core.amount import Amount
from beancount.core.inventory import Inventory
from beancount.core.number import Decimal
from beancount.core import position
from beancount.core import amount
from beancount.core import interpolate
from beancount.core import display_context

from .common import ROUNDING_ACCOUNT
from .common import ledger_flag, ledger_str, quote_currency, postings_by_type


def user_meta(meta):
    """
    Get user defined metadata, i.e. skip some automatically added keys
    """

    ignore = [
        '__tolerances__',
        '__automatic__',
        '__residual__',
        'filename',
        'lineno',
    ]
    return {key: meta[key] for key in meta if key not in ignore}


def format_meta(key, val):
    """"
    Format metadata
    """

    # See write_metadata() in beancount/parser/printer.py for allowed types
    if isinstance(val, str):
        sep = ':'
        val = ledger_str(val)
    elif isinstance(val, Decimal):
        sep = '::'
    elif isinstance(val, Amount):
        sep = '::'
    elif isinstance(val, datetime.date):
        sep = '::'
        val = f"[{val}]"
    elif isinstance(val, bool):
        sep = '::'
        val = 'true' if val else 'false'
    elif isinstance(val, (dict, Inventory)):
        # Ignore dicts, don't print them out (according to printer.py)
        return
    elif val is None:
        return f"{key}:"
    else:
        raise ValueError(f"Unexpected metadata type: {type(val)}")
    return f"{key}{sep} {val}"


class LedgerPrinter:
    "Multi-method for printing directives in Ledger format."

    # pylint: disable=invalid-name

    def __init__(self, dcontext=None):
        self.io = None
        self.dcontext = dcontext or display_context.DEFAULT_DISPLAY_CONTEXT
        self.dformat = self.dcontext.build(
            precision=display_context.Precision.MOST_COMMON)
        self.dformat_max = self.dcontext.build(
            precision=display_context.Precision.MAXIMUM)

    def __call__(self, obj):
        self.io = io.StringIO()
        method = getattr(self, obj.__class__.__name__)
        method(obj)
        return self.io.getvalue()

    def Transaction(self, entry):
        """Transactions"""

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
            ' '.join(strings), flag=flag, e=entry))

        if entry.tags:
            self.io.write('  ; :{}:\n'.format(':'.join(sorted(entry.tags))))
        if entry.links:
            self.io.write('  ; Link: {}\n'.format(', '.join(
                sorted(entry.links))))

        for key, val in user_meta(entry.meta or {}).items():
            meta = format_meta(key, val)
            if meta:
                self.io.write(f'  ; {meta}\n')

        for posting in entry.postings:
            self.Posting(posting, entry)

    def Posting(self, posting, entry):
        """Postings"""

        assert posting.account is not None
        flag = f"{ledger_flag(posting.flag)} " if ledger_flag(
            posting.flag) else ''
        flag_posting = f"{flag}{posting.account}"

        # We can't use default=True, even though we're interested in the
        # cost details, but we have to add them ourselves in the format
        # expected by ledger.
        pos_str = (position.to_string(posting, self.dformat, detail=False)
                   if isinstance(posting.units, Amount) else '')
        if posting.cost:
            if posting.cost.date != entry.date:
                pos_str += f" [{posting.cost.date}]"
            if posting.cost.label:
                pos_str += f" ({posting.cost.label})"

        if posting.price is not None:
            price_str = '@ {}'.format(
                posting.price.to_string(self.dformat_max))
        else:
            # Figure out if we need to insert a price on a posting held at cost.
            # See https://groups.google.com/d/msg/ledger-cli/35hA0Dvhom0/WX8gY_5kHy0J
            (postings_simple, postings_at_price,
             postings_at_cost) = postings_by_type(entry)

            cost = posting.cost
            if postings_at_price and postings_at_cost and cost:
                price_str = '@ {}'.format(
                    amount.Amount(cost.number,
                                  cost.currency).to_string(self.dformat))
            else:
                price_str = ''

        if posting.meta and '__automatic__' in posting.meta and not '__residual__' in posting.meta:
            posting_str = f'  {flag_posting}'
        else:
            # Width we have available for the amount: take width of
            # flag_posting add 2 for the indentation of postings and
            # add 2 to separate account from amount
            len_amount = max(0, 75 - (len(flag_posting) + 2 + 2))
            posting_str = f'  {flag_posting}  {quote_currency(pos_str):>{len_amount}} {quote_currency(price_str)}'
        self.io.write(posting_str.rstrip())
        self.io.write('\n')

        for key, val in user_meta(posting.meta or {}).items():
            meta = format_meta(key, val)
            if meta:
                self.io.write(f'    ; {meta}\n')

    def Balance(self, entry):
        """Balance entries"""

        # We cannot output balance directive equivalents because Ledger only
        # supports file assertions and not dated assertions. See "Balance
        # Assertions for Beancount" for details:
        # https://docs.google.com/document/d/1vyemZFox47IZjuBrT2RjhSHZyTgloYOUeJb73RxMRD0/

    def Note(self, entry):
        """Note entries"""

        self.io.write(
            ';; Note: {e.date:%Y-%m-%d} {e.account} {e.comment}\n'.format(
                e=entry))

    def Document(self, entry):
        """Document entries"""

        self.io.write(
            ';; Document: {e.date:%Y-%m-%d} {e.account} {e.filename}\n'.format(
                e=entry))

    def Pad(self, entry):
        """Pad entries"""

        # Note: We don't need to output these because when we're loading the
        # Beancount file explicit padding entries will be generated
        # automatically, thus balancing the accounts. Ledger does not support
        # automatically padding, so we can just output this as a comment.
        self.io.write(
            ';; Pad: {e.date:%Y-%m-%d} {e.account} {e.source_account}\n'.
            format(e=entry))

    def Commodity(self, entry):
        "Commodity declarations" ""

        # No need for declaration.
        self.io.write('commodity {e.currency}\n'.format(e=entry))

    def Open(self, entry):
        """Account open statements"""

        self.io.write('account {e.account}\n'.format(e=entry))
        if entry.currencies:
            self.io.write('  assert {}\n'.format(' | '.join(
                'commodity == "{}"'.format(currency)
                for currency in entry.currencies)))

    def Close(self, entry):
        """Account close statements"""

        self.io.write(
            ';; Close: {e.date:%Y-%m-%d} close {e.account}\n'.format(e=entry))

    def Price(self, entry):
        """Price entries"""

        self.io.write('P {:%Y-%m-%d} {:<26} {:>35}\n'.format(
            entry.date, quote_currency(entry.currency), str(entry.amount)))

    def Event(self, entry):
        """ Event entries"""

        self.io.write(
            ';; Event: {e.date:%Y-%m-%d} "{e.type}" "{e.description}"\n'.
            format(e=entry))

    def Query(self, entry):
        """Query entries"""

        self.io.write(
            ';; Query: {e.date:%Y-%m-%d} "{e.name}" "{e.query_string}"\n'.
            format(e=entry))

    def Custom(self, entry):
        """Custom entries"""

        # Don't render anything.
