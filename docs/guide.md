# User guide

## Auxiliary dates

Beancount currently doesn't support ledger's [auxiliary dates](https://www.ledger-cli.org/3.0/doc/ledger3.html#Auxiliary-dates) (or effective dates; also known as [date2 in hledger](https://hledger.org/journal.html#secondary-dates)).

However, beancount2ledger can add auxiliary dates to the ledger output if the information is stored as metadata (either attached to a transaction or a posting).  The `auxdate` variable needs to be defined in the config file, reflecting the key for the metadata information.

For example, given this beancount file:

```beancount
2020-01-01 open Assets:Test

2020-11-13 * "Auxiliary dates"
  aux-date: 2020-11-11
  Assets:Test                           10.00 EUR
    aux-date: 2020-11-11
  Assets:Test
```

and this config file:

```yaml
auxdate: aux-date
```

the following ledger output will be created:

```ledger
account Assets:Test

2020-11-13=2020-11-11 * Auxiliary dates
    Assets:Test                         10.00 EUR  ; [=2020-11-11]
    Assets:Test
```

Output for hledger (using the `-f` option) uses a `date2` tag for postings.

Posting dates (`date` in hledger) are also supported using the `postdate` config variable.

## Links

Since links are not supported in ledger or hledger, they are represented as metadata.

## Lots

Lots are supported and properly converted.

Beancount2ledger contains some logic to work around a [bug in ledger](https://github.com/ledger/ledger/issues/630).

This is a valid beancount transaction:


```beancount
2020-01-01 open Assets:Test

2020-11-13 * "Costs"
  Assets:Test             1 FOO {150.00 EUR}
  Assets:Test             1 FOO {200.00 EUR}
  Assets:Test                   -350.00 EUR
```

However, loading it in ledger will give the error:

```text
Unbalanced remainder is:
         -350.00 EUR
  1 FOO {150.00 EUR}
  1 FOO {200.00 EUR}
Amount to balance against:
  1 FOO {150.00 EUR}
  1 FOO {200.00 EUR}
Error: Transaction does not balance
```

This is because ledger doesn't use the cost to balance a transaction when no price is specified.  Therefore, beancount2ledger will automatically add a price (in addition to the cost) for ledger output when this is needed.

Since lots are not supported in hledger, beancount will convert costs to prices if there's no price information already.

## Metadata

Beancount2ledger will convert metadata correctly.

For ledger output, metadata types other than strings will be converted to [typed metadata](https://www.ledger-cli.org/3.0/doc/ledger3.html#Typed-metadata).  Typed metadata is not supported for hledger.

## Payee and narration

Unlike beancount, ledger does not differentiate between payee and narration.  Therefore, the following syntax is used for ledger's payee field:

```
payee | narration
```

This is also the syntax used by hledger (where narration is called a [note](https://hledger.org/journal.html#payee-and-note)).

## Rounding and tolerance

Beancount handles the tolerance differently to ledger and hledger when balancing transactions.

The following beancount transactions are valid:

```beancount
2010-01-01 open Expenses:Test
2010-01-01 open Assets:Bank

2020-01-10 * "Test"
  Expenses:Test                           4.990 USD
  Assets:Bank                            -4.990 USD

2020-01-10 * "Test: will fail in ledger due to precision of USD"
  Expenses:Test            150.75 THB @ 0.03344 USD
  Assets:Bank                             -5.04 USD
```

They are valid in beancount because each transaction is processed separately and tested against `inferred_tolerance_default`.

Ledger and hledger, on the other hand, infer the tolerance based on all past transactions involving the same currency.  Since the first transaction uses a precision with 3 digits for USD, the same precision is required for the second transaction.  With 3 digits of precision, the second transaction fails to balance because `150.75 * 0.03344` is `5.041` and not `5.04` as specified.  Therefore, beancount2ledger will add rounding postings (using the `Equity:Rounding` account) when needed.

## Transaction codes

Ledger's [transactions codes](https://www.ledger-cli.org/3.0/doc/ledger3.html#Codes) are not supported in beancount.  However, they can be added from metadata if the `code` config variable is specified.

For example, given this beancount file:

```beancount
2020-01-01 open Assets:Test

2020-11-13 * "Code"
  code: 123
  Assets:Test                                  10.00 EUR
  Assets:Test
```

and this config file:

```yaml
code: code
```

the following transaction header will be created:

```ledger
2020-11-13 * (123) Code
```

