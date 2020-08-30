from pyproj import CRS, Transformer
import json, csv
from PIL import Image, ImageDraw
import argparse
import math

# TODO:
#   1. Implement buffering
#   2. Mainland detection

crs = CRS.from_epsg(3857) # Web Mercator
equator_len = 20037508.342789244 * 2 # Web Mercator constant

proj = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True) # From WGS 84 to Web Mercator
                                                                   # input:  (lon, lat)
                                                                   # output: (x, y)

with open('../datasets/countries.geojson') as f:
    countries = json.load(f)
    
country_code2idx_map = dict() 
for a3_code, index in [(country["properties"]["ISO_A3"], idx) for (idx, country) in enumerate(countries["features"])]:
    country_code2idx_map[a3_code] = index

with open('../datasets/mainlands.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)
    mainlands = {int(rows[0]) : int(rows[1]) for rows in reader}

# country_index = [country["properties"]["ISO_A3"] for country in countries["features"]].index(args.country_code)
# country = countries["features"][country_index]
# country_boundaries_lonlat = []
# if country["geometry"]["type"] == "Polygon":
#     country_boundaries_lonlat.append(country["geometry"]["coordinates"][0])
# elif country["geometry"]["type"] == "MultiPolygon":
#     for coords in country["geometry"]["coordinates"]:
#         country_boundaries_lonlat.append(coords[0])

# # Get the xy coordinates of the Web Mercator projection
# country_boundaries_xy = list(map(lambda boundaries_lonlat: [proj.transform(point[0], point[1]) for point in boundaries_lonlat],
#                            country_boundaries_lonlat))

# flat_country_boundaries_xy = [item for sublist in country_boundaries_xy for item in sublist]

# if len(list(filter(lambda p: p[0] < -170, flat_country_boundaries_xy))) > 0 and len(list(filter(lambda p: p[0] > 170, flat_country_boundaries_xy))) > 0:
#     country_boundaries_xy = list(map(lambda boundaries_xy: [p if p[0] >= 0 else (p[0] + equator_len, p[1]) for p in boundaries_xy],
#                            country_boundaries_xy))

# flat_country_boundaries_xy = [item for sublist in country_boundaries_xy for item in sublist]

def getBoundingRect(points):
    x_min, x_max = points[0][0], points[0][0]
    y_min, y_max = points[0][1], points[0][1] 

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

# x_min, x_max, y_min, y_max = getBoundingRect(flat_country_boundaries_xy)
# wm_width = x_max - x_min
# wm_height = y_max - y_min
# img_aspect_ratio = wm_width / wm_height
# px_height = 1000
# px_width = math.ceil(px_height * img_aspect_ratio)
# w_scale = px_width / wm_width
# h_scale = px_height / wm_height

def transformPoints(points, x_min, y_max, w_scale, h_scale):
    return [(abs(point[0] - x_min) * w_scale, (abs(point[1] - y_max) * h_scale)) for point in points]    

# country_boundaries_xy =[transformPoints(boundaries_xy) for boundaries_xy in country_boundaries_xy]

# img = Image.new("RGB", (px_width, px_height), "#ffffff")
# img1 = ImageDraw.Draw(img)
# for boundaries_xy in country_boundaries_xy:
#     img1.polygon(boundaries_xy, fill="#fccb88", outline="#000")
# img.show()

def lonlat2xy(boundaries_list_lonlat):
    return list(map(lambda boundaries_lonlat: [proj.transform(point[0], point[1]) for point in boundaries_lonlat], boundaries_list_lonlat))

def getRegionLonLat(country_indexes):
    region_boundaries_lonlat = []
    for country_index in country_indexes:
        country = countries["features"][country_index]

        if country["geometry"]["type"] == "Polygon":
            region_boundaries_lonlat.append(country["geometry"]["coordinates"][0])
        elif country["geometry"]["type"] == "MultiPolygon":
            # Mainlands only:
            region_boundaries_lonlat.append(country["geometry"]["coordinates"][mainlands[country_index]][0]) 
            # All territories
            # for coords in country["geometry"]["coordinates"]:
            #     region_boundaries_lonlat.append(coords[0])
    
    return region_boundaries_lonlat

def flattenList(a_list):
    return [item for sublist in a_list for item in sublist]

def moveToEastHemisphereXY(list_of_boundaries):
    flat_list_of_boundaries = flattenList(list_of_boundaries)

    if len(list(filter(lambda p: p[0] < -170, flat_list_of_boundaries))) > 0 and len(list(filter(lambda p: p[0] > 170, flat_list_of_boundaries))) > 0:
        return list(map(lambda boundaries_xy: [p if p[0] >= 0 else (p[0] + equator_len, p[1]) for p in boundaries_xy], list_of_boundaries))
    else:
        return list(list_of_boundaries)

def getRegionCountries(region_name):
    with open('../datasets/{}.csv'.format(region_name)) as f:
        reader = csv.reader(f)
        next(reader) # Skip headers

        country_codes = [int(row[0]) for row in reader]
        return country_codes

def a3ToDbIdx(a3_codes):
    db_indexes = list(map(lambda a3_code: country_code2idx_map[a3_code], a3_codes))
    db_indexes.sort()
    return db_indexes

def mergeSortedList(a: list, b: list):
    merged_list = []
    j = 0
    for i in range(len(a)):
        while(j < len(b) and b[j] <= a[i]):
            merged_list.append(b[j])
            j += 1
        merged_list.append(a[i])
    
    if j < len(b):
        merged_list += b[j:]

    return merged_list
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print the contours of a country specifiied by ISO 3166-1 alpha-3 code.')
    parser.add_argument('--countries', '-c', action='extend', nargs='+', type=str)
    parser.add_argument('--region', '-r')
    parser.add_argument('--selected', '-s', action='extend', nargs='+', type=str)
    args = parser.parse_args()

    countries_to_print = []
    if args.region is not None:
        countries_to_print = getRegionCountries(args.region)
    elif args.countries is not None:
        # Map selected countries to their A3 codes
        countries_to_print = a3ToDbIdx(args.countries)
    
    selected_countries = []
    if args.selected is not None:
        selected_countries = a3ToDbIdx(args.selected)
        countries_to_print = mergeSortedList(countries_to_print, selected_countries)
    

    # Drawing region
    region_boundaries_lonlat = getRegionLonLat(countries_to_print)
    region_boundaries_xy = lonlat2xy(region_boundaries_lonlat)

    selected_boundaries_lonlat = getRegionLonLat(selected_countries)
    selected_boundaries_xy = lonlat2xy(selected_boundaries_lonlat)

    flat_region_boundaries_xy = flattenList(region_boundaries_xy)

    x_min, x_max, y_min, y_max = getBoundingRect(flat_region_boundaries_xy)
    wm_width = x_max - x_min
    wm_height = y_max - y_min
    img_aspect_ratio = wm_width / wm_height
    px_height = 1000
    px_width = math.ceil(px_height * img_aspect_ratio)
    w_scale = px_width / wm_width
    h_scale = px_height / wm_height

    # Transform to image xy
    region_boundaries_xy = [transformPoints(boundaries_xy, x_min, y_max, w_scale, h_scale) for boundaries_xy in region_boundaries_xy]
    selected_boundaries_xy = [transformPoints(boundaries_xy, x_min, y_max, w_scale, h_scale) for boundaries_xy in selected_boundaries_xy]

    img = Image.new("RGB", (px_width, px_height), "#d6eeff")
    img1 = ImageDraw.Draw(img)
    for boundaries_xy in region_boundaries_xy:
        img1.polygon(boundaries_xy, fill="#ffeebd", outline="#000")
    for boundaries_xy in selected_boundaries_xy:
        img1.polygon(boundaries_xy, fill="#ff1414", outline="#000")
    img.show()