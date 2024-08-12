""" this project required 'chunked' iterator instead a full module
original code: https://github.com/more-itertools/more-itertools
"""
from functools import partial

from itertools import islice


def take(n, iterable):
    """Return first *n* items of the iterable as a list.

        >>> take(3, range(10))
        [0, 1, 2]

    If there are fewer than *n* items in the iterable, all of them are
    returned.

        >>> take(10, range(3))
        [0, 1, 2]

    """
    return list(islice(iterable, n))


def chunked(iterable, n, strict=False):
    """Break *iterable* into lists of length *n*:

        >>> list(chunked([1, 2, 3, 4, 5, 6], 3))
        [[1, 2, 3], [4, 5, 6]]

    By the default, the last yielded list will have fewer than *n* elements
    if the length of *iterable* is not divisible by *n*:

        >>> list(chunked([1, 2, 3, 4, 5, 6, 7, 8], 3))
        [[1, 2, 3], [4, 5, 6], [7, 8]]

    To use a fill-in value instead, see the :func:`grouper` recipe.

    If the length of *iterable* is not divisible by *n* and *strict* is
    ``True``, then ``ValueError`` will be raised before the last
    list is yielded.

    """
    iterator = iter(partial(take, n, iter(iterable)), [])
    if strict:
        if n is None:
            raise ValueError('n must not be None when using strict mode.')

        def ret():
            for chunk in iterator:
                if len(chunk) != n:
                    raise ValueError('iterable is not divisible by n.')
                yield chunk

        return iter(ret())
    else:
        return iterator
