# Configuration

beancount2ledger can use a configuration file using [YAML](https://yaml.org/) syntax.

It will search for a configuration file in the following order:

* The file specified via the `--config` option
* `.beancount2ledger.yaml` in the current working directory
* `beancount2ledger/config.yaml` in `$XDG_CONFIG_HOME` (that is, usually `$HOME/.config/beancount2ledger/config.yaml`)

## Config options

### General

indent

:   The number of spaces to indent postings (default: 2).

### Information from metadata

auxdate

:   A metadata key that specifies metadata that should become the auxiliary date of a transaction or posting (`date2` in hledger).

postdate
:   A metadata key that specifies metadata that should become the date of a posting (`date` in hledger).

code
:   A metadata key that specifies metadata that should become the code of a transaction.

### Information to metadata

payee-meta

:   A metadata key that specifies where to store the payee of a transaction, instead of using the `payee | narration` syntax (which is the default).

### Mappings

account_map
:   A mapping of beancount account names to ledger account names.

currency_map
:   A mapping of beancount currency names to ledger currency names.
