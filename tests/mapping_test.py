"""
Tests for mapping of accounts and currencies
"""

# SPDX-FileCopyrightText: © 2020 Martin Michlmayr

# SPDX-License-Identifier: GPL-2.0-or-later

__license__ = "GPL-2.0-or-later"

from beancount.utils import test_utils
from beancount.parser import cmptest
from beancount import loader

import beancount2ledger
from beancount2ledger.common import map_data


class TestMappingUtilityFunctions(cmptest.TestCase):
    """
    Test mapping functions
    """

    def test_account(self):
        """
        Test account conversion
        """

        config = {}
        config["account_map"] = {
            "Assets:Test": "Assets:My Test",
            "Assets:Test-Bank": "Assets:Test Bank",
        }
        test = {
            "Assets:Test": "Assets:My Test",
            "Assets:Test-Bank": "Assets:Test Bank",
            "Assets:Testx": "Assets:Testx",
            "Assets:ABC": "Assets:ABC",
            "Assets:Test  Assets:Test": "Assets:My Test  Assets:My Test",
        }
        for orig, expected in test.items():
            self.assertEqual(map_data(orig, config), expected)

    def test_currency(self):
        """
        Test currency conversion
        """

        config = {}
        config["currency_map"] = {
            "EUR": "€",
            "EUR1": "EUR123",
            "EUR2": "EUR",
            "EURO": "EUR",
            "TEST": "TEST1",
        }
        test = {
            "0 EUR": "0 €",
            "0 EUR1": '0 "EUR123"',
            "0 EUR2": "0 EUR",
            "0 EURO": "0 EUR",
            "0 TEST": '0 "TEST1"',
        }
        for orig, expected in test.items():
            self.assertEqual(map_data(orig, config), expected)


class TestMappingConversion(test_utils.TestCase):
    """
    Test mapping after conversion
    """

    config = {}
    config["account_map"] = {
        "Assets:Test": "Assets:My Test",
        "Assets:Test-Bank": "Assets:Test Bank",
    }
    config["currency_map"] = {
        "EUR": "€",
        "TEST": "TEST1",
    }

    @loader.load_doc()
    def test_posting(self, entries, _, __):
        """
        2020-01-01 open Assets:Test

        2020-11-13 * "Test"
          Assets:Test        1000.00 EUR
          Assets:Test

        2020-11-13 * "Test"
          Assets:Test        1000.00 TEST
          Assets:Test
        """
        result = beancount2ledger.convert(entries, config=self.config)
        self.assertLines(
            """
            account Assets:My Test

            2020-11-13 * Test
                Assets:My Test                                                 1000.00 €
                Assets:My Test

            2020-11-13 * Test
                Assets:My Test                                                 1000.00 "TEST1"
                Assets:My Test
        """,  # NoQA: E501 line too long
            result,
        )
