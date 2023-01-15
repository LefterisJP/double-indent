# double-indent-rotki

A code formatter to add double indentation to function and method definitions.
Original repository: https://github.com/theendlessriver13/double-indent/

We forked it to add additional functionality that the original author did not want to include upstream: https://github.com/theendlessriver13/double-indent/pull/19


## Installation

`pip install double-indent-rotki`

## usage

```console
usage: double-indent [-h] [-i INDENT] [filenames ...]

positional arguments:
  filenames

optional arguments:
  -h, --help            show this help message and exit
  -i INDENT, --indent INDENT
                        number of spaces for indentation
  --dry-run             do not modify anything, just print if any file would have changes
```

## indent function and method definitions twice

```diff
 def func(
-    arg,
-    arg2,
+        arg,
+        arg2,
 ):
     ...
```

```diff
 class C:
     def __init__(
-        self,
-        arg,
+            self,
+            arg,
     ):
         ...
```
