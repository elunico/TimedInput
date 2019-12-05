import os
import signal
import sys
from select import select
from threading import Timer


def isWindows():
    return 'win' in sys.platform


if isWindows():
    def term_handler(s, f):
        raise _InputTimeoutError()

    signal.signal(signal.SIGTERM, term_handler)


def timed_input(seconds, prompt='', default=None):
    """\
    This function takes a number of seconds, an optional prompt, and
    an optional default and then prints the prompt and waits
    for the user to give keyboard input for `seconds` seconds.
    If no input is received the `default` is returned otherwise
    the input is returned. The function automatically
    cancels the timeout delay if input is received

    This function is platform dependent and has different
    behavior on Windows because not all signal APIs are available
    on Windows.

    On Windows, a SIGTERM hanlder is installed by this function
    that raises a custom exception. Keep this in mind if you
    are using this function on Windows together with signals

    On other platforms, select() is used and no signal handlers are
    specially installed
    """
    if isWindows():
        return _windows_timed_input(seconds, prompt, default)
    else:
        return _unix_timed_input(seconds, prompt, default)


class _InputTimeoutError(Exception):
    pass


def _startThread(seconds):
    pid = os.getpid()

    def thread_target():
        os.kill(pid, signal.SIGTERM)

    t = Timer(seconds, thread_target)
    t.start()
    return t


def _windows_timed_input(seconds, prompt='', default=None):
    """\
    This function should not be called directly,
    it is a platform dependant implementation

    This function takes a number of seconds, an optional prompt, and
    an optional default and then prints the prompt and waits
    for the user to give keyboard input for `seconds` seconds.
    If no input is received the `default` is returned otherwise
    the input is returned

    This is accomplished by installing a signal handler on
    SIGTERM and then spawing a thread Timer to send SIGTERM
    to the process after the specified number of seconds. The
    SIGTERM handler raises a custom exception that is handled by
    the function which then returns the default

    This is less ideal than select() since it has to install a
    signal handler and spawn a thread Timer and handle an exception
    which is slow, but select() is not available on Windows for
    files (stdin) so this is the alternative approach when select is
    not available
    """

    try:
        print('WARNING: Input times out after {} seconds'.format(seconds))
        timer = _startThread(seconds)
        text = input(prompt)
        return text
    except _InputTimeoutError:
        return default
    finally:
        # cancels the alarm if it exists
        timer.cancel()


def _unix_timed_input(seconds, prompt='', default=None):
    """\
    This function should not be called directly,
    it is a platform dependant implementation

    This function takes a number of seconds, an optional prompt, and
    an optional default and then prints the prompt and waits
    for the user to give keyboard input for `seconds` seconds.
    If no input is received the `default` is returned otherwise
    the input is returned

    This is accomplished by select() on stdin when available (on UNIX)

    It mimics the built-in input function and returns the input
    with whitespace stripped.

    A warning is printed when using this function that there will be a
    timeout
    """

    print('WARNING: Input times out after {} seconds'.format(seconds))
    print(prompt, end='')
    sys.stdout.flush()

    inputs, _, _ = select([sys.stdin], [], [], seconds)
    if len(inputs) > 0:
        return inputs[0].readline().strip()
    else:
        return default
