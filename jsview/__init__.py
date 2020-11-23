#!/usr/bin/env python2.7
#
# Copyright (c) 2016-2018 Fabien Fleutot.
#
# This software is made available under the [MIT public
# license](https://opensource.org/licenses/MIT).
#
# (Kind-of) smart JSON formatter.
#
# Every JSON formatter I've found inserts newline + indent at every
# list item and every object pair. As a result, instead of being
# unreadable because it's too large (in a single line), the resulting
# JSON is unreadable because too tall (too many newlines), especially
# when dealing with formats like GeoJSON where long lists of
# coordinates are handled.
#
# This formatter works with a page width in mind, by default 80, and
# tries to optimize screen space usage in both width and height.

import os
import sys
import json
from numbers import Number
from argparse import ArgumentParser

if sys.version_info.major == 2:
    from collections import Hashable, OrderedDict
else:
    from collections.abc import Hashable
    OrderedDict = dict

name = "jsview"
__version__ = "1.2"

# default width, if it's not specified and we fail to retrieve it from `stty`.
DEFAULT_WIDTH = 80


class Memo(object):
    """
    Quick and dirty memoization utility. Works on objects and lists as
    long as no-one tries to modify them for the duration of the
    memoization process.
    """
    def __init__(self):
        self.hashable_cache = {}
        self.non_hashable_cache = {}

    def get(self, x):
        if isinstance(x, Hashable): return self.hashable_cache.get(x, None)
        else: return self.non_hashable_cache.get(id(x), None)

    def set(self, x, y):
        if isinstance(x, Hashable): self.hashable_cache[x] = y
        else: self.non_hashable_cache[id(x)] = y


def memo(f):
    """
    Decorator to turn functions into memoized functions.
    """
    M = Memo()
    def mf(x):
        y = M.get(x)
        if y is not None:
            return y
        else:
            y = f(x)
            M.set(x, y)
            return y
    return mf

def strip_final_spaces(buffer):
    """
    Trim spaces, if any, at the end of a buffer (list of string
    fragments).  This is intended to avoid spaces just before a
    newline.
    """
    if len(buffer) > 0:
        buffer[-1] = buffer[-1].rstrip()

