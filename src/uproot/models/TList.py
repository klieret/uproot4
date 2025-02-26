# BSD 3-Clause License; see https://github.com/scikit-hep/uproot4/blob/main/LICENSE

"""
This module defines a versionless model for ``TList``.
"""

from __future__ import absolute_import

import struct

try:
    from collections.abc import Sequence
except ImportError:
    from collections import Sequence

import uproot

_tlist_format1 = struct.Struct(">i")


class Model_TList(uproot.model.Model, Sequence):
    """
    A versionless :doc:`uproot.model.Model` for ``TList``.
    """

    def read_members(self, chunk, cursor, context, file):
        if self.is_memberwise:
            raise NotImplementedError(
                """memberwise serialization of {0}
in file {1}""".format(
                    type(self).__name__, self.file.file_path
                )
            )
        self._bases.append(
            uproot.models.TObject.Model_TObject.read(
                chunk,
                cursor,
                context,
                file,
                self._file,
                self._parent,
                concrete=self.concrete,
            )
        )

        self._members["fName"] = cursor.string(chunk, context)
        self._members["fSize"] = cursor.field(chunk, _tlist_format1, context)

        self._starts = []
        self._data = []
        self._options = []
        self._stops = []
        for _ in uproot._util.range(self._members["fSize"]):
            self._starts.append(cursor.index)
            item = uproot.deserialization.read_object_any(
                chunk, cursor, context, file, self._file, self._parent
            )
            self._data.append(item)
            self._options.append(cursor.bytestring(chunk, context))
            self._stops.append(cursor.index)

    def __repr__(self):
        if self.class_version is None:
            version = ""
        else:
            version = " (version {0})".format(self.class_version)
        return "<{0}{1} of {2} items at 0x{3:012x}>".format(
            self.classname,
            version,
            len(self),
            id(self),
        )

    def __getitem__(self, where):
        return self._data[where]

    def __len__(self):
        return len(self._data)

    @property
    def byte_ranges(self):
        return zip(self._starts, self._stops)

    def tojson(self):
        return {
            "_typename": "TList",
            "name": "TList",
            "arr": [x.tojson() for x in self._data],
            "opt": [],
        }

    writable = True

    def _to_writable_postprocess(self, original):
        self._data = original._data
        self._options = original._options

    def _serialize(self, out, header, name, tobject_flags):
        import uproot._writing

        where = len(out)
        for x in self._bases:
            x._serialize(out, True, None, tobject_flags)

        out.append(uproot._writing.serialize_string(self._members["fName"]))
        out.append(_tlist_format1.pack(self._members["fSize"]))

        for datum, option in zip(self._data, self._options):
            uproot.serialization._serialize_object_any(out, datum, None)
            out.append(option)

        if header:
            num_bytes = sum(len(x) for x in out[where:])
            version = 5
            out.insert(where, uproot.serialization.numbytes_version(num_bytes, version))


uproot.classes["TList"] = Model_TList
