import contextlib
import sys
from typing import List
from models import CommandLineOptions


class DummyFile:
    def write(self, x):
        pass


@contextlib.contextmanager
def stop_echo():
    temp_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = temp_stdout


def command_line_parser(arguments: List[str]) -> CommandLineOptions:
    flags: List[str] = [argument for argument in arguments if argument[0] == "-"]
    commands: List[str] = [argument for argument in arguments if argument not in flags]
    expand_flags: List[str] = [flag[2:] if flag[1] == "-" else CommandLineOptions.flag_maps[flag[1:]] for flag in flags]
    expand_flags_without_duplicates: List[str] = list(set(expand_flags))

    my_options: CommandLineOptions = CommandLineOptions(command_list=commands)
    if "progress" in expand_flags_without_duplicates:
        my_options.progress = True

    return my_options
