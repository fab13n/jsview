Copyright (c) 2016 Fabien Fleutot.

This software is made available under the
[MIT public license](https://opensource.org/licenses/MIT).

(Kind-of) smart JSON formatter.

Every JSON formatter I've found inserts newline + indent at every
list item and every object pair. As a result, instead of being
unreadable because it's too large (in a single line), the resulting
JSON is unreadable because too tall (too many newlines), especially
when dealing with formats like GeoJSON where long lists of
coordinates are handled.

This formatter works with a page width in mind, by default 80, and
tries to optimize screen space usage in both width and height.
