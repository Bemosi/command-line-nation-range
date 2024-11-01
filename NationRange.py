import GetHomeblocks # type: ignore
import DrawRange # type: ignore
import time
import asyncio
import sys

nation = sys.argv[3]

async def main():
    start_time = time.time()

    result = GetHomeblocks.fetch_all_homeblocks(nation)

    await DrawRange.draw(result, nation)

    print(f"{time.time() - start_time} seconds")
    
if __name__ == "__main__":
    asyncio.run(main())