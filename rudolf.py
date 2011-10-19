"""Color output plugin for the nose testing framework.

Use ``nosetests --with-color`` (no "u"!) to turn it on.

http://en.wikipedia.org/wiki/Rudolph_the_Red-Nosed_Reindeer

"Rudolph the Red-Nosed Reindeer" is a popular Christmas story about Santa
Claus' ninth and lead reindeer who possesses an unusually red colored nose that
gives off its own light that is powerful enough to illuminate the team's path
through inclement weather.


Copyright 2007 John J. Lee <jjl@pobox.com>

This code is derived from zope.testing version 3.5.0, which carries the
following copyright and licensing notice:

##############################################################################
#
# Copyright (c) 2004-2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

import binascii
import doctest
import os
import re
import sys
import time
import traceback
import unittest
import warnings

import nose.config
import nose.core
import nose.plugins
import nose.util

# TODO
# syntax-highlight traceback Python source lines


__version__ = "0.3"
__revision__ = "$Id: rudolf.py 49867 2007-12-17 13:55:54Z jjlee $"


# some of this ANSI/xterm colour stuff is based on public domain code by Ian
# Ward

CUBE_START = 16  # first index of colour cube
CUBE_SIZE = 6  # one side of the colour cube
GRAY_START = CUBE_SIZE ** 3 + CUBE_START
# values copied from xterm 256colres.h:
CUBE_STEPS = 0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff
GRAY_STEPS = (0x08, 0x12, 0x1c, 0x26, 0x30, 0x3a, 0x44, 0x4e, 0x58, 0x62,
              0x6c, 0x76, 0x80, 0x84, 0x94, 0x9e, 0xa8, 0xb2, 0xbc, 0xc6, 0xd0,
              0xda, 0xe4, 0xee)
TABLE_START = CUBE_START  # don't use the basic 16 colours, since we can't be
                          # sure what their RGB values are
TABLE_END = 256


def xterm_from_rgb_string(rgb_text):
    """
    >>> xterm_from_rgb_string("000000")
    16
    >>> xterm_from_rgb_string("FF0000")
    196

    >>> xterm_from_rgb_string("0000")
    Traceback (most recent call last):
    ValueError: 0000
    >>> xterm_from_rgb_string("blah")
    Traceback (most recent call last):
    ValueError: blah
    """
    try:
        bytes = binascii.unhexlify(rgb_text)
    except TypeError:
        raise ValueError(rgb_text)
    if len(bytes) < 3:
        raise ValueError(rgb_text)
    rgb = map(ord, bytes)
    return xterm_from_rgb(rgb)


def cube_vals(n):
    """Return the cube coordinates for colour-number n."""
    assert n >= CUBE_START and n < GRAY_START
    val = n - CUBE_START
    c = val % CUBE_SIZE
    val = val / CUBE_SIZE
    b = val % CUBE_SIZE
    a = val / CUBE_SIZE
    return a, b, c


def rgb_from_xterm(n):
    """Return the red, green and blue components of colour-number n.
    Components are between 0 and 255."""
    # we don't handle the basic 16 colours, since we can't be sure what their
    # RGB values are
    assert n >= CUBE_START
    if n < GRAY_START:
        return [CUBE_STEPS[v] for v in cube_vals(n)]
    return (GRAY_STEPS[n - GRAY_START],) * 3


RGB_FROM_XTERM_COLOR = [
    rgb_from_xterm(xi) for xi in range(TABLE_START, TABLE_END)]


def xterm_from_rgb(rgb):
    smallest_distance = sys.maxint
    for index in range(0, TABLE_END - TABLE_START):
        rc = RGB_FROM_XTERM_COLOR[index]
        dist = ((rc[0] - rgb[0]) ** 2 +
                (rc[1] - rgb[1]) ** 2 + 
                (rc[2] - rgb[2]) ** 2)
        if dist < smallest_distance:
            smallest_distance = dist
            best_match = index
    return best_match + TABLE_START


class Xterm256Color(object):

    def __init__(self, xterm_color_code):
        self._code = xterm_color_code

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._code)

    def terminal_code(self):
        return "\033[38;5;%dm" % self._code


class Ansi16Color(object):

    def __init__(self, foreground_color, bright):
        self._fg_color = foreground_color
        self._bright = bright

    def __str__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               self._fg_color, self._bright)

    def terminal_code(self):
        if self._fg_color is None:
            fg_code = 0
        else:
            fg_code = self._fg_color + 30
        if self._bright is None:
            prefix_code = ""
        elif self._bright:
            prefix_code = "1;"
        else:
            prefix_code = "0;"
        return "\033[%s%sm" % (prefix_code, fg_code)


def parse_color(color_text):
    """
    Names for the 16 ANSI colours

    >>> print parse_color("black")
    Ansi16Color(0, None)
    >>> print parse_color("red")
    Ansi16Color(1, None)
    >>> print parse_color("darkred")
    Ansi16Color(1, False)
    >>> print parse_color("lightred")
    Ansi16Color(1, True)
    >>> print parse_color("brightred")
    Ansi16Color(1, True)
    >>> print parse_color("boldred")
    Ansi16Color(1, True)

    RGB colours

    >>> print parse_color("rgb(ff0000)")
    Xterm256Color(196)
    >>> print parse_color("rgb(FF0000)")
    Xterm256Color(196)

    xterm colour codes

    >>> print parse_color("0")
    Xterm256Color(0)
    >>> print parse_color("140")
    Xterm256Color(140)

    Bad colours

    >>> parse_color("moored")
    Traceback (most recent call last):
    ValueError: Bad named colour: 'moored'
    >>> parse_color("boldpink")
    Traceback (most recent call last):
    ValueError: Bad named colour: 'boldpink'
    >>> parse_color("256")
    Traceback (most recent call last):
    ValueError: Bad xterm colour: '256'
    >>> parse_color("-1")
    Traceback (most recent call last):
    ValueError: Bad xterm colour: '-1'
    >>> parse_color("ff0000")
    Traceback (most recent call last):
    ValueError: Bad named colour: 'ff0000'
    >>> parse_color("rgb(fg0000)")
    Traceback (most recent call last):
    ValueError: Bad RGB colour: 'rgb(fg0000)'
    >>> parse_color("rgb(ff0000f)")
    Traceback (most recent call last):
    ValueError: Bad RGB colour: 'rgb(ff0000f)'
    >>> parse_color("rgb(0000)")
    Traceback (most recent call last):
    ValueError: Bad RGB colour: 'rgb(0000)'
    """
    assert color_text

    # RGB
    if color_text.startswith("rgb(") and color_text.endswith(")"):
        try:
            xc = xterm_from_rgb_string(color_text[4:-1])
        except ValueError:
            raise ValueError("Bad RGB colour: %r" % color_text)
        else:
            return Xterm256Color(xc)

    # xterm 256 colour code
    try:
        xc = int(color_text)
    except ValueError:
        pass
    else:
        if 0 <= xc < 256:
            return Xterm256Color(xc)
        else:
            raise ValueError("Bad xterm colour: %r" % color_text)

    # named ANSI 16 colour
    colorcodes = {"default": None, "normal": None,
                  "black": 0,
                  "red": 1,
                  "green": 2,
                  "brown": 3, "yellow": 3,
                  "blue": 4,
                  "magenta": 5,
                  "cyan": 6,
                  "grey": 7, "gray": 7, "white": 7}
    prefixes = [("dark", False),
                ("light", True),
                ("bright", True),
                ("bold", True)]
    is_bright = None
    remaining = color_text
    for prefix, bright in prefixes:
        if remaining.startswith(prefix):
            remaining = color_text[len(prefix):]
            is_bright = bright
            break
    try:
        foreground = colorcodes[remaining]
    except KeyError:
        raise ValueError("Bad named colour: %r" % color_text)
    return Ansi16Color(foreground, is_bright)


def parse_colorscheme(colorscheme):
    """
    >>> colors = parse_colorscheme("fail=red,pass=rgb(00ff00),error=40")
    >>> for name, color in sorted(colors.items()):
    ...     print "%s: %s" % (name, color)
    error: Xterm256Color(40)
    fail: Ansi16Color(1, None)
    pass: Xterm256Color(46)

    >>> parse_colorscheme("fail:red,pass=green")
    Traceback (most recent call last):
    ValueError: Missing equals (name=colour): 'fail:red'
    >>> parse_colorscheme("fail=spam")
    Traceback (most recent call last):
    ValueError: Bad named colour: 'spam'
    >>> parse_colorscheme("fail=")
    Traceback (most recent call last):
    ValueError: Missing colour (name=colour): 'fail='
    """
    if not colorscheme:
        return {}

    colors = {}
    specs = colorscheme.split(",")
    for spec in specs:
        try:
            name, color_text = spec.split("=", 1)
        except ValueError:
            raise ValueError("Missing equals (name=colour): %r" % spec)
        if color_text == "":
            raise ValueError("Missing colour (name=colour): %r" % spec)
        colors[name] = parse_color(color_text)
    return colors


def normalize_path(pathname):
    if hasattr(os.path, "realpath"):
        pathname = os.path.realpath(pathname)
    return os.path.normcase(os.path.abspath(pathname))


def relative_location(basedir, target, posix_result=True):
    """
    >>> relative_location("/a/b/", "/a/b/c")
    'c'
    >>> relative_location("a/b", "a/b/c/d")
    'c/d'
    >>> relative_location("/z", "/a/b")
    '../a/b'

    >>> this_dir = os.path.dirname(normalize_path(__file__))
    >>> relative_location("/a/b/", "a/b/c") == "../.." + this_dir + "/a/b/c"
    True

    >>> nr_dirs_up_to_root = os.path.join(this_dir, "a", "b").count(os.sep)
    >>> expected = "/".join([".."] * nr_dirs_up_to_root) + "/a/b/c/d"
    >>> relative_location("a/b", "/a/b/c/d/") == expected
    True
    """
    # based on a function by Robin Becker
    import os.path, posixpath
    basedir = normalize_path(basedir)
    target = normalize_path(target)
    baseparts = basedir.split(os.sep)
    targetparts = target.split(os.sep)
    nr_base = len(baseparts)
    nr_target = len(targetparts)
    nr_common = min(nr_base, nr_target)
    ii = 0
    while ii < nr_common and baseparts[ii] == targetparts[ii]:
        ii += 1
    relative_parts = (nr_base-ii)*['..'] + targetparts[ii:]
    if posix_result:
        return posixpath.join(*relative_parts)
    else:
        return os.path.join(*relative_parts)


def elide_foreign_path_and_line_nr(base_dir, path, line_nr):
    relpath = relative_location(base_dir, path)
    if ".." in relpath:
        filename = os.path.basename(relpath)
        return os.path.join("...", filename), "..."
    else:
        return relpath, line_nr


class DocTestFailureException(AssertionError):
    """Custom exception for doctest unit test failures."""


# colour output code taken from zope.testing, and hacked

class ColorfulOutputFormatter(object):
    """Output formatter that uses ANSI color codes.

    Like syntax highlighting in your text editor, colorizing
    test failures helps the developer.
    """

    separator1 = "=" * 70
    separator2 = "-" * 70

    doctest_template = """
