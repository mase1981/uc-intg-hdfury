#!/usr/bin/env python3
"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
from uc_intg_hdfury.driver import main, loop, cleanup_on_shutdown

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        loop.run_until_complete(cleanup_on_shutdown())
        loop.close()
