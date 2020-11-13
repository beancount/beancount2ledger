# Limitations

## Loss of information

Because of the way beancount2ledger operates, there is some loss of information during the conversion.  Beancount2ledger does not parse the beancount file itself, but instead uses beancount to load the input file into beancount data structures from which ledger output is created.  These data structures don't contain all information from the input file, which means that some information is lost.

This includes:

* Comments: both standalone comments and comments attached to postings are lost.
* Prices and costs: beancount contains prices and costs to per-unit amounts internally, so total prices (`@@`) and costs (`{{...}}`) will be written as per-unit amounts in the output ledger.

## Unsupported features in ledger

Beancount has a number of directives which have no equivalence in ledger.  This includes directives such as `event` and `close`.

Since equivalent directives don't exist, these directives are converted to comments in the ledger output.

