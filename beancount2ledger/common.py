"""
Common functions
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import re

from beancount.core import data
from beancount.core import convert
from beancount.core import amount

ROUNDING_ACCOUNT = 'Equity:Rounding'


def ledger_flag(flag):
    """
    Return the flag only if it's a valid flag in ledger
    """

    if flag and flag in ('*', '!'):
        return flag


def ledger_str(text):
    """
    Turn a beancount string into a valid ledger string.

    Specifically, turn multi-line strings into a single line
    """

    return text.replace('\n', '\\n')


def quote(match):
    """Add quotes around a re.MatchObject.

    Args:
      match: A MatchObject from the re module.
    Returns:
      A quoted string of the match contents.
    """
    currency = match.group(1)
    return '"{}"'.format(currency) if re.search(r'[0-9\.-]',
                                                currency) else currency


def quote_currency(string):
    """Quote all the currencies with numbers from the given string.

    Args:
      string: A string of text.
    Returns:
      A string of text, with the commodity expressions surrounded with quotes.
    """
    return re.sub(r'\b({})\b'.format(amount.CURRENCY_RE), quote, string)


def postings_by_type(entry):
    """Split up the postings by simple, at-cost, at-price.

    Args:
      entry: An instance of Transaction.
    Returns:
      A tuple of simple postings, postings with price conversions, postings held at cost.
    """
    postings_at_cost = []
    postings_at_price = []
    postings_simple = []
    for posting in entry.postings:
        if posting.cost:
            accumulator = postings_at_cost
        elif posting.price:
            accumulator = postings_at_price
        else:
            accumulator = postings_simple
        accumulator.append(posting)

    return (postings_simple, postings_at_price, postings_at_cost)


def split_currency_conversions(entry):
    """If the transaction has a mix of conversion at cost and a
    currency conversion, split the transaction into two transactions: one
    that applies the currency conversion in the same account, and one
    that uses the other currency without conversion.

    This is required because Ledger does not appear to be able to grok a
    transaction like this one:

      2014-11-02 * "Buy some stock with foreign currency funds"
        Assets:CA:Investment:HOOL          5 HOOL {520.0 USD}
        Expenses:Commissions            9.95 USD
        Assets:CA:Investment:Cash   -2939.46 CAD @ 0.8879 USD

    HISTORICAL NOTE: Adding a price directive on the first posting above makes
    Ledger accept the transaction. So we will not split the transaction here
    now. However, since Ledger's treatment of this type of conflict is subject
    to revision (See http://bugs.ledger-cli.org/show_bug.cgi?id=630), we will
    keep this code around, it might become useful eventually. See
    https://groups.google.com/d/msg/ledger-cli/35hA0Dvhom0/WX8gY_5kHy0J for
    details of the discussion.

    Args:
      entry: An instance of Transaction.
    Returns:
      A pair of
        converted: boolean, true if a conversion was made.
        entries: A list of the original entry if converted was False,
          or a list of the split converted entries if True.
    """
    assert isinstance(entry, data.Transaction)

    (postings_simple, postings_at_price,
     postings_at_cost) = postings_by_type(entry)

    converted = postings_at_cost and postings_at_price
    if converted:
        # Generate a new entry for each currency conversion.
        new_entries = []
        replacement_postings = []
        for posting_orig in postings_at_price:
            weight = convert.get_weight(posting_orig)
            posting_pos = data.Posting(posting_orig.account, weight, None,
                                       None, None, None)
            posting_neg = data.Posting(posting_orig.account, -weight, None,
                                       None, None, None)

            currency_entry = entry._replace(
                postings=[posting_orig, posting_neg],
                narration=entry.narration + ' (Currency conversion)')
            new_entries.append(currency_entry)
            replacement_postings.append(posting_pos)

        converted_entry = entry._replace(
            postings=(
                postings_at_cost + postings_simple + replacement_postings))
        new_entries.append(converted_entry)
    else:
        new_entries = [entry]

    return converted, new_entries
