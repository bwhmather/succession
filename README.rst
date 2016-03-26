==========
Succession
==========

|build-status| |coverage|

A python library providing a useful abstraction for recording state transitions, compressing them, and distributing to multiple listeners.



Usage
=====

Compression
-----------

The :class:`Succession` class provides a way to reduce long chains of updates
down to a reduced chain with the same effect.

For example, assume that you only care about the sum of the numbers pushed to a
succession, and that it's fine to replace all of the numbers from before you started
listening with the current total.  You can do something like the following:

>>> succession = Succession(compress=lambda items: [sum(items)])
<succession.Succession object at 0x7f5a65a10518>
>>> from_start = succession.iter()
>>> for i in [1, 2, 3, 4, 5]:
...     succession.push(i)
... succession.close()
>>> from_end = succession.iter()
>>> list(from_start)
[1, 2, 3, 4, 5])
>>> list(from_end)
[15]

Iterators forked earlier will not miss any transitions added from the time they
were created.  Compression is only applied to transitions before the fork.


Installation
============
Recommended method is to use the version from `pypi`_

.. code::

    pip install succession


Links
=====
- Source code: https://github.com/bwhmather/succession
- Issue tracker: https://github.com/bwhmather/succession/issues
- Continuous integration: https://travis-ci.org/bwhmather/succession
- PyPI: https://pypi.python.org/pypi/succession


License
=======
The project is licensed under the BSD license.  See `LICENSE`_ for details.


.. |build-status| image:: https://travis-ci.org/bwhmather/succession.png?branch=develop
    :target: https://travis-ci.org/bwhmather/succession
    :alt: Build Status
.. |coverage| image:: https://coveralls.io/repos/bwhmather/succession/badge.png?branch=develop
    :target: https://coveralls.io/r/bwhmather/succession?branch=develop
    :alt: Coverage
.. _pypi: https://pypi.python.org/pypi/sucession
.. _LICENSE: ./LICENSE
