from pyproj import CRS, Transformer
import json
from PIL import Image, ImageDraw
import argparse
import math

parser = argparse.ArgumentParser(description='Print the contours of a country specifiied by ISO 3166-1 alpha-3 code.')
parser.add_argument('country_code')
args = parser.parse_args()


crs = CRS.from_epsg(3857) # Web Mercator
equator_len = 20037508.342789244 * 2 # Web Mercator constant

proj = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True) # From WGS 84 to Web Mercator
                                                                   # input:  (lon, lat)
                                                                   # output: (x, y)

with open('../datasets/countries.geojson') as f:
    countries = json.load(f)

country_index = [country["properties"]["ISO_A3"] for country in countries["features"]].index(args.country_code)
country = countries["features"][country_index]
country_boundaries_lonlat = []
if country["geometry"]["type"] == "Polygon":
    country_boundaries_lonlat = [country["geometry"]["coordinates"][0]]
elif country["geometry"]["type"] == "MultiPolygon":
    for coords in country["geometry"]["coordinates"]:
        country_boundaries_lonlat.append(coords[0])

# Get the xy coordinates of the Web Mercator projection
country_boundaries_xy = list(map(lambda boundaries_lonlat: [proj.transform(point[0], point[1]) for point in boundaries_lonlat],
                           country_boundaries_lonlat))

flat_country_boundaries_xy = [item for sublist in country_boundaries_xy for item in sublist]

if len(list(filter(lambda p: p[0] < -170, flat_country_boundaries_xy))) > 0 and len(list(filter(lambda p: p[0] > 170, flat_country_boundaries_xy))) > 0:
    country_boundaries_xy = list(map(lambda boundaries_xy: [p if p[0] >= 0 else (p[0] + equator_len, p[1]) for p in boundaries_xy],
                           country_boundaries_xy))

flat_country_boundaries_xy = [item for sublist in country_boundaries_xy for item in sublist]

def getBoundingRect(points):
    x_min, y_min = float('inf'), float('inf')
    x_max, y_max = float('-inf'), float('-inf')

    for point in points:
        if point[0] < x_min:
            x_min = point[0]
        elif point[0] > x_max:
            x_max = point[0]
        
        if point[1] < y_min:
            y_min = point[1]
        elif point[1] > y_max:
            y_max = point[1]
    
    return x_min, x_max, y_min, y_max

x_min, x_max, y_min, y_max = getBoundingRect(flat_country_boundaries_xy)
wm_width = x_max - x_min
wm_height = y_max - y_min
img_aspect_ratio = wm_width / wm_height
px_height = 1000
px_width = math.ceil(px_height * img_aspect_ratio)
w_scale = px_width / wm_width
h_scale = px_height / wm_height

def transformPoints(points):
    return [(abs(point[0] - x_min) * w_scale, (abs(point[1] - y_max) * h_scale)) for point in points]    

country_boundaries_xy =[transformPoints(boundaries_xy) for boundaries_xy in country_boundaries_xy]

img = Image.new("RGB", (px_width, px_height), "#ffffff")
img1 = ImageDraw.Draw(img)
for boundaries_xy in country_boundaries_xy:
    img1.polygon(boundaries_xy, fill="#fccb88", outline="#000")
img.show()
