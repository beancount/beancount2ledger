# Release process

* Update `docs/changelog.md`

* Write changes to git:

  ```shell
  git commit -S -m "changelog: timestamp 1.X release"
  ```

* Tag release:

  ```shell
  git tag 1.X -s
  ```

  Use the following format for the commit message:

  ```
  Release beancount2ledger 1.X

  <copy info from docs/changelog.md>
  ```

* Push new tags to GitHub:

  ```shell
  git push github master --tags
  ```

* Go to the [GitHub release page](https://github.com/beancount/beancount2ledger/releases/new) to create a new release:

    * Select the tag
    * Use 1.X as the version
    * Copy release notes from `docs/changelog.md`

* Build and upload the Python package:

  ```shell
  python3 setup.py build
  python3 setup.py sdist bdist_wheel
  twine upload dist/*
  ```

