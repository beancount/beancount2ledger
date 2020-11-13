"""
Common functions
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import re
import sys

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


def quote(currency):
    """
    Add quotes around a currency string
    """

    return f'"{currency}"' if re.search(r'[0-9\.-]', currency) else currency


def quote_match(match):
    """Add quotes around a re.MatchObject.

    Args:
      match: A MatchObject from the re module.
    Returns:
      A quoted string of the match contents.
    """
    currency = match.group(1)
    return quote(currency)


def quote_currency(string):
    """Quote all the currencies with numbers from the given string.

    Args:
      string: A string of text.
    Returns:
      A string of text, with the commodity expressions surrounded with quotes.
    """
    return re.sub(r'\b({})\b'.format(amount.CURRENCY_RE), quote_match, string)


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


def set_default(config):
    """
    Set some defaults for the config
    """

    if not "indent" in config:
        config["indent"] = 2
    return config


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


def get_lineno(posting):
    """
    Get line number of posting
    """

    meta = posting.meta or {}
    return meta.get("lineno", sys.maxsize)


def is_automatic_posting(posting):
    """
    Is posting an automatic posting added by beancount?
    """

    if not posting.meta:
        return False
    if '__automatic__' in posting.meta and not '__residual__' in posting.meta:
        return True
    return False


def filter_rounding_postings(entry, dformat):
    """
    Return entry without rounding postings that wouldn't be displayed
    because the display precision rounds them to 0.00.
    """

    postings = list(entry.postings)
    new_postings = []
    for posting in postings:
        pos_str = posting.units.to_string(dformat)
        # Don't create a posting if the amount (rounded to the display
        # precision) is 0.00.
        amt = amount.from_string(pos_str)
        if amt or posting.account != ROUNDING_ACCOUNT:
            new_postings.append(posting)
    entry = entry._replace(postings=new_postings)
    return entry


def map_data(string, config):
    """
    Map accounts and curencies according to user-defined mappings.
    """

    account_map = config.get("account_map", {})
    currency_map = config.get("currency_map", {})

    if not account_map and not currency_map:
        return string

    for account in account_map:
         string = re.sub(rf'\b{account}(?=  |\t|$)', account_map[account], string)

    def map_currency(match):
        currency = match.group(2)
        return quote(currency_map.get(currency, currency))

    string = re.sub(rf'(?<=\d\s)(")?({amount.CURRENCY_RE})\1?', map_currency, string)

    return string
