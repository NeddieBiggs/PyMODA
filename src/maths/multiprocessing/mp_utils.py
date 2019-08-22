#  PyMODA, a Python implementation of MODA (Multiscale Oscillatory Dynamics Analysis).
#  Copyright (C) 2019 Lancaster University
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <https://www.gnu.org/licenses/>.

import psutil as psutil
from multiprocess import Process

"""
Contains functions to help with multiprocessing.
"""


def terminate_tree(process: Process):
    """
    Terminates a process along with all of its child processes.
    """
    try:
        pid = process.pid
        for child in psutil.Process(pid).children(recursive=True):
            child.terminate()
    except psutil.NoSuchProcess:
        pass
    finally:
        process.terminate()
