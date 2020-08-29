from pyproj import CRS, Transformer
import json, csv


crs = CRS.from_epsg(3857) # Web Mercator
proj = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True) # From WGS 84 to Web Mercator
                                                                   # input:  (lon, lat)
                                                                   # output: (x, y)


def lonlat2xy(boundaries_list_lonlat):
    return list(map(lambda boundaries_lonlat: [proj.transform(point[0], point[1]) for point in boundaries_lonlat], boundaries_list_lonlat))

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

def detectMainland(borders_xy):
    maxArea, maxIdx = 0, 0
    for idx, region in enumerate(borders_xy):
        x_min, x_max, y_min, y_max = getBoundingRect(region[0])
        area = (x_max - x_min) * (y_max - y_min)
        if area > maxArea:
            maxArea = area
            maxIdx = idx
    
    return maxIdx

if __name__ == "__main__":

    with open('../datasets/countries.geojson') as f:
        countries_data = json.load(f)
    
    borders_data = countries_data["features"]

    with open('../datasets/mainlands.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['DB Index', 'Mainland Polygon Index'])

        for idx, country_borders in enumerate(borders_data):
            if country_borders["geometry"]["type"] == "MultiPolygon":
                # mainland = detectMainland(country["geometry"]["coordinates"])
                # region_boundaries_lonlat.append(coords[0])
                borders_xy = list(map(lambda border: lonlat2xy(border), country_borders["geometry"]["coordinates"]))
                mainlandPolygonIdx = detectMainland(borders_xy)
                writer.writerow([idx, mainlandPolygonIdx])

                 
