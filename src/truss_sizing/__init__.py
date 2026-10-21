"""Linear sizing optimisation of isostatic trusses under external and self-weight loads.

Implements the "indirect method" of Martins, Avila & da Silva (2019),
Int. J. Steel Struct. 19(4), 1146-1157, doi:10.1007/s13296-018-0194-8.
"""
from .truss import Truss, member_forces, size_truss

__all__ = ["Truss", "member_forces", "size_truss"]
