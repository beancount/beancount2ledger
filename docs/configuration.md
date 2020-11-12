# Configuration

beancount2ledger can use a configuration file using [YAML](https://yaml.org/) syntax.

It will search for a configuration file in the following order:

* The file specified via the `--config` option
* `.beancount2ledger.yaml` in the current working directory
* `beancount2ledger/config.yaml` in `$XDG_CONFIG_HOME` (that is, usually `$HOME/.config/beancount2ledger/config.yaml`)

## Config options

indent

:   The number of spaces to indent postings (default: 2).

