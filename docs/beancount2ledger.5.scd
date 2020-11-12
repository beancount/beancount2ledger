beancount2ledger(5)

; SPDX-FileCopyrightText: © 2020 Martin Michlmayr <tbm@cyrius.com>

; SPDX-License-Identifier: GPL-2.0-or-later

# NAME

beancount2ledger - configuration file for *beancount2ledger*

# OPTIONS

*indent* <integer>
	The number of spaces to indent postings (default: 2).

*auxdate* <string>
	A metadata key that specifies metadata that should become the auxiliary date of a transaction or posting (*date2* in hledger).

*postdate* <string>
	A metadata key that specifies metadata that should become the date of a posting (*date* in hledger).

# FORMAT

The configuration file uses YAML.

# AUTHORS

Martin Blais, Martin Michlmayr, and others

# SEE ALSO

*beancount2ledger*(1), *ledger*(1), *hledger*(1)

