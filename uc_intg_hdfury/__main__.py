"""
Entry point for running as module: python -m uc_intg_hdfury

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
from uc_intg_hdfury import main

if __name__ == "__main__":
    asyncio.run(main())
