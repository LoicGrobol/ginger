import os
from sys import path
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path.append(PATH)

import pytest
