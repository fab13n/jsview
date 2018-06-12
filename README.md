Copyright (c) 2016-2018 Fabien Fleutot.

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

# Installation

    pip install jsview

# Usage

```
jsview.py [-h] [-w WIDTH] [-i INDENT] [-o OUTPUT] [-l] [-u] [-r] filename

Format JSON inputs with smart line-returns and indendation.

positional arguments:
  filename              Input file; use '-' to read from stdin

optional arguments:
  -h, --help            show this help message and exit
  -w WIDTH, --width WIDTH
                        Set the ideal width of the output text; if unspecified,
                        try to fit the terminal's width as returned by stty.
  -i INDENT, --indent INDENT
                        Indentation, in number of space characters; default=2
  -o OUTPUT, --output OUTPUT
                        Output file; defaults to stdout
  -l, --close-on-same-line
                        When set, further lines are saved by closing lists and
                        objects on the same line as the last element.
  -u, --utf8-output     Output strings as UTF8 rather than ASCII 7 bits
  -r, --reformat        When set, file content is replaced by a reformatted
                        version. File must not be '-'.
```

# Example

Below is the result of formatting a non-trivial JSON input to 80 characters wide:

```
{
  "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
  "totalFeatures": 116570,
  "type": "FeatureCollection",
  "features": [
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [[-3.59, 48.28], [-3.57, 48.28], [-3.54, 48.28], [-3.53, 48.26],
            [-3.51, 48.25], [-3.49, 48.24], [-3.47, 48.22], [-3.48, 48.21],
            [-3.5, 48.2], [-3.5, 48.18], [-3.48, 48.17], [-3.49, 48.15],
            [-3.52, 48.15], [-3.53, 48.14], [-3.56, 48.14], [-3.58, 48.14],
            [-3.59, 48.15], [-3.58, 48.17], [-3.58, 48.19], [-3.57, 48.21],
            [-3.57, 48.23], [-3.58, 48.25], [-3.6, 48.26], [-3.59, 48.28],
            [-3.59, 48.28]]]
      },
      "properties": {
        "lastrevision": "2016-02-17T15:40:00Z",
        "probability": 0,
        "convectiontype": "ASPOC3D",
        "directiontowards": 90.06896,
        "top": 310,
        "phasetype": null,
        "convectioncelltopvariation": "CONSTANT",
        "intensity": "LIGHT",
        "base": 0,
        "identifier": "OPIC_RADAR.1.201602171540000060_310",
        "speed": 9.1,
        "obsorfcsttime": "2016-02-17T16:40:00Z"
      },
      "type": "Feature",
      "id": "convectionAirm.3449590",
      "geometry_name": "extent"
    }
  ]
}
```
