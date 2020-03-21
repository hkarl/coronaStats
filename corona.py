"""Download and visualiaze corona numbers.
Based on: 
- Corona data from https://covid.ourworldindata.org/data/full_data.csv
- Possibly better source: https://data.humdata.org/dataset/novel-coronavirus-2019-ncov-cases/resource/4cd2eaa1-fd3e-4371-a234-a8ef2b44cc1f 
- Population data from https://datahub.io/JohnSnowLabs/population-figures-by-country (more up to date useful)
"""

import csv, sys

from pprint import pprint as pp
from collections import defaultdict 
from itertools import groupby, dropwhile
from math import log10 

import click 
import requests

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt


class NotImplemented(Exception):
    pass



def get_data(download, countries_file, corona_file, url):
    """Download and write to file, or just load from file. 
    Return two lists of values: population numbers and corona statistics"""
    
    def download_files(url, corona_file):
        r = requests.get(url)
        with open(corona_file, 'wb') as f:
            f.write(r.content)

    def load_files():
        with open(countries_file, "r", newline='') as f:
            next(f)  # skip header 
            reader = csv.reader(f)
            countries = [r for r in reader]

        with open(corona_file, "r", newline='') as f:
            next(f)
            reader = csv.DictReader(f,
                fieldnames=["date", "country", "new_cases", "new_deaths", "total_cases", "total_deaths"])
            corona = [r for r in reader]
            
        return (countries, corona)


    if download:
        raw_csv = download_files(url, corona_file)

    raw_csv = load_files()

    return raw_csv


def process_csv(raw_csv):
    """Clean up numbers, compute ratios proportional to population size"""

    myint = lambda s: int(s) if s.isdigit() else 0

    raw_countries, raw_corona = raw_csv

    countries = dict( ( (x[0], x[-1]) for x in raw_countries) ) 

    corona = defaultdict(dict)

    for country, countrygroup in groupby(raw_corona, lambda x: x['country']):
        if country == "International":
            # That is just those cruise ships, not so interesting 
            continue 
        
        it = dropwhile(lambda x: x['new_cases'] == '' or int(x['new_cases']) < 50, countrygroup)
        first = next(it, None)
        if first: 
            corona[country] = {'start': first['date'],
                                'new_cases': [myint(first['new_cases'])],
                                'new_deaths': [myint(first['new_deaths'])],
                                'total_cases': [myint(first['total_cases'])],
                                'total_deaths': [myint(first['total_deaths'])],
                                'population': int(countries[first['country']])
                                              if first['country'] in countries else 0,
                              }

            for rest in it:
                corona[country]['new_cases'].append(myint(rest['new_cases']))
                corona[country]['new_deaths'].append(myint(rest['new_deaths']))
                corona[country]['total_cases'].append(myint(rest['total_cases']))
                corona[country]['total_deaths'].append(myint(rest['total_deaths']))

            if corona[country]['population'] > 0: 
                for k in ('new_cases', 'new_deaths', 'total_cases', 'total_deaths'):
                    try: 
                        corona[country][k + "_relative"] = [float(x)/corona[country]['population']
                                                        if x > 0 else 0
                                                        for x in corona[country][k] ]
                        corona[country][k + "_relative_log"] = [log10(float(x))/corona[country]['population']
                                                        if x > 0 else 0
                                                        for x in corona[country][k] ]
                    except ValueError:
                        print(corona[country][k])


    return corona 


def visualize(corona, mincases, mindays):

    fields = (        
        ('total_cases', 'Total cases', 'Total', 0, 0,),
        ('total_deaths', 'Total deaths',  'Total', 0, 1, ),
        ('total_cases_relative', 'Total cases, relative to population', "Relative to population", 1, 0, ),
        ('total_deaths_relative', 'Total deaths, relative to population', "Relative to population", 1, 1, ),
        )

    fig, ax = plt.subplots(2, 2)

    for field, title, valuelabel, x, y,  in fields: 

        ax[x][y].set_title(title)
        ax[x][y].set_xlabel("Days since {} total cases".format(mincases))
        ax[x][y].set_ylabel(valuelabel)

        ax[x][y].set_prop_cycle(color=plt.cm.Spectral([x/12 for x in range(12)]),
                          marker=['o', '+', 'x'] * 4)

        for country, values in corona.items():

            if field not in values:
                print("Skipping, value not present : ", country, field)
                continue
            if len(values[field]) < mindays:
                print("Skipping, country not enough days : ", country)
                continue
            
            ax[x][y].semilogy(values[field], label=country)
            
        ax[x][y].grid()
        ax[x][y].legend()

    plt.show()
    

@click.command()
@click.option('--download/--no-download', default=False, help="Should new values be downloaded from URL")
@click.option('-p', '--population', default="population-figures-by-country-csv_csv.csv", help="File from which population data should be obtained")
@click.option('-c', '--corona', default="full_data.csv", help="Where is data stored (overwritten upon download")
@click.option('-m', '--mincases', default=50, help="Minimum total cases before country is considered")
@click.option('-u', '--url', default="https://covid.ourworldindata.org/data/full_data.csv", help="From where should Corona data be downloaded?")
@click.option('-d', '--days', default=10, help="Minimum number of days (after threshold) for which data must be available bbefore considering country in visualization")
# @click.option('-s', '--status', default=False, help="Show status information")
def main(download, population, corona, mincases, url, days):
    raw_csv = get_data(download, population, corona, url)
    data = process_csv(raw_csv)
    visualize(data, mincases, days) 

if __name__ == '__main__':
    main()

