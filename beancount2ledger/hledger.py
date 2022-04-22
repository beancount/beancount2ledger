"""
Convert Beancount entries to hledger
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import datetime
import re

from beancount.core.amount import Amount
from beancount.core import position
from beancount.core import interpolate
from beancount.core import display_context

from .common import ROUNDING_ACCOUNT
from .common import ledger_flag, ledger_str, quote_currency, user_meta
from .common import gen_bal_assignment, get_lineno, filter_rounding_postings
from .ledger import LedgerPrinter


class HLedgerPrinter(LedgerPrinter):
    "Multi-method for printing directives in HLedger format."

    def format_meta(self, key, val):
        """
        Format metadata
        """

        if val is None:
            return f"{key}:"
        return f"{key}: {val}"

    def Transaction(self, entry):
        indent = " " * self.config["indent"]

        if entry.flag == "P":
            match = re.match(
                r"\(Padding inserted for Balance of (.+) for difference",
                entry.narration,
            )
            if match:
                string = gen_bal_assignment(entry, match.group(1), indent)
                self.io.write(string)
                return

        # Insert a posting to absorb the residual if necessary. This is
        # sometimes needed because Ledger bases its balancing precision on the
        # *last* number of digits used on that currency. This is believed to be
        # a bug, so instead, we simply insert a rounding account to absorb the
        # residual and precisely balance the transaction.
        entry = interpolate.fill_residual_posting(entry, ROUNDING_ACCOUNT)
        # Remove postings which wouldn't be displayed (due to precision
        # rounding amounts to 0.00)
        entry = filter_rounding_postings(entry, self.dformat)

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
            self.io.write(" " + flag)
        code_key = self.config.get("code")
        if code_key and not meta.get(code_key) is None:
            code = meta[code_key]
            self.io.write(" (" + str(code) + ")")
            del meta[code_key]
        payee = " ".join(strings)
        if payee:
            self.io.write(" " + payee)
        self.io.write("\n")

        if entry.tags:
            self.io.write(indent + "; {}:\n".format(":, ".join(sorted(entry.tags))))
        if entry.links:
            self.io.write(indent + "; Link: {}\n".format(" ".join(sorted(entry.links))))

        for key, val in meta.items():
            meta = self.format_meta(key, val)
            if meta:
                self.io.write(indent + f"; {meta}\n")

        # If a posting without an amount is given and several amounts would
        # be added when balancing, beancount will create several postings.
        # But we ignore the amount on those postings (since they were added
        # by beancount and not the user), which means we may end up with
        # two or more postings with no amount, which is not valid.
        # Therefore, only take *one* posting by looking at the line number.
        seen = set()
        for posting in sorted(entry.postings, key=lambda p: get_lineno(p)):
            lineno = get_lineno(posting)
            if lineno is not None:
                if lineno in seen:
                    continue
                seen.add(lineno)
            self.Posting(posting, entry)

    def Posting(self, posting, entry):
        assert posting.account is not None
        flag = f"{ledger_flag(posting.flag)} " if ledger_flag(posting.flag) else ""
        flag_posting = f"{flag}{posting.account}"

        pos_str = ""
        # We don't use position.to_string() because that uses the same
        # dformat for amount and cost, but we want dformat from our
        # dcontext to format amounts to the right precision while
        # retaining the full precision for costs.
        if isinstance(posting.units, Amount):
            pos_str = posting.units.to_string(self.dformat)
        # Convert the cost as a price entry, that's what HLedger appears to want.
        if isinstance(posting.cost, position.Cost):
            pos_str += " @ " + position.cost_to_str(
                posting.cost, display_context.DEFAULT_FORMATTER, detail=False
            )

        price_str = (
            "@ {}".format(posting.price.to_string())
            if posting.price is not None and posting.cost is None
            else ""
        )
        if (
            posting.meta
            and "__automatic__" in posting.meta
            and "__residual__" not in posting.meta
        ):
            posting_str = f"{flag_posting}"
        else:
            # Width we have available for the amount: take width of
            # flag_posting add config["indent"] for the indentation
            # of postings and add 2 to separate account from amount
            len_amount = max(0, 76 - (len(flag_posting) + 2 + 2))
            posting_str = (
                f"{flag_posting}  {quote_currency(pos_str):>{len_amount}}"
                f" {quote_currency(price_str)}"
            )
        indent = " " * self.config["indent"]
        self.io.write(indent + posting_str.rstrip())
        self.io.write("\n")

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
                self.io.write(2 * indent + f"; {formatted_meta}\n")