def tobuffer(x, buffer=[], width=80, indent=2, close_on_same_line=False,
             utf8_output=False, with_boring_lists=True, cls=None):
    """
    Write some JSON content, smartly indented, into a buffer (list of
    strings). Take into account:

    * the intended page width, in characters, which it will try not to
      overflow;
    * the number of spaces to use for indentation;
    * whether a few further lines should be saved by putting closing
      "]" and "}" characters on the same line as the last element of a
      list / object;
    * Whether strings should be output with "backslash-u" ASCII 7 bits
      encoding, as as UTF8.

    Return the buffer as a result.
    """

    encoder = cls() if cls is not None else None

    None  # Will be filled with an instance of `cls` if needed.
    
    @memo
    def one_line_size(x):
        """
        Number of characters which would be taken by a JSON fragment
        if it were printed as a single line.  Since a block's size
        will be asked again and again (as its computation is a subpart
        of the computation of all of its superblocks), results are
        memoized.
        """
        if isinstance(x, dict):
            # each pair has a ": ", each pair but the last has a ", ",
            # and there's a surrounding "{}" => the missing last ", "
            # is cancelled by the "{}"
            return sum(one_line_size(key) + one_line_size(value) + 4 for key, value in x.items())
        elif isinstance(x, list):
            # the extra final ", " cancels the surrounding "[]"
            return sum(one_line_size(y) + 2 for y in x)
        else:
           return len(json.dumps(x, cls=cls))

    @memo
    def is_boring_list(x):
        """
        Determine whether `x` is a boring list.

        A "boring" list is one which should take as little vertical
        space as possible, even if it won't fit in a single list. In
        other words, it should be formatted like a paragraph, not as
        either a single line or a single column. Elements should be
        pushed as indented lines of as many elements as possible, each
        line going as far right as possible without breaking the
        width.

        Notice that this question of boringness only makes sense for
        lists which wouldn't fit on a single line.

        For now, this only applies to (possibly nested) lists of
        numbers.
        """
        if not with_boring_lists or not isinstance(x, list):
            return False
        for y in x:
            if not isinstance(y, Number) and y is not None and not is_boring_list(y): return False
        return True

    def parse(x, one_line, current_indent, current_offset, width):
        """
        Main recursive function.

        * `x`: the JSON object to be dumped in buffer;
        * `one_line`: when true, we know without further verification
          that x must be written on a single line;
        * `current_indent`: current level of nesting in surrounding
          objects/lists;
        * `current_offset`: index of the first character to dump in
          the line (in other words, its initial X coordinate);
        * `width`: intended page width.

        Returns the offset at the end of the buffer (might be less
        than `current_offset` if line breaks have been added).
        """
        if isinstance(x, dict):
            # Item are stored because `json.loads` was hooked with a `collections.OrderedDict`.
            sorted_items = x.items()
            if not x:  # Empty object
                buffer.append("{}")
                return current_offset+2
            elif one_line or not bool(x) or current_offset + one_line_size(x) <= width:  # Single-line object
                buffer.append("{")
                current_offset += 1
                for key, value in sorted_items:
                    current_offset = parse(key, True, current_indent+1, current_offset, width)
                    buffer.append(": ")
                    current_offset = parse(value, True, current_indent+1, current_offset, width)
                    buffer.append(", ")
                buffer.pop()  # remove last ", "
                buffer.append("}")
                return current_offset - 1  # "}" is one character shorter than ", "
            else:  # Object, newline for each pair
                buffer.append("{")
                inner_offset = indent * (current_indent+1)
                new_line_and_indent = "\n" + " " * inner_offset
                for key, value in sorted_items:
                    strip_final_spaces(buffer)
                    buffer.append(new_line_and_indent)
                    current_offset = parse(key, False, current_indent+1, inner_offset, width)
                    buffer.append(": ")
                    parse(value, False, current_indent+1, current_offset+2, width)
                    buffer.append(", ")
                buffer.pop()
                if not close_on_same_line:
                    strip_final_spaces(buffer)
                    buffer.append("\n")
                    buffer.append(" " * (current_indent * indent))
                buffer.append("}")
                return current_indent * indent + 1
        elif isinstance(x, list):
            if not x:  # Empty list
                buffer.append("[]")
                return current_offset+2
            elif one_line or not bool(x) or current_offset + one_line_size(x) <= width:  # Single-line list
                buffer.append("[")
                current_offset += 1
                for y in x:
                    current_offset = parse(y, True, current_indent+1, current_offset, width) + 2
                    buffer.append(", ")
                buffer.pop()  # remove last ", "
                buffer.append("]")
                return current_offset - 1  # "]" is one character shorter than ", "
            elif is_boring_list(x):  # Multi-line list, but still as many elements as possible per line
                buffer.append("[")
                current_offset += 1
                inner_offset = indent * (current_indent+1)
                new_line_and_indent = "\n" + " " * inner_offset
                for y in x:
                    if current_offset != None and current_offset + one_line_size(y) + 2 >= width:
                        # Next element won't fit on current line
                        strip_final_spaces(buffer)
                        buffer.append(new_line_and_indent)
                        current_offset = inner_offset
                    current_offset = parse(y, False, current_indent+1, current_offset, width-2)
                    buffer.append(", ")
                    current_offset += 2
                buffer.pop()
                buffer.append("]")
                return current_offset - 1 # Replaced ", " with "]"
            else:  # One-element-per-line list
                buffer.append("[")
                inner_offset = indent * (current_indent+1)
                new_line_and_indent = "\n" + " " * inner_offset
                for y in x:
                    strip_final_spaces(buffer)
                    buffer.append(new_line_and_indent)
                    last_element_offset = parse(y, False, current_indent+1, inner_offset, width-2)
                    buffer.append(", ")
                buffer.pop()
                if close_on_same_line:
                    buffer.append("]")
                    return last_element_offset + 1
                else:
                    strip_final_spaces(buffer)
                    buffer.append("\n")
                    buffer.append(" " * (current_indent * indent))
                    buffer.append("]")
                    return current_indent * indent + 1
        else:  # Non-compound element
            try:
                if utf8_output and sys.version_info.major == 3:
                    r = json.dumps(x, ensure_ascii=False)
                elif utf8_output and isinstance(x, unicode):
                    r = json.dumps(x, ensure_ascii=False).encode('utf8')
                else:
                    r = json.dumps(x)
            except TypeError:  # Try with custom encoding class, if provided
                if encoder is None:
                    raise
                else:
                    r = encoder.encode(x)
            buffer.append(r)
            return current_offset + len(r)
    parse(x, False, 0, 0, width)
    return buffer


