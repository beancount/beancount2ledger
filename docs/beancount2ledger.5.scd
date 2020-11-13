beancount2ledger(5)

; SPDX-FileCopyrightText: © 2020 Martin Michlmayr <tbm@cyrius.com>

; SPDX-License-Identifier: GPL-2.0-or-later

# NAME

beancount2ledger - configuration file for *beancount2ledger*

# OPTIONS

## GENERAL

*indent* <integer>
	The number of spaces to indent postings (default: 2).

## INFORMATION FROM METADATA

*auxdate* <string>
	A metadata key that specifies metadata that should become the auxiliary date of a transaction or posting (*date2* in hledger).

*postdate* <string>
	A metadata key that specifies metadata that should become the date of a posting (*date* in hledger).

*code* <string>
	A metadata key that specifies metadata that should become the code of a transaction.

## MAPPINGS

*account_map* <hash>
	A mapping of beancount account names to ledger account names.

*currency_map* <hash>
	A mapping of beancount currency names to ledger currency names.

# FORMAT

The configuration file uses YAML.

# AUTHORS

Martin Blais, Martin Michlmayr, and others

# SEE ALSO

*beancount2ledger*(1), *ledger*(1), *hledger*(1)

