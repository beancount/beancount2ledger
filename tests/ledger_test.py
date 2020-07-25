"""
Tests for ledger conversion
"""

# SPDX-FileCopyrightText: © 2014-2017 Martin Blais
# SPDX-FileCopyrightText: © 2020 Software in the Public Interest, Inc.

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

import tempfile
import datetime
import re
import shutil
import subprocess
import unittest

from beancount.core import data
from beancount.utils import test_utils
from beancount.scripts import example
from beancount.parser import cmptest
from beancount import loader

import beancount2ledger
from beancount2ledger.common import quote_currency, postings_by_type, split_currency_conversions


class TestLedgerUtilityFunctions(cmptest.TestCase):

    def test_quote_currency(self):
        test = """
          2014-10-01 * "Buy some stock with local funds"
            Assets:CA:Investment:HOOL          5 HOOL1 {500.00 USD}
            Expenses:Commissions            9.95 USD

          2020-07-25 * "Test for quoted commodity"
            Assets:Test                        1 E.R
            Assets:Test                       -1 E.R

          2020-07-25 * "Test for quoted commodity"
            Assets:Test                        1 E-R
            Assets:Test                       -1 E-R
        """
        expected = """
          2014-10-01 * "Buy some stock with local funds"
            Assets:CA:Investment:HOOL          5 "HOOL1" {500.00 USD}
            Expenses:Commissions            9.95 USD

          2020-07-25 * "Test for quoted commodity"
            Assets:Test                        1 "E.R"
            Assets:Test                       -1 "E.R"

          2020-07-25 * "Test for quoted commodity"
            Assets:Test                        1 "E-R"
            Assets:Test                       -1 "E-R"
        """
        self.assertEqual(expected, quote_currency(test))


class TestLedgerUtilityFunctionsOnPostings(cmptest.TestCase):

    @loader.load_doc()
    def setUp(self, entries, _, __):
        """
          2000-01-01 open Assets:CA:Investment:HOOL
          2000-01-01 open Expenses:Commissions
          2000-01-01 open Assets:CA:Investment:Cash

          2014-10-01 * "Buy some stock with local funds"
            Assets:CA:Investment:HOOL          5 HOOL {500.00 USD}
            Expenses:Commissions            9.95 USD
            Assets:CA:Investment:Cash   -2509.95 USD

          2014-10-02 * "Regular price conversion with fee"
            Assets:CA:Investment:Cash    2500.00 USD
            Expenses:Commissions            9.95 USD
            Assets:CA:Investment:Cash   -2826.84 CAD @ 0.8879 USD

          2014-10-03 * "Buy some stock with foreign currency funds"
            Assets:CA:Investment:HOOL          5 HOOL {520.0 USD}
            Expenses:Commissions            9.95 USD
            Assets:CA:Investment:Cash   -2939.46 CAD @ 0.8879 USD
        """
        self.txns = [entry for entry in entries if isinstance(entry, data.Transaction)]

    def test_postings_by_type(self):
        postings_lists = postings_by_type(self.txns[0])
        self.assertEqual([2, 0, 1], list(map(len, postings_lists)))

        postings_lists = postings_by_type(self.txns[1])
        self.assertEqual([2, 1, 0], list(map(len, postings_lists)))

        postings_lists = postings_by_type(self.txns[2])
        self.assertEqual([1, 1, 1], list(map(len, postings_lists)))

    def test_split_currency_conversions(self):
        converted, _ = split_currency_conversions(self.txns[0])
        self.assertFalse(converted)

        converted, _ = split_currency_conversions(self.txns[1])
        self.assertFalse(converted)

        converted, new_entries = split_currency_conversions(self.txns[2])
        self.assertTrue(converted)
        self.assertEqualEntries("""

          2014-10-03 * "Buy some stock with foreign currency funds (Currency conversion)"
            Assets:CA:Investment:Cash       -2,939.46 CAD @ 0.8879 USD
            Assets:CA:Investment:Cash        2,609.946534 USD

          2014-10-03 * "Buy some stock with foreign currency funds"
            Assets:CA:Investment:HOOL            5 HOOL {520.0 USD}
            Expenses:Commissions                 9.95 USD
            Assets:CA:Investment:Cash       -2,609.946534 USD

        """, new_entries)