def dump(obj, fp, width=80, indent=2, close_on_same_line=False,
         utf8_output=False, with_boring_lists=True, cls=None):
    """
    Dump value `obj` as smartly indented JSON in file-like object `fp`.

    @param obj object to dump
    @param fp file-like object where JSON is written
    @param width tentative output lines width in characters
    @param indent indentation, in number of space characters
    @param close_on_same_line if true, closing braces and brackets are on the same line as last item,
           even if items are on separate lines.
    @param utf8_output if true, use unicode characters as output rather than backslash+u escape sequences
    @param with_boring_lists if true, possibly-nested series of numbers are packed on as few lines
           as possible while respecting the width limitation.
    """
    buffer = tobuffer(obj, [], width, indent, close_on_same_line, utf8_output, with_boring_lists, cls)
    for fragment in buffer:
        fp.write(fragment)
    fp.write("\n")


def dumps(obj, width=80, indent=2, close_on_same_line=False,
          utf8_output=False, with_boring_lists=True, cls=None):
    """
    Dump value `obj` as smartly indented JSON as a string.

    @param obj object to dump
    @param fp file-like object where JSON is written
    @param width tentative output lines width in characters
    @param indent indentation, in number of space characters
    @param close_on_same_line if true, closing braces and brackets are on the same line as last item,
           even if items are on separate lines.
    @param utf8_output if true, use unicode characters as output rather than backslash+u escape sequences
    @param with_boring_lists if true, possibly-nested series of numbers are packed on as few lines
           as possible while respecting the width limitation.
    @return the JSON string.
    """
    # TODO use cls if not None
    buffer = tobuffer(obj, [], width, indent, close_on_same_line, utf8_output, with_boring_lists, cls)
    return "".join(buffer)


# Call from command line
def main():
    parser = ArgumentParser(description="Format JSON inputs with smart line-returns and indendation.")
    parser.add_argument('-w', '--width', default=0,
                        help="Set the ideal width of the output text; default=80")
    parser.add_argument('-i', '--indent', default=2,
                        help="Indentation, in number of space characters; default=2")
    parser.add_argument('-o', '--output',
                        help="Output file; defaults to stdout")
    parser.add_argument('-l', '--close-on-same-line', action='store_const', const=True, default=False,
                        help="When set, further lines are saved by closing lists and objects on the same\
                              line as the last element.")
    parser.add_argument('-b', '--no-boring-lists', action='store_const', const=True, default=False,
                        help="When set, boring lists (possibly nested lists of numbers) are not compacted.")
    parser.add_argument('-u', '--utf8-output', action='store_const', const=True, default=False,
                        help="Output strings as UTF8 rather than ASCII 7 bits")
    parser.add_argument('-r', '--reformat', action='store_const', const=True, default=False,
                        help="When set, file content is replaced by a reformatted version. File must not be '-'.")
    parser.add_argument('filename', help="Input file; use '-' to read from stdin.")

    # Agruments parsing
    args = parser.parse_args()
    width = int(args.width)
    if width == 0:
        try:
            # `stty size` should return the current numbers of rows and columns of the terminal, separated by a space.
            from subprocess import Popen, PIPE
            p = Popen(['stty', 'size'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode == 0:
                rows, columns = (int(x) for x in stdout.split())
                width = columns
            else:  # Error during stty execution, can't get temrinal size
                width = DEFAULT_WIDTH
        except Exception:  # stty failed for some reason (not found, not in a terminal...)
            width = DEFAULT_WIDTH
    f = open(args.filename) if args.filename != "-" else sys.stdin
    with f:
        content_string = f.read()
    try:
        content = json.loads(content_string, object_pairs_hook=OrderedDict)
    except Exception as e:  # Exception type differs between python 2/3
        sys.stderr.write("Invalid JSON input: %s\n" % str(e))
        exit(-2)

    # Main call
    buffer = tobuffer(content, [], width, int(args.indent),
                      args.close_on_same_line, args.utf8_output,
                      not args.no_boring_lists)

    # Choose and open output channel
    if args.reformat:
        if args.filename == "-":
            sys.stderr.write("Cannot reformat from stdin\n");
            exit(-1)
        else:
            g = open(args.filename, "w")
    elif args.output:
        g = open(args.output, "w")
    else:
        g = sys.stdout

    with g:
        for fragment in buffer:
            g.write(fragment)
        g.write('\n')

    if args.reformat:
        print("Reformatted file %s" % args.filename)

if __name__ == "__main__":
    main()