File "%s", line %s, in %s

%s
Want:
%s
Got:
%s
"""

    # Map prefix character to color in diff output.  This handles ndiff and
    # udiff correctly, but not cdiff.
    diff_color = {"-": "expected-output",
                  "+": "actual-output",
                  "?": "character-diffs",
                  "@": "diff-chunk",
                  "*": "diff-chunk",
                  "!": "actual-output",}

    def __init__(self, verbosity, descriptions, colorscheme,
                 stream=sys.stdout, clean_tracebacks=False, base_dir=False):
        self._stream = stream
        self._verbose = bool(verbosity)
        self._show_all = verbosity > 1
        self._dots = verbosity == 1
        self._descriptions = descriptions
        self._clean_tracebacks = clean_tracebacks
        self._base_dir = base_dir
        self._colorscheme = colorscheme
#         for name, value in self._colorscheme.items():
#             print >>sys.stderr, '%s = %s' % (name, value)

    def color(self, what):
        """Pick a named color from the color scheme"""
        return self._colorscheme[what].terminal_code()

    def colorize(self, what, message, normal="normal"):
        """Wrap message in color."""
        return self.color(what) + message + self.color(normal)

    def get_description(self, test):
        if self._descriptions:
            return test.shortDescription() or str(test)
        else:
            return str(test)

    def start_test(self, test):
        if self._show_all:
            self._stream.write(self.colorize("normal",
                                             self.get_description(test)))
            self._stream.write(self.colorize("normal", " ... "))
        self._stream.flush()

    def test_success(self, test):
        if self._show_all:
            self._stream.writeln(self.colorize("pass", "ok"))
        elif self._dots:
            self._stream.write(self.colorize("pass", "."))

    def test_error(self, test, exc_info, label):
        if self._show_all:
            self._stream.writeln(self.colorize("error", label))
        elif self._dots:
            self._stream.write(self.colorize("error", label[:1]))

    def test_skip(self, label):
        if self._show_all:
            self._stream.writeln(self.colorize("skip", label))
        elif self._dots:
            self._stream.write(self.colorize("skip", label[:1]))

    def test_failure(self, test, exc_info):
        if self._show_all:
            self._stream.writeln(self.colorize("failure", "FAIL"))
        elif self._dots:
            self._stream.write(self.colorize("failure", "F"))

    def print_error_list(self, flavour, errors):
        problem_color = {
            "FAIL": "failure",
            "SKIP": "skip"
        }.get(flavour, "error")
        for tup in errors:
            test, err = tup[:2]
            try:
                err_type = tup[2]
            except IndexError:
                err_type = None
            # Handle skip message
            skip_msg = ""
            if flavour == "SKIP":
                reason = getattr(err, "message", None)
                if reason:
                    skip_msg = " (%s)" % self.colorize("skip", reason)
            self._stream.writeln(self.separator1)
            self._stream.writeln("%s: %s%s" % (
                    self.colorize(problem_color, flavour),
                    self.colorize("testname", self.get_description(test)),
                    skip_msg
            ))
            if flavour != "SKIP":
                self._stream.writeln(self.separator2)
                self.print_traceback(err, err_type)

    def print_summary(self, success, summary, tests_run, start, stop):
        write = self._stream.write
        writeln = self._stream.writeln
        writelines = self._stream.writelines
        taken = float(stop - start)
        plural = tests_run != 1 and "s" or ""
        count_color = success and "ok-number" or "error-number"

        writeln(self.separator2)
        writelines([
                "Ran ",
                self.colorize(count_color, "%s " % tests_run),
                "test%s in " % plural,
                self._format_seconds(taken)])
        writeln()
        if not success:
            write(self.colorize("failure", "FAILED"))
            write(" (")
            any = False
            for label, count in summary.items():
                if not count:
                    continue
                if any:
                    write(", ")
                write("%s=" % label)
                problem_color = (label == "failures") and "failure" or "error"
                write(self.colorize(problem_color, str(count)))
                any = True
            writeln(")")
        else:
            writeln(self.colorize("pass", "OK"))

    def _format_seconds(self, n_seconds, normal="normal"):
        """Format a time in seconds."""
        if n_seconds >= 60:
            n_minutes, n_seconds = divmod(n_seconds, 60)
            return "%s minutes %s seconds" % (
                        self.colorize("number", "%d" % n_minutes, normal),
                        self.colorize("number", "%.3f" % n_seconds, normal))
        else:
            return "%s seconds" % (
                        self.colorize("number", "%.3f" % n_seconds, normal))

    def format_traceback(self, exc_info):
        """Format the traceback."""
        v = exc_info[1]
        if isinstance(v, DocTestFailureException):
            tb = v.args[0]
        if isinstance(v, doctest.DocTestFailure):
            # XXX
#             if self._clean_tracebacks:
#                 filename, lineno = elide_foreign_path_and_line_nr(
#                     self._base_dir,
#                     v.test.filename,
#                     (v.test.lineno + v.example.lineno + 1))
            tb = self.doctest_template % (
                v.test.filename,
                v.test.lineno + v.example.lineno + 1,
                v.test.name,
                v.example.source,
                v.example.want,
                v.got,
                )
        else:
            tb = "".join(traceback.format_exception(*exc_info))
        return tb

    def print_traceback(self, formatted_traceback, err_type):
        """Report an error with a traceback."""
        if issubclass(err_type, DocTestFailureException):
            self.print_doctest_failure(formatted_traceback)
        else:
            self.print_colorized_traceback(formatted_traceback)
            print >>self._stream

    def print_doctest_failure(self, formatted_failure):
        """Report a doctest failure.

        ``formatted_failure`` is a string -- that's what
        DocTestSuite/DocFileSuite gives us.
        """
        color_of_indented_text = 'normal'
        colorize_diff = False
        colorize_exception = False
        lines = formatted_failure.splitlines()

        # this first traceback in a doctest failure report is rarely
        # interesting, but it looks funny non-colourized so let's colourize it
        # anyway
        exc_lines = []
        while True:
            line = lines.pop(0)
            if line == self.separator2:
                break
            exc_lines.append(line)
        self.print_colorized_traceback("\n".join(exc_lines))
        print >>self._stream
        print >>self._stream, self.separator2
        exc_lines = []

        for line in lines:
            if line.startswith('File '):
                m = re.match(r'File "(.*)", line (\d*), in (.*)$', line)
                if m:
                    filename, lineno, test = m.groups()
                    if self._clean_tracebacks:
                        filename, lineno = elide_foreign_path_and_line_nr(
                            self._base_dir, filename, lineno)
                    self._stream.writelines([
                        self.color('normal'), 'File "',
                        self.color('filename'), filename,
                        self.color('normal'), '", line ',
                        self.color('lineno'), lineno,
                        self.color('normal'), ', in ',
                        self.color('testname'), test,
                        self.color('normal'), '\n'])
                else:
                    print >>self._stream, line
            elif line.startswith('    '):
                if colorize_diff and len(line) > 4:
                    color = self.diff_color.get(line[4],
                                                color_of_indented_text)
                    print >>self._stream, self.colorize(color, line)
                elif colorize_exception:
                    exc_lines.append(line[4:])
                else:
                    print >>self._stream, self.colorize(color_of_indented_text,
                                                        line)
            else:
                colorize_diff = False
                if colorize_exception:
                    self.print_colorized_traceback("\n".join(exc_lines),
                                                   indent_level=1)
                    colorize_exception = False
                    exc_lines = []
                if line.startswith('Failed example'):
                    color_of_indented_text = 'failed-example'
                elif line.startswith('Expected:'):
                    color_of_indented_text = 'expected-output'
                elif line.startswith('Got:'):
                    color_of_indented_text = 'actual-output'
                elif line.startswith('Exception raised:'):
                    color_of_indented_text = 'exception'
                    colorize_exception = True
                elif line.startswith('Differences '):
                    if line in [
                        "Differences (ndiff with -expected +actual):",
                        "Differences (unified diff with -expected +actual):"
                        ]:
                        line = "".join([
                                "Differences (ndiff with ",
                                self.color("expected-output"), "-expected ",
                                self.color("actual-output"), "+actual",
                                self.color("normal"), "):",
                                ])
                    color_of_indented_text = 'normal'
                    colorize_diff = True
                else:
                    color_of_indented_text = 'normal'
                print >>self._stream, line
        print >>self._stream

    def print_colorized_traceback(self, formatted_traceback, indent_level=0):
        """Report a test failure.

        ``formatted_traceback`` is a string.
        """
        indentation = "    " * indent_level
        for line in formatted_traceback.splitlines():
            if line.startswith("  File"):
                m = re.match(r'  File "(.*)", line (\d*)(?:, in (.*))?$', line)
                if m:
                    filename, lineno, test = m.groups()
                    if self._clean_tracebacks:
                        filename, lineno = elide_foreign_path_and_line_nr(
                            self._base_dir, filename, lineno)
                    tb_lines = [
                        self.color("normal"), '  File "',
                        self.color("filename"), filename,
                        self.color("normal"), '", line ',
                        self.color("lineno"), lineno,
                        ]
                    if test:
                        # this is missing for the first traceback in doctest
                        # failure report
                        tb_lines.extend([
                                self.color("normal"), ", in ",
                                self.color("testname"), test,
                                ])
                    tb_lines.extend([
                            self.color("normal"), "\n",
                                    ])
                    self._stream.write(indentation)
                    self._stream.writelines(tb_lines)
                else:
                    print >>self._stream, indentation + line
            elif line.startswith("    "):
                print >>self._stream, self.colorize("failed-example",
                                                    indentation + line)
            elif line.startswith("Traceback (most recent call last)"):
                print >>self._stream, indentation + line
            else:
                print >>self._stream, self.colorize("exception",
                                                    indentation + line)

    def stop_test(self, test):
        if self._verbose > 1:
            print >>self._stream
        self._stream.flush()

    def stop_tests(self):
        if self._verbose == 1:
            self._stream.write("\n")
        self._stream.flush()


class ColorOutputPlugin(nose.plugins.Plugin):

    """Output test results in colour to terminal."""

    name = "color"

    formatter_class = ColorfulOutputFormatter
    clean_tracebacks = False
    base_dir = None

    # These colors are carefully chosen to have enough contrast
    # on terminals with both black and white background.
    default_colorscheme = {"normal": "normal",
                           "pass": "green",
                           "failure": "magenta",
                           "error": "brightred",
                           "number": "green",
                           "ok-number": "green",
                           "error-number": "brightred",
                           "filename": "lightblue",
                           "lineno": "lightred",
                           "testname": "lightcyan",
                           "failed-example": "cyan",
                           "expected-output": "green",
                           "actual-output": "red",
                           "character-diffs": "magenta",
                           "diff-chunk": "magenta",
                           "exception": "red",
                           "skip": "yellow"}
    default_colorscheme = dict((name, parse_color(color)) for name, color in
                               default_colorscheme.iteritems())

    score = 50  # Lower than default plugin level, since the output we're
                # printing is replacing non-plugin core nose output, which
                # usually happens after plugin output.  If this were >= default
                # score, then e.g. core plugin testid output would come out in
                # the wrong place.

    def __init__(self):
        nose.plugins.Plugin.__init__(self)
        self._result = None
        # for debugging
#         self.base_dir = os.path.dirname(__file__)
#     clean_tracebacks = True

    def options(self, parser, env=os.environ):
        nose.plugins.Plugin.options(self, parser, env)
        parser.add_option("--no-color", action="store_false",
                          dest="enable_plugin_color",
                          help="Don't output in color")
        # XXX This might be wrong when running tests in a subprocess (since I
        # guess sys.stdout will be a pipe, but colour output should be turned
        # on).  Depends on how the running-in-a-subprocess is done (it's not a
        # core nose feature as of version 0.10.0).
        # XXX should be able to specify auto-color in environment
        action = sys.stdout.isatty() and "store_true" or "store_false"
        parser.add_option("--auto-color", action=action,
                          dest="enable_plugin_color",
                          help="Output in color only if stdout is a terminal")
        env_opt = "NOSE_COLORS"
        parser.add_option("--colors", action="store",
                          type="string",
                          dest="colors",
                          default=env.get(env_opt, ""),
                          help="Colour scheme for --with-color terminal "
                               "output, listing colours to be used for each "
                               "named part of the output.  Format is "
                               "name1=color1,name2=color2 . "
                               "Colours can be specified as xterm 256 colour "
                               "codes (e.g. '45'), RGB colours (e.g. "
                               "'rgb(00ff00)'), ANSI 16 colour names (e.g. "
                               "'red' or 'brightred'), and the special "
                               "colour 'normal'.  Example: "
                               "--colors='fail=red,pass=rgb(00ff00),error=45' "
                               + "[%s]" % env_opt)

    def configure(self, options, conf):
        nose.plugins.Plugin.configure(self, options, conf)
        if not self.enabled:
            return

        self._verbosity = conf.verbosity
        cs = dict(self.default_colorscheme)
        try:
            user_colorscheme = parse_colorscheme(options.colors)
        except ValueError, exc:
            filenames = list(conf.files)
            if options.files:
                filenames.extend(options.files)
            warnings.warn("Bad colorscheme string "
                          "(from --colors or one of %s): %s" %
                          (", ".join(filenames), exc), RuntimeWarning)
            user_colorscheme = {}
        unknown_names = set(user_colorscheme.keys()) - set(cs.keys())
        if unknown_names:
            warnings.warn("Invalid colorscheme names: %s" %
                          (", ".join(unknown_names)))
        cs.update(user_colorscheme)
        self._colorscheme = cs
        self._show_all = self._verbosity > 1
        self._dots = self._verbosity == 1

    def begin(self):
        self._old_failure_exception = doctest.DocTestCase.failureException
        # monkeypatch!
        doctest.DocTestCase.failureException = DocTestFailureException

    def setOutputStream(self, stream):
        self._stream = stream
        self._formatter = self.formatter_class(
            self._verbosity,
            True,
            self._colorscheme,
            self._stream,
            clean_tracebacks=self.clean_tracebacks,
            base_dir=self.base_dir)

    def prepareTestResult(self, result):
        result.__failures = []
        result.__errors = []
        result.__tests_run = 0
        result.__start_time = time.time()
        # Python <= 2.6 has _WritelnDecorator at top level
        try:
            writeln_decorator = unittest._WritelnDecorator
        # Python >= 2.7 has it in the runner module
        except AttributeError:
            writeln_decorator = unittest.runner._WritelnDecorator
        # This neuters any default or plugin defined output streams,
        # effectively forcing all output through Rudolf.
        result.stream = writeln_decorator(open(os.devnull, 'w'))
        # So we need to monkeypatch core addSkip, which appears to be the only
        # code called on skips (our own addSkip, if defined, is ignored.)
        # Gross, but works.
        old_addSkip = result.addSkip
        def new_addSkip(test, reason):
            old_addSkip(test, reason)
            label = result.errorClasses[nose.plugins.skip.SkipTest][1]
            self._formatter.test_skip(label)
        result.addSkip = new_addSkip

        self._result = result

    def startTest(self, test):
        self._result.__tests_run = self._result.__tests_run + 1
        self._formatter.start_test(test)

    def addSuccess(self, test):
        self._formatter.test_success(test)

    def addFailure(self, test, err):
        formatted_failure = self._exc_info_to_string(err, test)
        self._result.__failures.append((test, formatted_failure, err[0]))
        self._formatter.test_failure(test, err)

    def addError(self, test, err):
        # If the exception is a registered class, the error will be added to
        # the list for that class, not errors.
        formatted_err = self._formatter.format_traceback(err)
        for cls, (storage, label, isfail) in self._result.errorClasses.items():
            if issubclass(err[0], cls):
                storage.append((test, formatted_err, err[0]))
                self._formatter.test_error(test, err, label)
                return
        self._result.__errors.append((test, formatted_err, err[0]))
        self._formatter.test_error(test, err, "ERROR")

    def stopTest(self, test):
        self._formatter.stop_test(test)

    def report(self, stream):
        self._print_errors()
        self._print_summary(self._result.__start_time,
                            time.time())
        self._result = None

    def finalize(self, result):
        self._formatter.stop_tests()
        # remove monkeypatch
        doctest.DocTestCase.failureException = self._old_failure_exception

    def _print_errors(self):
        if self._dots or self._show_all:
            self._stream.writeln()
        self._formatter.print_error_list("ERROR", self._result.__errors)
        self._formatter.print_error_list("FAIL", self._result.__failures)
        for cls in self._result.errorClasses.keys():
            storage, label, isfail = self._result.errorClasses[cls]
            self._formatter.print_error_list(label, storage)

    def _print_summary(self, start, stop):
        success = self._result.wasSuccessful()
        summary = nose.util.odict()
        if not success:
            summary["failures"], summary["errors"] = \
                map(len, [self._result.__failures, self._result.__errors])
            for cls in self._result.errorClasses.keys():
                storage, label, isfail = self._result.errorClasses[cls]
                if not isfail:
                    continue
                summary[label] = len(storage)
        self._formatter.print_summary(success, summary,
                                      self._result.__tests_run, start, stop)

    def _exc_info_to_string(self, err, test):
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next
        if exctype is test.failureException:
            # Skip assert*() traceback levels
            length = self._count_relevant_tb_levels(tb)
            return ''.join(traceback.format_exception(exctype, value, tb,
                                                      length))
        return ''.join(traceback.format_exception(exctype, value, tb))

    def _is_relevant_tb_level(self, tb):
        return tb.tb_frame.f_globals.has_key('__unittest')

    def _count_relevant_tb_levels(self, tb):
        length = 0
        while tb and not self._is_relevant_tb_level(tb):
            length += 1
            tb = tb.tb_next
        return length


# classes for use in rudolf's own tests


class TestColorfulOutputFormatter(ColorfulOutputFormatter):

    __test__ = False

    def _format_seconds(self, n_seconds, normal="normal"):
        return "%s seconds" % (self.colorize("number", "...", normal))


class TestColorOutputPlugin(ColorOutputPlugin):

    __test__ = False

    formatter_class = TestColorfulOutputFormatter
    clean_tracebacks = True

    def __init__(self):
        ColorOutputPlugin.__init__(self)
        self.base_dir = os.path.dirname(__file__)
