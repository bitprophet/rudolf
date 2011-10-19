Colorful output
===============

The plugin emits terminal control sequences to highlight important
pieces of information (such as the names of failing tests) in
different colors.  The plugin only works on Unix-like systems.

    >>> import os.path, sys, tempfile

    >>> import rudolf

    >>> directory_with_tests = os.path.join(os.path.dirname(__file__),
    ...                                     "test-support")

Since it wouldn't be a good idea to have terminal control characters in a
test file, let's wrap sys.stdout in a simple terminal interpreter

    >>> import re
    >>> class Terminal(object):
    ...     _xterm_color_regexp = re.compile('\033[[]38;5;([0-9;]*)m')
    ...     _color_regexp = re.compile('\033[[]([0-9;]*)m')
    ...     _colors = {'0': 'normal', '1': 'bold', '30': 'black', '31': 'red',
    ...                '32': 'green', '33': 'yellow', '34': 'blue',
    ...                '35': 'magenta', '36': 'cyan', '37': 'grey'}
    ...     def __init__(self, stream):
    ...         self._stream = stream
    ...         self._isatty = False
    ...     def isatty(self):
    ...         return self._isatty
    ...     def set_isatty(self, value):
    ...         self._isatty = bool(value)
    ...     def __getattr__(self, attr):
    ...         return getattr(self._stream, attr)
    ...     def write(self, text):
    ...         if "\033[38;5;" in text:
    ...             text = self._xterm_color_regexp.sub(self._xterm_color, text)
    ...         if '\033[' in text:
    ...             text = self._color_regexp.sub(self._color, text)
    ...         self._stream.write(text)
    ...     def writelines(self, lines):
    ...         for line in lines:
    ...             self.write(line)
    ...     def _xterm_color(self, match):
    ...         return "{xterm %s}" % match.group(1)
    ...     def _color(self, match):
    ...         colorstring = '{'
    ...         for number in match.group(1).split(';'):
    ...             colorstring += self._colors.get(number, '?')
    ...         return colorstring + '}'

    >>> real_stdout = sys.stdout
    >>> sys.stdout = Terminal(sys.stdout)

We don't want to remove tracebacks from the output or remove the test
timing like nose.plugins.plugintest.run(), so we use a modified
version.

    >>> def run(*arg, **kw):
    ...     from cStringIO import StringIO
    ...     from nose import run
    ...     from nose.config import Config
    ...     from nose.plugins.manager import PluginManager
    ...
    ...     buffer = StringIO()
    ...     if 'config' not in kw:
    ...         plugins = kw.pop('plugins', None)
    ...         env = kw.pop('env', {})
    ...         manager = PluginManager(plugins=plugins)
    ...         kw['config'] = Config(env=env, plugins=manager)
    ...     if 'argv' not in kw:
    ...         kw['argv'] = ['nosetests', '-v']
    ...     kw['config'].stream = buffer
    ...     run(*arg, **kw)
    ...     out = buffer.getvalue()
    ...     print out.strip()

