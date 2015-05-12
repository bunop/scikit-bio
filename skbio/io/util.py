r"""
I/O utils (:mod:`skbio.io.util`)
================================

.. currentmodule:: skbio.io.util

This module provides utility functions to deal with files and I/O in
general.

Functions
---------

.. autosummary::
    :toctree: generated/

    open_file
    open_files

"""

# ----------------------------------------------------------------------------
# Copyright (c) 2013--, scikit-bio development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from future.builtins import bytes, str
from six import BytesIO
import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

from contextlib import contextmanager
from tempfile import gettempdir


def _is_string_or_bytes(s):
    """Returns True if input argument is string (unicode or not) or bytes.
    """
    return isinstance(s, str) or isinstance(s, bytes)


def _get_filehandle(filepath_or, *args, **kwargs):
    """Open file if `filepath_or` looks like a string/unicode/bytes, else
    pass through.
    """
    if _is_string_or_bytes(filepath_or):
        if requests.compat.urlparse(filepath_or).scheme in {'http', 'https'}:
            sess = CacheControl(requests.Session(),
                                cache=FileCache(gettempdir()))
            req = sess.get(filepath_or, **kwargs)

            # if the response is not 200, an exception will be raised
            req.raise_for_status()

            fh, own_fh = BytesIO(req.content), True
        else:
            fh, own_fh = open(filepath_or, *args, **kwargs), True
    else:
        fh, own_fh = filepath_or, False
    return fh, own_fh


@contextmanager
def open_file(filepath_or, *args, **kwargs):
    """Context manager, like ``open``, but lets file handles and file like
    objects pass untouched.

    It is useful when implementing a function that can accept both
    strings and file-like objects (like numpy.loadtxt, etc), with the
    additional benefit that it can load data from an HTTP/HTTPS URL.

    Parameters
    ----------
    filepath_or : str/bytes/unicode string or file-like
        If ``filpath_or`` is a file path to be opened the ``open`` function is
        used and a filehandle is returned. If ``filepath_or`` is a string that
        refers to an HTTP or HTTPS URL, a GET request is created and a BytesIO
        object is returned with the contents of the URL. Else, if a file-like
        object is passed, the object is returned untouched.

    Other parameters
    ----------------
    args, kwargs : tuple, dict
        When `filepath_or` is a string, any extra arguments are passed
        on to the ``open`` builtin. If `filepath_or` is a URL, then only kwargs
        are passed into `requests.get`.

    Notes
    -----
    When files are retrieved from a URL, they are cached in disk inside a
    temporary directory as generated by tempfile.gettempdir.

    Examples
    --------
    >>> with open_file('filename') as f:  # doctest: +SKIP
    ...     pass
    >>> fh = open('filename')             # doctest: +SKIP
    >>> with open_file(fh) as f:          # doctest: +SKIP
    ...     pass
    >>> fh.closed                         # doctest: +SKIP
    False
    >>> fh.close()                        # doctest: +SKIP
    >>> with open_file('http://foo.bar.com/file.fasta') as f: # doctest: +SKIP
    ...     pass

    See Also
    --------
    requests.get

    """
    fh, own_fh = _get_filehandle(filepath_or, *args, **kwargs)
    try:
        yield fh
    finally:
        if own_fh:
            fh.close()


@contextmanager
def open_files(fp_list, *args, **kwargs):
    fhs, owns = zip(*[_get_filehandle(f, *args, **kwargs) for f in fp_list])
    try:
        yield fhs
    finally:
        for fh, is_own in zip(fhs, owns):
            if is_own:
                fh.close()
