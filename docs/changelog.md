# Beancount2ledger releases

## 1.2 (2020-07-25)

* Quote commodities containing minus/dash (`-`) ([issue #15](https://github.com/beancount/beancount2ledger/issues/15))
* Turn multi-line strings into a single line ([issue #17](https://github.com/beancount/beancount2ledger/issues/17))
* Ensure flags are valid in ledger ([issue #20](https://github.com/beancount/beancount2ledger/issues/20))
* Show amounts only when they are specified in the source file ([issue #10](https://github.com/beancount/beancount2ledger/issues/10))
* Fix crash with very long account names ([issue #19](https://github.com/beancount/beancount2ledger/issues/19))
* Fix crash when entry.meta or entry.posting are not set ([issue #16](https://github.com/beancount/beancount2ledger/issues/16))
* Use account declarations for hledger

## 1.1 (2020-07-24)

* Preserve metadata information ([issue #3](https://github.com/beancount/beancount2ledger/issues/3))
* Preserve cost information (lot dates and lot labels/notes) ([issue #5](https://github.com/beancount/beancount2ledger/issues/5))
* Avoid adding two prices in hledger ([issue #2](https://github.com/beancount/beancount2ledger/issues/2))
* Avoid trailing whitespace in account open declarations ([issue #6](https://github.com/beancount/beancount2ledger/issues/6))
* Fix indentation issue in postings ([issue #8](https://github.com/beancount/beancount2ledger/issues/8))
* Fix indentation issue in price entries
* Drop time information from price (`P`) entries
* Add documentation
* Relicense under GPL-2.0-or-later ([issue #1](https://github.com/beancount/beancount2ledger/issues/1))

## 1.0 (2020-07-22)

* Split ledger and hledger conversion from `bean-report` into a standalone tool
* Add man page for `beancount2ledger`(1)

