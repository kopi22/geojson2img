from bs4 import BeautifulSoup
from urllib.request import urlopen
import csv
import json


def wikiLinksToCountryAlpha3Codes(wikiLinks: str):
    url = "https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3"
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    rows = []
    for wikiLink in wikiLinks:
        a_country = soup.find('a', href=wikiLink)
        try:
            span_code = a_country.find_previous_sibling('span')
        except AttributeError as err:
            name = wikiLink.split('/')[-1]
            if (name == 'Cape_Verde'):
                rows.append(['CPV', 'Cabo Verde'])
            else:
                print('Territory without the code: {}'.format(name))
        else:
            rows.append([span_code.string, a_country.string])
    
    return rows

def retrieveCountriesWikiLinks(url: str):
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    flags = soup.find_all('span', class_='flagicon')

    wikiLinks = []
    for flag in flags:
        wikiLinks.append(flag.find_next_sibling('a')['href'])
    
    return wikiLinks

regions = {
    'africa': 'https://en.wikipedia.org/wiki/List_of_African_countries_by_area',
    'asia': 'https://en.wikipedia.org/wiki/List_of_Asian_countries_by_area',
    'europe': 'https://en.wikipedia.org/wiki/List_of_European_countries_by_area',
    'south_america': 'https://en.wikipedia.org/wiki/List_of_South_American_countries_by_area',
    'north_america': 'https://en.wikipedia.org/wiki/List_of_North_American_countries_by_area',
    # 'oceania': 'https://en.wikipedia.org/wiki/List_of_islands_in_Oceania_by_area', as it needs manual refining
}

if __name__ == '__main__':

    for regionName, regionUrl in regions.items():
        wikiLinks = retrieveCountriesWikiLinks(regionUrl)
        countryData = wikiLinksToCountryAlpha3Codes(wikiLinks)
        countryData.sort(key=lambda data: data[0])

        with open('../datasets/{}.csv'.format(regionName), 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['DB Index', 'Country Code', 'Country Name'])
            
            with open('../datasets/countries.geojson') as database:
                dbData = json.load(database)
            countries = [country["properties"]["ISO_A3"] for country in dbData["features"]]
            
            for countryCode, countryName in countryData:
                try:
                    countryIndex = countries.index(countryCode)
                except ValueError as err:
                    print('{} - {} is not in the DB'.format(countryCode, countryName))
                else:
                    writer.writerow([countryIndex, countryCode, countryName])
        