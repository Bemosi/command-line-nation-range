import GetHomeblocks # type: ignore
import DrawRange # type: ignore
import time
import asyncio
import sys

nation_csv = sys.argv[3]

async def main():
    start_time = time.time()

    nation_list = nation_csv.split(",")
	
    homeblocks = []
    for nation in nation_list:
        result = GetHomeblocks.fetch_all_homeblocks(nation)
        homeblocks.extend(result)

    other_nation_filename = ''
    if len(nation_list) > 1:
        other_nation_filename = f'-+{len(nation_list) - 1}'

    filename = f'natiorange-{nation_list[0]}{other_nation_filename}-{(time.time()):.2f}.png'
    await DrawRange.draw(homeblocks, filename)

    print(f"{time.time() - start_time} seconds")
    
if __name__ == "__main__":
    asyncio.run(main())
