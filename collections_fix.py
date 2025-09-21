# collections_fix.py — compatibility shim
import collections
import collections.abc as _abc

# Restore names older libraries expect
collections.MutableMapping = _abc.MutableMapping
collections.Mapping = _abc.Mapping
collections.Sequence = _abc.Sequence
collections.MutableSequence = _abc.MutableSequence
collections.Iterable = _abc.Iterable
collections.MappingView = _abc.MappingView
