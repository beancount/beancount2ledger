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
        self.assertLines(
            """
          account Assets:A

          account Assets:B

          2019-01-25 * Test tags
            ; bar:, baz:, foo:
            ; Link: link1 link2
            Assets:A                       10.00 EUR
            Assets:B                      -10.00 EUR
        """,
            result,
        )

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
        self.assertLines(
            """
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
        """,  # NoQA: E501 line too long
            result,
        )

    @loader.load_doc()
    def test_metadata_entry(self, entries, _, ___):
        """
        2020-01-01 open Assets:Test

        2020-07-23 * "Test metadata"
          string: "foo"
          year: 2020
          amount: 10.00 EUR
          date: 2020-07-19
          none:
          bool: TRUE
          Assets:Test     10.00 EUR
          Assets:Test    -10.00 EUR
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            """
          account Assets:Test

          2020-07-23 * Test metadata
            ; string: foo
            ; year: 2020
            ; amount: 10.00 EUR
            ; date: 2020-07-19
            ; none:
            ; bool: True
            Assets:Test                                                      10.00 EUR
            Assets:Test                                                     -10.00 EUR
        """,
            result,
        )

    @loader.load_doc()
    def test_metadata_posting(self, entries, _, ___):
        """
        2020-01-01 open Assets:Test

        2020-07-23 * "Test metadata"
          Assets:Test     10.00 EUR
          Assets:Test    -10.00 EUR
          string: "foo"
          year: 2020
          amount: 10.00 EUR
          date: 2020-07-19
          none:
          bool: FALSE
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            """
          account Assets:Test

          2020-07-23 * Test metadata
            Assets:Test                                                      10.00 EUR
            Assets:Test                                                      -10.00 EUR
              ; string: foo
              ; year: 2020
              ; amount: 10.00 EUR
              ; date: 2020-07-19
              ; none:
              ; bool: False
        """,
            result,
        )

    @loader.load_doc()
    def test_auxdate(self, entries, _, ___):
        """
        2020-01-01 open Assets:Test
        2020-01-01 open Equity:Opening-Balance

        2020-11-12 * "Test with aux date"
          aux-date: 2020-11-03
          Assets:Test                        10.00 EUR
          Equity:Opening-Balance

        2020-11-12 * "Test with transaction and posting aux date"
          aux-date: 2020-11-03
          Assets:Test                        10.00 EUR
            aux-date: 2020-11-04
          Equity:Opening-Balance

        2020-11-12 * "Test with posting date"
          Assets:Test                        10.00 EUR
            postdate: 2020-11-03
          Equity:Opening-Balance            -10.00 EUR
            postdate: 2020-11-04
            test: "foo"

        2020-11-12 * "Testing with posting date and posting aux date"
          Assets:Test                        10.00 EUR
            aux-date: 2020-11-04
            postdate: 2020-11-03
          Equity:Opening-Balance            -10.00 EUR
            postdate: 2020-11-03
            aux-date: 2020-11-04
            test: "foo"
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Assets:Test

            account Equity:Opening-Balance

            2020-11-12 * Test with aux date
              ; aux-date: 2020-11-03
              Assets:Test                                                      10.00 EUR
              Equity:Opening-Balance

            2020-11-12 * Test with transaction and posting aux date
              ; aux-date: 2020-11-03
              Assets:Test                                                      10.00 EUR
                ; aux-date: 2020-11-04
              Equity:Opening-Balance

            2020-11-12 * Test with posting date
              Assets:Test                                                      10.00 EUR
                ; postdate: 2020-11-03
              Equity:Opening-Balance                                          -10.00 EUR
                ; postdate: 2020-11-04
                ; test: foo

            2020-11-12 * Testing with posting date and posting aux date
              Assets:Test                                                      10.00 EUR
                ; aux-date: 2020-11-04
                ; postdate: 2020-11-03
              Equity:Opening-Balance                                          -10.00 EUR
                ; postdate: 2020-11-03
                ; aux-date: 2020-11-04
                ; test: foo

        """,
            result,
        )

        config = {"auxdate": "aux-date", "postdate": "postdate"}
        result = beancount2ledger.convert(entries, "hledger", config=config)
        self.assertLines(
            r"""
            account Assets:Test

            account Equity:Opening-Balance

            2020-11-12=2020-11-03 * Test with aux date
              Assets:Test                                                      10.00 EUR
              Equity:Opening-Balance

            2020-11-12=2020-11-03 * Test with transaction and posting aux date
              Assets:Test                                                      10.00 EUR
                ; date2: 2020-11-04
              Equity:Opening-Balance

            2020-11-12 * Test with posting date
              Assets:Test                                                      10.00 EUR
                ; date: 2020-11-03
              Equity:Opening-Balance                                          -10.00 EUR
                ; test: foo
                ; date: 2020-11-04

            2020-11-12 * Testing with posting date and posting aux date
              Assets:Test                                                      10.00 EUR
                ; date: 2020-11-03
                ; date2: 2020-11-04
              Equity:Opening-Balance                                          -10.00 EUR
                ; test: foo
                ; date: 2020-11-03
                ; date2: 2020-11-04
        """,
            result,
        )

        config = {"auxdate": "aux-date"}
        result = beancount2ledger.convert(entries, "hledger", config=config)
        self.assertLines(
            r"""
            account Assets:Test

            account Equity:Opening-Balance

            2020-11-12=2020-11-03 * Test with aux date
              Assets:Test                                                      10.00 EUR
              Equity:Opening-Balance

            2020-11-12=2020-11-03 * Test with transaction and posting aux date
              Assets:Test                                                      10.00 EUR
                ; date2: 2020-11-04
              Equity:Opening-Balance

            2020-11-12 * Test with posting date
              Assets:Test                                                      10.00 EUR
                ; postdate: 2020-11-03
              Equity:Opening-Balance                                          -10.00 EUR
                ; postdate: 2020-11-04
                ; test: foo

            2020-11-12 * Testing with posting date and posting aux date
              Assets:Test                                                      10.00 EUR
                ; postdate: 2020-11-03
                ; date2: 2020-11-04
              Equity:Opening-Balance                                          -10.00 EUR
                ; postdate: 2020-11-03
                ; test: foo
                ; date2: 2020-11-04
        """,
            result,
        )

    @loader.load_doc()
    def test_code(self, entries, _, ___):
        """
        2020-01-01 open Assets:Test

        2020-01-01 open Equity:Opening-Balance

        2020-11-12 * "No code"
          Assets:Test                        10.00 EUR
          Equity:Opening-Balance

        2020-11-12 * "Code is integer"
          code: 1234
          Assets:Test                        10.00 EUR
          Equity:Opening-Balance

        2020-11-12 * "Code is string"
          code: "string"
          Assets:Test                        10.00 EUR
          Equity:Opening-Balance

        2020-11-12 * "Code is date"
          code: 2020-11-12
          Assets:Test                        10.00 EUR
          Equity:Opening-Balance

        2020-11-12 * "Code is empty"
          code:
          Assets:Test                        10.00 EUR
          Equity:Opening-Balance

        2020-11-12 * "Code and aux-date"
          aux-date: 2020-11-03
          code: 1234
          Assets:Test                        10.00 EUR
          Equity:Opening-Balance
        """

        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Assets:Test

            account Equity:Opening-Balance

            2020-11-12 * No code
              Assets:Test                                                     10.00 EUR
              Equity:Opening-Balance

            2020-11-12 * Code is integer
              ; code: 1234
              Assets:Test                                                     10.00 EUR
              Equity:Opening-Balance

            2020-11-12 * Code is string
              ; code: string
              Assets:Test                                                     10.00 EUR
              Equity:Opening-Balance

            2020-11-12 * Code is date
              ; code: 2020-11-12
              Assets:Test                                                     10.00 EUR
              Equity:Opening-Balance

            2020-11-12 * Code is empty
              ; code:
              Assets:Test                                                     10.00 EUR
              Equity:Opening-Balance

            2020-11-12 * Code and aux-date
              ; aux-date: 2020-11-03
              ; code: 1234
              Assets:Test                                                     10.00 EUR
              Equity:Opening-Balance
        """,
            result,
        )

        config = {"code": "code", "auxdate": "aux-date"}
        result = beancount2ledger.convert(entries, "hledger", config=config)
        self.assertLines(
            r"""
            account Assets:Test

            account Equity:Opening-Balance

            2020-11-12 * No code
                Assets:Test                                                   10.00 EUR
                Equity:Opening-Balance

            2020-11-12 * (1234) Code is integer
                Assets:Test                                                   10.00 EUR
                Equity:Opening-Balance

            2020-11-12 * (string) Code is string
                Assets:Test                                                   10.00 EUR
                Equity:Opening-Balance

            2020-11-12 * (2020-11-12) Code is date
                Assets:Test                                                   10.00 EUR
                Equity:Opening-Balance

            2020-11-12 * Code is empty
                ; code:
                Assets:Test                                                   10.00 EUR
                Equity:Opening-Balance

            2020-11-12=2020-11-03 * (1234) Code and aux-date
                Assets:Test                                                   10.00 EUR
                Equity:Opening-Balance
        """,
            result,
        )

    @loader.load_doc()
    def test_retain_precision(self, entries, _, ___):
        """
        2010-01-01 open Expenses:Nutrition:Food
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Investments

        2020-01-10 * "Supermarket"
          Expenses:Nutrition:Food  150.75 THB @ 0.03310116086236 USD
          Assets:Bank                                      -4.99 USD

        2020-01-10 * "Supermarket"
          Expenses:Nutrition:Food  150.75 THB @ 0.025207296849 GBP
          Assets:Bank                                    -3.80 GBP

        2020-02-28 * "Bought GB00BPN5P782"
          Assets:Investments           1 GB00BPN5P782 {101.689996215 GBP}
          Assets:Investments                                 -101.69 GBP
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Expenses:Nutrition:Food

            account Assets:Bank

            account Assets:Investments

            2020-01-10 * Supermarket
              Expenses:Nutrition:Food                                        150.75 THB @ 0.03310116086236 USD
              Assets:Bank                                                     -4.99 USD

            2020-01-10 * Supermarket
              Expenses:Nutrition:Food                                        150.75 THB @ 0.025207296849 GBP
              Assets:Bank                                                     -3.80 GBP

            2020-02-28 * Bought GB00BPN5P782
              Assets:Investments                    1 "GB00BPN5P782" @ 101.689996215 GBP
              Assets:Investments                                             -101.69 GBP
        """,  # NoQA: E501 line too long
            result,
        )

    @loader.load_doc()
    def test_rounding(self, entries, _, ___):
        """
        2010-01-01 open Expenses:Test
        2010-01-01 open Assets:Bank

        2020-01-10 * "Test"
          Expenses:Test                           4.990 USD
          Assets:Bank                            -4.990 USD

        2020-01-10 * "Test: will fail in ledger due to precision of USD"
          Expenses:Test            150.75 THB @ 0.03344 USD
          Assets:Bank                             -5.04 USD

        2020-01-10 * "Test: will fail in ledger due to precision of USD"
          Expenses:Test               140.1 THB @ 0.021 USD
          Assets:Bank                             -2.94 USD
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Expenses:Test

            account Assets:Bank

            2020-01-10 * Test
              Expenses:Test                                                    4.990 USD
              Assets:Bank                                                     -4.990 USD

            2020-01-10 * Test: will fail in ledger due to precision of USD
              Expenses:Test                                                   150.75 THB @ 0.03344 USD
              Assets:Bank                                                     -5.040 USD
              Equity:Rounding                                                 -0.001 USD

            2020-01-10 * Test: will fail in ledger due to precision of USD
              Expenses:Test                                                   140.10 THB @ 0.021 USD
              Assets:Bank                                                     -2.940 USD
              Equity:Rounding                                                 -0.002 USD
        """,  # NoQA: E501 line too long
            result,
        )

    @loader.load_doc()
    def test_avoid_too_much_precision(self, entries, _, ___):
        """
        2020-01-01 open Assets:Property
        2020-01-01 open Equity:Opening-Balance

        2020-10-23 * "Test of precision for EUR"
            Assets:Property               0.11110000 FOO {300.00 EUR}
            Equity:Opening-Balance                        -33.33 EUR

        2020-10-23 * "Test of precision for EUR"
            Assets:Property               0.11110000 FOO {300.00 EUR}
            Equity:Opening-Balance

        2020-10-23 * "Test of precision for EUR"
            Assets:Property                   0.1111 FOO {300.00 EUR}
            Equity:Opening-Balance
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Assets:Property

            account Equity:Opening-Balance

            2020-10-23 * Test of precision for EUR
              Assets:Property                                0.11110000 FOO @ 300.00 EUR
              Equity:Opening-Balance                                          -33.33 EUR

            2020-10-23 * Test of precision for EUR
              Assets:Property                                0.11110000 FOO @ 300.00 EUR
              Equity:Opening-Balance

            2020-10-23 * Test of precision for EUR
              Assets:Property                                0.11110000 FOO @ 300.00 EUR
              Equity:Opening-Balance
        """,
            result,
        )

    @loader.load_doc()
    def test_avoid_multiple_null_postings(self, entries, _, ___):
        """
        2010-01-01 open Assets:Cash
        2010-01-01 open Equity:Opening-balance

        2020-01-01 * "Opening balance: cash"
          Assets:Cash                                               0.10 EUR
          Assets:Cash                                               1.00 GBP
          Equity:Opening-balance
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Assets:Cash

            account Equity:Opening-balance

            2020-01-01 * Opening balance: cash
              Assets:Cash                                                       0.10 EUR
              Assets:Cash                                                       1.00 GBP
              Equity:Opening-balance
        """,
            result,
        )

    @loader.load_doc()
    def test_add_price_when_needed(self, entries, _, ___):
        """
        2020-01-01 open Assets:Property
        2020-01-01 open Equity:Opening-Balance

        2020-11-13 * "Cost without price"
            Assets:Property                   0.1 FOO {300.00 EUR}
            Assets:Property                   0.2 BAR {200.00 EUR}
            Equity:Opening-Balance         -70.00 EUR
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Assets:Property

            account Equity:Opening-Balance

            2020-11-13 * Cost without price
              Assets:Property                                      0.1 FOO @ 300.00 EUR
              Assets:Property                                      0.2 BAR @ 200.00 EUR
              Equity:Opening-Balance                                         -70.00 EUR
        """,
            result,
        )

    @loader.load_doc()
    def test_keep_zero_amounts(self, entries, _, ___):
        """
        2010-01-01 open Assets:Investments
        2010-01-01 open Expenses:Fees:Investments

        2020-05-24 * "Bought ETH"
          Assets:Investments                     0.00000221 ETH {190.60 EUR}
          Expenses:Fees:Investments                                 0.00 EUR
          Assets:Investments                                       -0.00 EUR
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Assets:Investments

            account Expenses:Fees:Investments

            2020-05-24 * Bought ETH
              Assets:Investments                            0.00000221 ETH @ 190.60 EUR
              Expenses:Fees:Investments                                        0.00 EUR
              Assets:Investments                                               0.00 EUR
        """,
            result,
        )

    @loader.load_doc()
    def test_preserve_posting_order(self, entries, _, ___):
        """
        2010-01-01 open Assets:Test

        2020-07-24 * "Posting order"
          Assets:Test        1000.00 EUR
          Assets:Test       -1000.00 EUR
          Assets:Test        1000.00 EUREUREUREUREUR
          Assets:Test       -1000.00 EUREUREUREUREUR
          Assets:Test        1000.00 EUR
          Assets:Test       -1000.00 EUR
        """
        result = beancount2ledger.convert(entries, "hledger")
        self.assertLines(
            r"""
            account Assets:Test

            2020-07-24 * Posting order
              Assets:Test                                                    1000.00 EUR
              Assets:Test                                                   -1000.00 EUR
              Assets:Test                                        1000.00 EUREUREUREUREUR
              Assets:Test                                       -1000.00 EUREUREUREUREUR
              Assets:Test                                                    1000.00 EUR
              Assets:Test                                                   -1000.00 EUR
        """,
            result,
        )

    def test_example(self):
        """
        Test converted example with hledger
        """
        with tempfile.NamedTemporaryFile(
            "w", suffix=".beancount", encoding="utf-8"
        ) as beanfile:
            # Generate an example Beancount file.
            example.write_example_file(
                datetime.date(1980, 1, 1),
                datetime.date(2010, 1, 1),
                datetime.date(2014, 1, 1),
                reformat=True,
                file=beanfile,
            )
            beanfile.flush()

            # Convert the file to HLedger format.
            #
            # Note: don't bother parsing for now, just a smoke test to make sure
            # we don't fail on run.
            with tempfile.NamedTemporaryFile("w", suffix=".hledger") as lgrfile:
                result = beancount2ledger.convert_file(beanfile.name, "hledger")
                lgrfile.write(result)
                lgrfile.flush()


if __name__ == "__main__":
    unittest.main()
