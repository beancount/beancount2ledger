#!/usr/bin/env python

"""
Setup script
"""

import os
import subprocess
import setuptools

def generate_man_pages():
    """Generate man pages from scdoc sources if scdoc is available."""
    man_pages = {
        "docs/beancount2ledger.1": "docs/beancount2ledger.1.scd",
        "docs/beancount2ledger.5": "docs/beancount2ledger.5.scd",
    }
    for output, source in man_pages.items():
        if os.path.exists(output):
            continue
        if not os.path.exists(source):
            continue
        try:
            with open(source, "r") as src, open(output, "w") as dst:
                subprocess.run(["scdoc"], stdin=src, stdout=dst, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # scdoc not available or failed; skip man page generation
            if os.path.exists(output):
                os.remove(output)

def get_data_files():
    """Return data_files list with only man pages that exist."""
    generate_man_pages()
    data_files = []
    if os.path.exists("docs/beancount2ledger.1"):
        data_files.append(("share/man/man1", ["docs/beancount2ledger.1"]))
    if os.path.exists("docs/beancount2ledger.5"):
        data_files.append(("share/man/man5", ["docs/beancount2ledger.5"]))
    return data_files

if __name__ == "__main__":
    setuptools.setup(data_files=get_data_files())
