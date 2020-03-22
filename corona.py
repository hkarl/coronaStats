"""Download and visualiaze corona numbers.
Based on: 
- Use https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series 
- Population data from https://datahub.io/JohnSnowLabs/population-figures-by-country (more up to date useful)
"""

import csv, sys, io

from pprint import pprint as pp
from collections import defaultdict 
from itertools import groupby, dropwhile
from math import log10 
import datetime

import click 
import requests

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

debug = False 
baseUrl = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/" 
filenames = (
    "time_series_19-covid-Confirmed.csv",
    "time_series_19-covid-Deaths.csv",
    "time_series_19-covid-Recovered.csv", 
    )


thresholds = {
    "Confirmed": {'Days': 18, 'Cases': 50}, 
    "Confirmed_relative": {'Days': 18, 'Cases': 50},
    # 
    "Deaths": {'Days': 5, 'Cases': 10}, 
    "Deaths_relative": {'Days': 5, 'Cases': 10},
    # 
    "Recovered": {'Days': 10, 'Cases': 20}, 
    "Recovered_relative": {'Days': 10, 'Cases': 20}, 
    }
    
   
def load_population(countries_file):
    with open(countries_file, "r", newline='') as f:
        next(f)  # skip header 
        reader = csv.reader(f)
        countries = [r for r in reader]

    return countries 

def download_files(baseUrl, filenames):
    data = {}
    for fn in filenames: 
        r = requests.get(baseUrl + fn)
        data[fn] = str(r.text)
        with open(fn, 'w') as f:
            f.write(data[fn])

    return data 
        
def load_files(filenames):
    data = {}
    for fn in filenames: 
        with open(fn, "r") as f:
            data[fn] = f.read()

    return data 

def get_csv(data):
    """ turn raw data into useful CSV output"""

    dataout = {}
    for k, v in data.items():
        reader = csv.DictReader(io.StringIO(v), delimiter=",")
        temp_entries = [r for r in reader]

        temp_entries_with_dates = []
        
        # Some immediate cleanup:
        for r in temp_entries:
            # ensure consistency with population data (fix US later for different counties): 
            if r['Country/Region'] == 'Korea, South':
                r['Country/Region'] = 'South Korea'

            # turn numbers into numbers; dates into dates 
            tmp = {'Country/Region': r['Country/Region'],
                    'Province/State': r['Province/State'],
                    'dates': defaultdict(int),
                    }
                
            for kk, vv in r.items():
                #  dates into dates, get the integer value:
                try:
                    kk_date = datetime.datetime.strptime(kk, "%m/%d/%y")
                    tmp['dates'][kk_date] = int(vv)
                except Exception:
                    pass

            temp_entries_with_dates.append(tmp)

        # Summarize for China, US:
        summarize_countries = ("China", "US", "France", "United Kingdom")
        for s in summarize_countries:
            counties = [r for r in temp_entries_with_dates if r['Country/Region'] == s]
            new_entry = counties[0].copy()
            new_entry['Province/State'] = ""
            new_entry['dates'] = {}
            relevant_dates = set([x for r in counties for x in list(r['dates'].keys()) ])
            
            for kk in relevant_dates:
                new_entry['dates'][kk] = sum( r['dates'][kk] for r in counties  )

            if new_entry['Country/Region'] == 'US':
                new_entry['Country/Region'] = 'United States'

            if debug: 
                print("Filtering: ", s)
                pp(new_entry)
                
            temp_entries_with_dates.append(new_entry)

        # filter out provinces
        actual_key = k[1+k.rfind('-'):-4]
        dataout[actual_key] = [r for r in temp_entries_with_dates if r['Province/State'] == ""]
        
    if debug:  
        pp(dataout)
    # pp(dataout.keys())
    return dataout


def process_csv(population_data, corona_csv):
    """Clean up numbers, compute ratios proportional to population size"""

    if debug: 
        print("=======================")

    countries = dict( ( (x[0], x[-1]) for x in population_data) ) 

    corona = defaultdict(dict)

    for statistics_key, countrylist in corona_csv.items():
        for country in countrylist:
            countryname = country['Country/Region']
            if debug: 
                print(statistics_key, country['Country/Region'])
                
            # only consider country if it has at least a certain mimimum number of days 
            if len(country['dates'].keys()) < thresholds[statistics_key]['Days']:
                continue

            # only consider country if it has a certain minimum number of cases
            if max(country['dates'].values()) < thresholds[statistics_key]['Cases']:
                continue
            
            
            values = [(k, country['dates'][k])
                          for k in sorted(country['dates'].keys())
                          if country['dates'][k] > thresholds[statistics_key]['Cases']
                          ]
            
            if len(values) < thresholds[statistics_key]['Days']:
                continue

            
            try:
                population = int(countries[countryname])
            except Exception:
                population = 0

            corona[countryname].update({
                'start': values[0][0],
                'population': population})
            corona[countryname][statistics_key] = [v[1] for v in values] 
            corona[countryname][statistics_key + "_relative"] =  [float(v[1]*100000)/float(population) for v in values ] if population > 0 else None 
            

    if debug: 
        pp(corona)
        
    return corona


def visualize(corona):

    fields = (
        # key, titel, label, subplot positions 
        ('Confirmed', 'Total cases', 'Absolute numbers', 0, 0,),
        ('Confirmed_relative', 'Total cases, relative to population', "Cases per 100.000", 1, 0, ),
        ('Deaths', 'Total deaths',  'Absolute numbers', 0, 1, ),
        ('Deaths_relative', 'Total deaths, relative to population', "Cases per 100.000", 1, 1, ),
        ('Recovered', 'Recovered cases', "Total", 0, 2, ),
        ('Recovered_relative', 'Recovered, relative to population', "Cases per 100.000", 1, 2, ),
        )

    fig, ax = plt.subplots(2, 3)

    for field, title, valuelabel, x, y,  in fields: 

        ax[x][y].set_title(title + " (at least {} days)".format(
            thresholds[field]['Days']) )        
        ax[x][y].set_xlabel("Days since {} cases".format(thresholds[field]['Cases']))
        ax[x][y].set_ylabel(valuelabel)

        
        count = len([1
                        for country, values in corona.items()
                        if field in values
                        and not values[field] == None
                        and len(values[field]) >= thresholds[field]['Days']
                    ])
                    

        color_count = (count // 3) + 2 
        ax[x][y].set_prop_cycle(color=plt.cm.Spectral([float(x)/(color_count*3) for x in range(color_count*3)]),
                          marker=['o', '+', 'x'] * color_count )

        if debug: 
            print (count, color_count) 
        
        for country, values in corona.items():

            if field not in values:
                print("Skipping, value not present : ", country, field)
                continue
            if values[field] == None:
                print("Skipping, value is None: ", country, field)
                continue
            
            if len(values[field]) < thresholds[field]['Days']:
                print("Skipping, country not enough days : ", country, field)
                continue
            
            ax[x][y].semilogy(values[field], label=country)
            
        ax[x][y].grid()
        ax[x][y].legend()

    plt.show()
    

@click.command()
@click.option('--download/--no-download', default=False, help="Should new values be downloaded from URL")
@click.option('-g', '--graph/--no-graph', default=True, help="Show graph")
@click.option('-d', '--debug/--no-debug', default=False, help="Debug flag")
def main(download, population, graph, debug):
    if download:
        raw_data = download_files(baseUrl, filenames)
    else:
        raw_data = load_files(filenames) 

    population_data = load_population(population)

    corona_csv = get_csv(raw_data)

    data = process_csv(population_data, corona_csv)

    if graph: 
        visualize(data) 

if __name__ == '__main__':
    main()

