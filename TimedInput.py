import os
import signal
import sys
from select import select

_initialized = False


def timed_input(seconds, prompt='', default=None):
    if 'win' in sys.platform:
        return _windows_timed_input(seconds, prompt, default)
    else:
        return _unix_timed_input(seconds, prompt, default)


class _InputTimeoutError(Exception):
    pass


def _windows_timed_input(seconds, prompt='', default=None):
    global _initialized
    if not _initialized:

        def alarm_handler(s, f):
            raise _InputTimeoutError()

        signal.signal(signal.SIGALRM, alarm_handler)

        _initialized = True

    # FIXME: signal.alarm is not available on windows
    try:
        print('WARNING: Input times out after {} seconds'.format(seconds))
        signal.alarm(seconds)
        text = input(prompt)
        return text
    except _InputTimeoutError:
        return default
    finally:
        # cancels the alarm if it exists
        signal.alarm(0)


def _unix_timed_input(seconds, prompt='', default=None):
    print('WARNING: Input times out after {} seconds'.format(seconds))
    print(prompt, end='')
    sys.stdout.flush()

    inputs, _, _ = select([sys.stdin], [], [], seconds)
    if len(inputs) > 0:
        return inputs[0].readline().strip()
    else:
        return default
