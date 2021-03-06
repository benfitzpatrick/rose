Building & Testing
==================


``rose make-docs``
------------------

The documentation is built by the :ref:`command-rose-make-docs` command. Its
arguments are provided to the sphinx makefile in order.

Build using the ``--strict`` argument before committing changes, this forces a
re-build and will fail if any warnings are raised.

Whenever making changes to the sphinx infrastructure use a clean build e.g:

.. code-block:: bash

   rose make-docs clean html

The following builders are useful for development:

``linkcheck``
   Check external links (internal links are checked by a regular build).
``doctest``
   Run any doctests contained within documented code (e.g. see ``rose.config``).


``rose test-battery``
---------------------

The :ref:`command-rose-test-battery` runs:

* pep8 on the python extensions (``sphinx/ext``).
* ``python2 -m doctest <file>`` for python extensions (``sphinx/ext``).
* eslint on any static javascript files (``sphinx/static/js``).
