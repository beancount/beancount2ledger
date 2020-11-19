# Limitations

## Loss of information

Because of the way beancount2ledger operates, there is some loss of information during the conversion.  The input file is not converted from beancount to ledger syntax line by line.  Instead, beancount2ledger uses beancount to load the input file into beancount data structures from which ledger output is created.  This means that beancount does certain processing of the input file, such as including files specified via the `include` directive and running beancount plugins (which might modify transactions).  Furthermore, the data structures used by beancount don't contain all information from the input file, which means that some information is lost.

Therefore, there is some degree of loss of information, including:

* Comments: both standalone comments and comments attached to postings are lost.
* Prices and costs: beancount contains prices and costs to per-unit amounts internally, so total prices (`@@`) and costs (`{{...}}`) will be written as per-unit amounts in the output ledger.
* The `pushtag` directive is applied to transactions by beancount, so tags are added to each transaction instead of using ledger's `apply tag` directive.
* Transactions included with the `include` directive are included rather than showing the `include` directive.

## Unsupported features in ledger

### Flags

Beancount supports a wide range of flags whereas ledger only allows `*` and `!`.  Flags which are not supported in ledger are therefore removed.

### Directives

Beancount has a number of directives which have no equivalence in ledger.  This includes directives such as `event` and `close`.

Since equivalent directives don't exist, these directives are converted to comments in the ledger output.

### Inline math

Inline math is evaluated and the calculated amount is written to the ledger file rather than the original inline math.

