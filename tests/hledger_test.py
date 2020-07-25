"""
Tests for hledger conversion
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais
# SPDX-FileCopyrightText: © 2020 Software in the Public Interest, Inc.

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import tempfile
import datetime
import unittest

from beancount.utils import test_utils
from beancount.scripts import example
from beancount import loader

import beancount2ledger


class TestHLedgerConversion(test_utils.TestCase):
    """
    Tests for hledger conversion
    """

    @loader.load_doc()
    def test_tags_links(self, entries, _, __):
        """
          2019-01-25 open Assets:A
          2019-01-25 open Assets:B

          2019-01-25 * "Test tags" #foo ^link2 #bar #baz ^link1
            Assets:A                       10.00 EUR
            Assets:B                      -10.00 EUR
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines("""
          account Assets:A

          account Assets:B

          2019-01-25 * Test tags
            ; bar:, baz:, foo:
            ; Link: link1 link2
            Assets:A                       10.00 EUR
            Assets:B                      -10.00 EUR
        """, result)

    @loader.load_doc()
    def test_cost(self, entries, _, __):
        """
          2020-01-01 open Assets:Bank
          2020-01-01 open Expenses:Grocery

          2020-01-01 * "Grocery"  "Salad"
              Expenses:Grocery                5 SALAD  {1.00 USD} @   1.00 USD
              Assets:Bank

          2020-01-01 * "Grocery"  "Salad"
              Expenses:Grocery                5 SALAD  {1.00 USD} @@  5.00 USD
              Assets:Bank

          2020-01-01 * "Grocery"  "Salad"
              Expenses:Grocery                5 SALAD {{5.00 USD}} @  1.00 USD
              Assets:Bank

          2020-01-01 * "Grocery"  "Salad"
              Expenses:Grocery                5 SALAD {{5.00 USD}} @@ 5.00 USD
              Assets:Bank
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines("""
          account Assets:Bank

          account Expenses:Grocery

          2020-01-01 * Grocery | Salad
            Expenses:Grocery                                                 5 SALAD @ 1.00 USD
            Assets:Bank

          2020-01-01 * Grocery | Salad
            Expenses:Grocery                                                 5 SALAD @ 1.00 USD
            Assets:Bank

          2020-01-01 * Grocery | Salad
            Expenses:Grocery                                                 5 SALAD @ 1.00 USD
            Assets:Bank

          2020-01-01 * Grocery | Salad
            Expenses:Grocery                                                 5 SALAD @ 1.00 USD
            Assets:Bank
        """, result)

    def test_example(self):
        """
        Test converted example with hledger
        """
        with tempfile.NamedTemporaryFile('w',
                                         suffix='.beancount',
                                         encoding='utf-8') as beanfile:
            # Generate an example Beancount file.
            example.write_example_file(datetime.date(1980, 1, 1),
                                       datetime.date(2010, 1, 1),
                                       datetime.date(2014, 1, 1),
                                       reformat=True,
                                       file=beanfile)
            beanfile.flush()

            # Convert the file to HLedger format.
            #
            # Note: don't bother parsing for now, just a smoke test to make sure
            # we don't fail on run.
            with tempfile.NamedTemporaryFile('w', suffix='.hledger') as lgrfile:
                result = beancount2ledger.convert_file(beanfile.name, "hledger")
                lgrfile.write(result)
                lgrfile.flush()


if __name__ == '__main__':
    unittest.main()
