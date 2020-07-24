[![Build Status](https://travis-ci.org/beancount/beancount2ledger.svg?branch=master)](https://travis-ci.org/beancount/beancount2ledger)

# Beancount2ledger

Beancount2ledger converts files in the [beancount](https://beancount.github.io/) format to either [ledger](https://ledger-cli.org/) or [hledger](https://hledger.org/) output.

# Installation

You can install beancount2ledger with pip:

    pip3 install beancount2ledger

## Usage

Beancount2ledger takes a file argument, loads the file into beancount data structures, and converts the data to ledger output.

You can use the `--format` (`-f`) option to toggle between `ledger` and `hledger` output.

## Documentation

You can [read the documentation online](https://beancount2ledger.readthedocs.io/) thanks to Read the Docs.