A successful test run.  The "ok"s and numbers come out in green.

    >>> from nose.plugins.doctests import Doctest

    >>> plugins = [rudolf.TestColorOutputPlugin(), Doctest()]

    >>> run(argv=["nosetests", "-v", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}Doctest: passing_doctest.rst{normal}{normal} ... {normal}{green}ok{normal}
    {normal}passing_tests.passing_test_1{normal}{normal} ... {normal}{green}ok{normal}
    {normal}passing_tests.passing_test_2{normal}{normal} ... {normal}{green}ok{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {green}3 {normal}tests in {green}...{normal} seconds
    {green}OK{normal}


Without the '-v' for "verbose", the dots are green:

    >>> run(argv=["nosetests", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {green}.{normal}{green}.{normal}{green}.{normal}
    ----------------------------------------------------------------------
    Ran {green}3 {normal}tests in {green}...{normal} seconds
    {green}OK{normal}


A failed test highlights the errors and failures in magenta:

    >>> py = os.path.join(directory_with_tests, "failing", "failing_tests.py")
    >>> testname = py + ":failing_test"
    >>> run(argv=["nosetests", "-v", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           testname],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}failing_tests.failing_test{normal}{normal} ... {normal}{magenta}FAIL{normal}
    <BLANKLINE>
    ======================================================================
    {magenta}FAIL{normal}: {boldcyan}failing_tests.failing_test{normal}
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    {normal}  File "{boldblue}.../case.py{normal}", line {boldred}...{normal}, in {boldcyan}runTest{normal}
    {cyan}    self.test(*self.arg){normal}
    {normal}  File "{boldblue}test-support/failing/failing_tests.py{normal}", line {boldred}5{normal}, in {boldcyan}failing_test{normal}
    {cyan}    assert False{normal}
    {red}AssertionError{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {boldred}1 {normal}test in {green}...{normal} seconds
    {magenta}FAILED{normal} (failures={magenta}1{normal})


A test that raises an error highlights the errors and failures in red.
The test run summary is still in magenta.

    >>> py = os.path.join(directory_with_tests, "failing", "failing_tests.py")
    >>> testname = py + ":erroring_test"
    >>> run(argv=["nosetests", "-v", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           testname],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}failing_tests.erroring_test{normal}{normal} ... {normal}{boldred}ERROR{normal}
    <BLANKLINE>
    ======================================================================
    {boldred}ERROR{normal}: {boldcyan}failing_tests.erroring_test{normal}
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    {normal}  File "{boldblue}unittest.py{normal}", line {boldred}260{normal}, in {boldcyan}run{normal}
    {cyan}    testMethod(){normal}
    {normal}  File "{boldblue}.../case.py{normal}", line {boldred}...{normal}, in {boldcyan}runTest{normal}
    {cyan}    self.test(*self.arg){normal}
    {normal}  File "{boldblue}test-support/failing/failing_tests.py{normal}", line {boldred}2{normal}, in {boldcyan}erroring_test{normal}
    {cyan}    raise Exception(){normal}
    {red}Exception{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {boldred}1 {normal}test in {green}...{normal} seconds
    {magenta}FAILED{normal} (errors={boldred}1{normal})


Passing doctest looks just like any other passing test

    >>> suitepath = os.path.join(directory_with_tests, "passing",
    ...                          "passing_doctest.rst")
    >>> run(argv=["nosetests", "-v", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           suitepath],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}Doctest: passing_doctest.rst{normal}{normal} ... {normal}{green}ok{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {green}1 {normal}test in {green}...{normal} seconds
    {green}OK{normal}


Failing doctest

    >>> suitepath = os.path.join(directory_with_tests, "failing",
    ...                          "failing_doctest.rst")
    >>> run(argv=["nosetests", "-v", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           suitepath],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}Doctest: failing_doctest.rst{normal}{normal} ... {normal}{magenta}FAIL{normal}
    <BLANKLINE>
    ======================================================================
    {magenta}FAIL{normal}: {boldcyan}Doctest: failing_doctest.rst{normal}
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    {normal}  File "{boldblue}doctest.py{normal}", line {boldred}2112{normal}, in {boldcyan}runTest{normal}
    {cyan}    raise self.failureException(self.format_failure(new.getvalue())){normal}
    {red}DocTestFailureException: Failed doctest test for failing_doctest.rst{normal}
    {normal}  File "{boldblue}test-support/failing/failing_doctest.rst{normal}", line {boldred}0{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    {normal}File "{boldblue}test-support/failing/failing_doctest.rst{normal}", line {boldred}1{normal}, in {boldcyan}failing_doctest.rst{normal}
    Failed example:
    {cyan}    True{normal}
    Expected:
    {green}    False{normal}
    Got:
    {red}    True{normal}
    <BLANKLINE>
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {boldred}1 {normal}test in {green}...{normal} seconds
    {magenta}FAILED{normal} (failures={magenta}1{normal})


Failing doctest with REPORT_NDIFF turned on.  The ndiff gets syntax-coloured.

    >>> suitepath = os.path.join(directory_with_tests, "failing",
    ...                          "failing_doctest_with_ndiff.rst")
    >>> run(argv=["nosetests", "-v", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           suitepath],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}Doctest: failing_doctest_with_ndiff.rst{normal}{normal} ... {normal}{magenta}FAIL{normal}
    <BLANKLINE>
    ======================================================================
    {magenta}FAIL{normal}: {boldcyan}Doctest: failing_doctest_with_ndiff.rst{normal}
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    {normal}  File "{boldblue}doctest.py{normal}", line {boldred}2112{normal}, in {boldcyan}runTest{normal}
    {cyan}    raise self.failureException(self.format_failure(new.getvalue())){normal}
    {red}DocTestFailureException: Failed doctest test for failing_doctest_with_ndiff.rst{normal}
    {normal}  File "{boldblue}test-support/failing/failing_doctest_with_ndiff.rst{normal}", line {boldred}0{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    {normal}File "{boldblue}test-support/failing/failing_doctest_with_ndiff.rst{normal}", line {boldred}1{normal}, in {boldcyan}failing_doctest_with_ndiff.rst{normal}
    Failed example:
    {cyan}    print "The quick brown fox jumps over the lazy dog."{normal}
    {cyan}        # doctest: +REPORT_NDIFF{normal}
    Differences (ndiff with {green}-expected {red}+actual{normal}):
    {green}    - 'The quick brown zox jumps over the spam lazy dog.'{normal}
    {magenta}    ? -                ^                 -----          -{normal}
    {red}    + The quick brown fox jumps over the lazy dog.{normal}
    {magenta}    ?                 ^{normal}
    <BLANKLINE>
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {boldred}1 {normal}test in {green}...{normal} seconds
    {magenta}FAILED{normal} (failures={magenta}1{normal})


Erroring doctest (with traceback)

    >>> suitepath = os.path.join(directory_with_tests, "failing",
    ...                          "erroring_doctest.rst")
    >>> run(argv=["nosetests", "-v", "--with-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           suitepath],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}Doctest: erroring_doctest.rst{normal}{normal} ... {normal}{magenta}FAIL{normal}
    <BLANKLINE>
    ======================================================================
    {magenta}FAIL{normal}: {boldcyan}Doctest: erroring_doctest.rst{normal}
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    {normal}  File "{boldblue}doctest.py{normal}", line {boldred}2112{normal}, in {boldcyan}runTest{normal}
    {cyan}    raise self.failureException(self.format_failure(new.getvalue())){normal}
    {red}DocTestFailureException: Failed doctest test for erroring_doctest.rst{normal}
    {normal}  File "{boldblue}test-support/failing/erroring_doctest.rst{normal}", line {boldred}0{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    {normal}File "{boldblue}test-support/failing/erroring_doctest.rst{normal}", line {boldred}1{normal}, in {boldcyan}erroring_doctest.rst{normal}
    Failed example:
    {cyan}    raise Exception("oops"){normal}
    Exception raised:
        Traceback (most recent call last):
        {normal}  File "{boldblue}doctest.py{normal}", line {boldred}1212{normal}, in {boldcyan}__run{normal}
    {cyan}        compileflags, 1) in test.globs{normal}
        {normal}  File "{boldblue}<doctest erroring_doctest.rst[0]>{normal}", line {boldred}1{normal}, in {boldcyan}<module>{normal}
    {cyan}        raise Exception("oops"){normal}
    {red}    Exception: oops{normal}
    <BLANKLINE>
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {boldred}1 {normal}test in {green}...{normal} seconds
    {magenta}FAILED{normal} (failures={magenta}1{normal})


Custom colors:

    >>> run(argv=["nosetests", "--with-color",
    ...           "--colors", "pass=red,ok-number=rgb(0000ff),number=220",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {red}.{normal}{red}.{normal}{red}.{normal}
    ----------------------------------------------------------------------
    Ran {xterm 21}3 {normal}tests in {xterm 220}...{normal} seconds
    {red}OK{normal}


If --with-color or environment variable NOSE_WITH_COLOR have been
previously set (perhaps by a test runner wrapper script), but no
colorized output is desired, the --no-color option will disable
colorized output:

    >>> import nose.plugins.plugintest
    >>> nose.plugins.plugintest.run(
    ...     env={"NOSE_WITH_COLOR": True},
    ...     argv=["nosetests", "-v", "--with-color", "--no-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    Doctest: passing_doctest.rst ... ok
    passing_tests.passing_test_1 ... ok
    passing_tests.passing_test_2 ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 3 tests in ...s
    <BLANKLINE>
    OK


The --auto-color option will determine if stdout is a terminal, and
only enable colorized output if so.  Of course, stdout is not a
terminal here, so no color will be produced:

    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--auto-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    Doctest: passing_doctest.rst ... ok
    passing_tests.passing_test_1 ... ok
    passing_tests.passing_test_2 ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 3 tests in ...s
    <BLANKLINE>
    OK

with stdout pretending to be a terminal, the output is colorized:

    >>> sys.stdout.set_isatty(True)
    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--auto-color",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}Doctest: passing_doctest.rst{normal}{normal} ... {normal}{green}ok{normal}
    {normal}passing_tests.passing_test_1{normal}{normal} ... {normal}{green}ok{normal}
    {normal}passing_tests.passing_test_2{normal}{normal} ... {normal}{green}ok{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {green}3 {normal}tests in {green}...{normal} seconds
    {green}OK{normal}

    >>> sys.stdout.set_isatty(False)


The plugin should work with other plugins that print output to the
terminal (here, plugin testid is enabled):

    >>> from nose.plugins.testid import TestId
    >>> noseids = tempfile.mktemp()
    >>> plugins = [rudolf.TestColorOutputPlugin(), Doctest(), TestId()]
    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--with-color",
    ...           "--with-id", "--id-file", noseids,
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    #1 {normal}Doctest: passing_doctest.rst{normal}{normal} ... {normal}{green}ok{normal}
    #2 {normal}passing_tests.passing_test_1{normal}{normal} ... {normal}{green}ok{normal}
    #3 {normal}passing_tests.passing_test_2{normal}{normal} ... {normal}{green}ok{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {green}3 {normal}tests in {green}...{normal} seconds
    {green}OK{normal}

    >>> os.remove(noseids)

It should still work even for low-score plugins whose output is
printed after rudolf's output, and whose plugin methods are called
after rudolf's:

    >>> class LowPriorityPlugin(nose.plugins.Plugin):
    ...     name = "bob"
    ...     score = rudolf.TestColorOutputPlugin.score - 1
    ...     def setOutputStream(self, stream):
    ...         self.stream = stream
    ...     def startTest(self, test):
    ...         self.stream.write("spam")
    >>> plugins = [rudolf.TestColorOutputPlugin(), Doctest(),
    ...            LowPriorityPlugin()]
    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--with-color",
    ...           "--with-bob",
    ...           "--with-doctest", "--doctest-extension", ".rst",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    {normal}Doctest: passing_doctest.rst{normal}{normal} ... {normal}spam{green}ok{normal}
    {normal}passing_tests.passing_test_1{normal}{normal} ... {normal}spam{green}ok{normal}
    {normal}passing_tests.passing_test_2{normal}{normal} ... {normal}spam{green}ok{normal}
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran {green}3 {normal}tests in {green}...{normal} seconds
    {green}OK{normal}



Clean up:

    >>> sys.stdout = real_stdout
