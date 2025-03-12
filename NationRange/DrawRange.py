import PIL
from PIL import Image, ImageDraw
from shapely.geometry import Point # type: ignore
from shapely.ops import unary_union # type: ignore
from shapely.affinity import scale # type: ignore
import time
import sys
import os
import aiohttp # type: ignore
import asyncio
import math

PIXEL_LIMIT=10000
FILE_SIZE_LIMIT=10485760
BYTES_IN_MB=1048576

zoom = int(sys.argv[1]) 
line_thickness = int(sys.argv[2])
s = 2**(int(zoom)+1)
sd = 16/s
padding = 4000//16
ts = 512
bpp = 2**(12-int(zoom))

async def draw(homeblocks, filename, default_radius=1000/sd, capital_radius=3500/sd):    
    def coordinates():
        coords = []
        for block in homeblocks:
            townblocks = block['townblocks']
            for coordis in townblocks:
                if not isinstance(coords, (list, tuple)) or len(coordis) != 2:
                    print(f"Invalid structure for town block: {coordis}")
                    continue
                coords.append(coordis)
        return coords
    
    coords = coordinates()
    
    minX = min(coord[0] for coord in coords)-padding
    minZ = min(coord[1] for coord in coords)-padding
    maxX = max(coord[0] for coord in coords)+padding
    maxZ = max(coord[1] for coord in coords)+padding
    
    total_width = int((maxX-minX)*16*ts/bpp)
    total_height = int((maxZ-minZ)*16*ts/bpp)
                    
    link = 'https://map.earthmc.net'
    world = 'minecraft_overworld'
    now = int(time.time())

    async def download_tiles(tiles):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for x, z in tiles:
                url = f'{link}/tiles/{world}/{zoom}/{x}_{z}.png'
                path = f'caches/{zoom}/{x}_{z}.png'
                tasks.append(download_tile(session, url, path))
            await asyncio.gather(*tasks)

    async def download_tile(session, url, path):
        if os.path.exists(path):
            return
        try:
            async with session.get(url, ssl=False) as response:
                if response.status != 200:
                    return
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as file:
                    file.write(await response.read())
        except Exception as e:
            print(f"Error downloading {url}: {e}")

    async def create_background():

        tminX = math.floor(minX*16/bpp)
        tminZ = math.floor(minZ*16/bpp)
        tmaxX = math.floor(maxX*16/bpp)
        tmaxZ = math.floor(maxZ*16/bpp)

        nx = math.floor(tminX*ts)
        nz = math.floor(tminZ*ts)
        
        tiles = [(x, z) for x in range(tminX, tmaxX+1) for z in range(tminZ, tmaxZ+1)]
                            
        await download_tiles(tiles)
        

        if total_width > PIXEL_LIMIT or total_height > PIXEL_LIMIT:
            print("One of the dimensions is greater than 10,000 pixels, too big to show on discord try a lower zoom level.")
            return None
        
        output = Image.new(mode="RGBA", size=(total_width+ts, total_height+ts))
        
        for x in range(tminX, tmaxX + 1):
            for z in range(tminZ, tmaxZ + 1):
                tile_path = f'caches/{zoom}/{x}_{z}.png'
                try:
                    tile = Image.open(tile_path)
                    output.paste(tile, ((x-tminX)*ts, (z-tminZ)*ts))
                except FileNotFoundError:
                    print(f"Warning: Tile {tile_path} not found.")
                    continue
                
        cLeft = abs(abs(minX)*s-abs(nx))
        cTop = abs(abs(minZ)*s-abs(nz))
        cRight = abs(cLeft+abs(maxX-minX)*s)+s*2
        cBottom = abs(cTop+abs(maxZ-minZ)*s)+s*2

        cropped = output.crop((cLeft, cTop, cRight, cBottom))
        return cropped
        
    background = await create_background()
    if background is None:
        return
        
    def draw_united_homeblock_circles():
        
        TINT_COLOR = (0, 0, 0)  # Black
        TRANSPARENCY = .5  # Degree of transparency, 0-100%
        OPACITY = int(255 * TRANSPARENCY)

        image = background

        overlay = Image.new('RGBA', image.size, TINT_COLOR+(0,))
        draw2 = ImageDraw.Draw(overlay)
        draw2.rectangle([(0, 0), (total_width+8*s, total_height+8*s)], fill=TINT_COLOR+(OPACITY,))
        
        image2 = Image.alpha_composite(image, overlay)
        
        draw = ImageDraw.Draw(image2)
        
        circles = []

        for block in homeblocks:
            if not isinstance(block, dict) or 'homeblock' not in block or not isinstance(block['homeblock'], list) or len(block['homeblock']) != 2:
                print(f"Invalid structure for block: {block}")
                continue

            x = block['homeblock'][0]
            z = block['homeblock'][1]
            
            radius = capital_radius if block.get('status', {}).get('isCapital', False) else default_radius

            circle = Point(x*s - minX*s, z*s - minZ*s).buffer(radius)
            circles.append(circle)

        united_shape = unary_union(circles)
        scaled_shape = scale(united_shape, xfact=1.0, yfact=1.0)

        def draw_shape(geom):
            if geom.geom_type == 'Polygon':
                coords2 = list(geom.exterior.coords)
                draw.polygon(coords2, outline="white", width = line_thickness)
            elif geom.geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    coords2 = list(poly.exterior.coords)
                    draw.polygon(coords2, outline="white", width = line_thickness)
                
        for coord in coords:
            adjusted_coord = ((coord[0] - minX)*s, (coord[1] - minZ)*s)
            draw.rectangle([adjusted_coord, (adjusted_coord[0] + s - 1, adjusted_coord[1] + s - 1)], fill="white")
                
        draw_shape(scaled_shape)
        image2.save(filename)
        size = os.path.getsize(filename)
        if size > FILE_SIZE_LIMIT:
            print(f"Image size {(size/BYTES_IN_MB):.2f}MB exceeds the limit {FILE_SIZE_LIMIT/BYTES_IN_MB}MB, try again with a lower zoom level.")
            os.remove(filename)
        elif size < FILE_SIZE_LIMIT:
            image2.show(filename)
            #os.remove(filename) ##add when moved to bot

    draw_united_homeblock_circles()