def get_ledger_version():
    """Check that we have a sufficient version of Ledger installed.

    Returns:
      A tuple of integer, the Ledger binary version triple, or None,
      if Ledger is not installed or could not be run.
    """
    try:
        pipe = subprocess.Popen(['ledger', '--version'],
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = pipe.communicate()
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', stdout.decode('utf-8'))
        if match:
            return tuple(map(int, match.group(1, 2, 3)))
    except OSError:
        pass
    return None


class TestLedgerConversion(test_utils.TestCase):

    def check_parses_ledger(self, ledger_filename):
        """Assert that the filename parses through Ledger without errors.

        Args:
          filename: A string, the name of the Ledger file.
        """
        version = get_ledger_version()
        if version is None or version < (3, 0, 0):
            self.skipTest('Ledger is not installed or has insufficient version, '
                          'cannot verify conversion; skipping test')

        pipe = subprocess.Popen(['ledger', '-f', ledger_filename, 'bal'],
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = pipe.communicate()
        self.assertEqual(0, pipe.returncode, stderr)

    @loader.load_doc()
    def test_simple(self, entries, _, __):
        """
          ;; All supported features exhibited here.

          2013-01-01 open Expenses:Restaurant
          2013-01-01 open Assets:Cash         USD,CAD

          2014-02-15 price HOOL 500.00 USD

          2014-03-02 * "Something"
            Expenses:Restaurant   50.02 USD
            Assets:Cash

          2015-01-01 custom "budget" Expenses:Food  "yearly"  34.43 HRK
        """
        result = beancount2ledger.convert(entries)
        self.assertLines("""

          account Expenses:Restaurant

          account Assets:Cash
            assert commodity == "USD" | commodity == "CAD"

          P 2014-02-15 HOOL                                                        500.00 USD

          2014-03-02 * Something
            Expenses:Restaurant                                                     50.02 USD
            Assets:Cash

        """, result)

    @loader.load_doc()
    def test_cost_and_foreign_currency(self, entries, _, __):
        """
          plugin "beancount.plugins.implicit_prices"

          2014-01-01 open Assets:CA:Investment:HOOL
          2014-01-01 open Expenses:Commissions
          2014-01-01 open Assets:CA:Investment:Cash

          2014-11-02 * "Buy some stock with foreign currency funds"
            Assets:CA:Investment:HOOL          5 HOOL {520.0 USD}
            Expenses:Commissions            9.95 USD
            Assets:CA:Investment:Cash   -2939.46 CAD @ 0.8879 USD
        """
        result = beancount2ledger.convert(entries)
        self.assertLines("""

          account Assets:CA:Investment:HOOL

          account Expenses:Commissions

          account Assets:CA:Investment:Cash

          2014-11-02 * Buy some stock with foreign currency funds
            Assets:CA:Investment:HOOL           5 HOOL {520.0 USD} @ 520.0 USD
            Expenses:Commissions             9.95 USD
            Assets:CA:Investment:Cash    -2939.46 CAD @ 0.8879 USD
            Equity:Rounding             -0.003466 USD

          P 2014-11-02 HOOL    520.0 USD

          P 2014-11-02 CAD    0.8879 USD

        """, result)

    @loader.load_doc()
    def test_tags_links(self, entries, _, ___):
        """
          2019-01-25 open Assets:A
          2019-01-25 open Assets:B

          2019-01-25 * "Test tags" #foo ^link2 #bar #baz ^link1
            Assets:A                       10.00 EUR
            Assets:B                      -10.00 EUR
        """
        result = beancount2ledger.convert(entries)
        self.assertLines("""
          account Assets:A

          account Assets:B

          2019-01-25 * Test tags
            ; :bar:baz:foo:
            ; Link: link1, link2
            Assets:A                       10.00 EUR
            Assets:B                      -10.00 EUR
        """, result)

    @loader.load_doc()
    def test_account_open(self, entries, _, ___):
        """
          2019-01-25 open Assets:A
        """
        result = beancount2ledger.convert(entries)
        self.assertEqual("account Assets:A\n", result)

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
        result = beancount2ledger.convert(entries)
        self.assertLines("""
          account Assets:Test

          2020-07-23 * Test metadata
            ; string: foo
            ; year:: 2020
            ; amount:: 10.00 EUR
            ; date:: [2020-07-19]
            ; none:
            ; bool:: true
            Assets:Test                                                      10.00 EUR
            Assets:Test                                                      -10.00 EUR
        """, result)

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
        result = beancount2ledger.convert(entries)
        self.assertLines("""
          account Assets:Test

          2020-07-23 * Test metadata
            Assets:Test                                                      10.00 EUR
            Assets:Test                                                      -10.00 EUR
              ; string: foo
              ; year:: 2020
              ; amount:: 10.00 EUR
              ; date:: [2020-07-19]
              ; none:
              ; bool:: false
        """, result)

    @loader.load_doc()
    def test_metadata_none(self, entries, _, ___):
        """
          2000-01-01 open Assets:Test1
          2000-01-01 open Assets:Test2

          2019-01-21 pad Assets:Test1 Assets:Test2
          2019-01-22 balance Assets:Test1   10.00 GBP
        """
        # padding (P) entries don't set entry.meta or posting.meta, so
        # convert to make sure we don't crash.
        _ = beancount2ledger.convert(entries)

    @loader.load_doc()
    def test_cost_info(self, entries, _, ___):
        """
          2020-01-01 open Expenses:Computers
          2020-01-01 open Assets:Bank

          2020-02-01 * "Super Shop"  "New computer"
            Expenses:Computers       1 COMPUTER {900.00 USD, 2019-12-25, "DiscountedComputer"} @ 1100.00 USD
            Assets:Bank

          2020-02-02 * "Super Shop"  "New computer"
            Expenses:Computers       1 COMPUTER {900.00 USD, "DiscountedComputer"} @ 1100.00 USD
            Assets:Bank

          2020-02-03 * "Super Shop"  "New computer"
            Expenses:Computers       1 COMPUTER {900.00 USD, 2019-12-25} @ 1100.00 USD
            Assets:Bank
        """
        result = beancount2ledger.convert(entries)
        self.assertLines("""
          account Expenses:Computers

          account Assets:Bank

          2020-02-01 * Super Shop | New computer
            Expenses:Computers  1 COMPUTER {900.00 USD} [2019-12-25] (DiscountedComputer) @ 1100.00 USD
            Assets:Bank

          2020-02-02 * Super Shop | New computer
            Expenses:Computers           1 COMPUTER {900.00 USD} (DiscountedComputer) @ 1100.00 USD
            Assets:Bank

          2020-02-03 * Super Shop | New computer
            Expenses:Computers                      1 COMPUTER {900.00 USD} [2019-12-25] @ 1100.00 USD
            Assets:Bank
        """, result)

    @loader.load_doc()
    def test_posting_alignment(self, entries, _, ___):
        """
          2020-01-01 open Assets:Test
          2020-01-01 open Assets:TestTestTestTestTestTestTestTestTestTestTestTest
          2020-01-01 open Assets:TestTestTestTestTestTestTestTestTestTestTestTestTestTest
          2010-01-01 open Assets:TestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTest
          2020-07-17 * "Test alignment of postings"
            * Assets:Test     1000000000.00 EUR
            Assets:Test      -1000000000.00 EUR
            * Assets:TestTestTestTestTestTestTestTestTestTestTestTest        1000.00 EUR
            Assets:Test                                                     -1000.00 EUR
            * Assets:TestTestTestTestTestTestTestTestTestTestTestTestTestTest     1000.00 EUR
            Assets:Test                                                          -1000.00 EUR
            Assets:TestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTestTest  1000.00 EUR
            Assets:Test                                                                         -1000.00 EUR
            * Assets:Test     100000.00 EUREUREUREUREUR
            Assets:Test      -100000.00 EUREUREUREUREUR
        """
        result = beancount2ledger.convert(entries)
        len_postings = [len(line) for line in result.rstrip().split('\n')]
        self.assertEqual(len_postings[-10:-1:2], [75, 75, 80, 98, 75])

    @loader.load_doc()
    def test_posting_no_amount(self, entries, _, ___):
        """
          2010-01-01 open Assets:Test

          2020-07-25 txn "No amount on second posting"
            Assets:Test                        10.00 EUR
            Assets:Test
        """
        result = beancount2ledger.convert(entries)
        self.assertLines("""
          account Assets:Test

          2020-07-25 * No amount on second posting
            Assets:Test                        10.00 EUR
            Assets:Test
        """, result)

    @loader.load_doc()
    def test_price_alignment(self, entries, _, ___):
        """
          2020-07-23 price EUR 1.16 USD
          2020-07-24 price EUREUREUREUREUREUREUREUR 1.16 USD
          2020-07-24 price EUREUREUREUREUREUREUREU1 1.16 USD
        """
        result = beancount2ledger.convert(entries)
        len_pricedb = [len(line) for line in result.rstrip().split('\n')]
        self.assertEqual(len_pricedb[::2], [75, 75, 75])

    @loader.load_doc()
    def test_multiline_strings(self, entries, _, ___):
        """
          2010-01-01 open Assets:Test

          2020-07-25 txn "Foo
bar" "Foo
bar
bar"
            meta: "Foo
bar"
            Assets:Test                        10.00 EUR
            meta: "Foo
bar"
            Assets:Test                       -10.00 EUR
        """
        result = beancount2ledger.convert(entries)
        self.assertLines(r"""
          account Assets:Test

          2020-07-25 * Foo\nbar | Foo\nbar\nbar
            ; meta: Foo\nbar
            Assets:Test                                                     10.00 EUR
              ; meta: Foo\nbar
            Assets:Test                                                    -10.00 EUR
        """, result)

    @loader.load_doc()
    def test_flags(self, entries, _, ___):
        """
          2010-01-01 open Assets:Test

          2020-07-25 txn "Valid flags"
            * Assets:Test                        10.00 EUR
            ! Assets:Test

          2020-07-25 R "Invalid flags"
            M Assets:Test                        10.00 EUR
            S Assets:Test                       -10.00 EUR
        """
        result = beancount2ledger.convert(entries)
        self.assertLines(r"""
          account Assets:Test

          2020-07-25 * Valid flags
            * Assets:Test                                                   10.00 EUR
            ! Assets:Test

          2020-07-25 Invalid flags
            Assets:Test                                                     10.00 EUR
            Assets:Test                                                    -10.00 EUR
        """, result)

    def test_example(self):
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

            # Convert the file to Ledger format.
            with tempfile.NamedTemporaryFile('w', suffix='.ledger') as lgrfile:
                result = beancount2ledger.convert_file(beanfile.name)
                lgrfile.write(result)
                lgrfile.flush()

                # FIXME: Use a proper temp dir.
                shutil.copyfile(lgrfile.name, '/tmp/test.ledger')
                self.check_parses_ledger(lgrfile.name)


if __name__ == '__main__':
    unittest.main()
