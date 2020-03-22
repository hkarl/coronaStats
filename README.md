# coronaStats

Visualize corona statistics. Lot's of online graphs don't make much
sense as they show an exponential process (epidemic spread) on a
linear axis. Here, we use logarithmic scale for better visualization.  

## Sources 

* Corona data from
  https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/
* Population data from
  https://datahub.io/JohnSnowLabs/population-figures-by-country
  
Population is a bit outdated, but probably does not make 

## Approach 

* Filter out countries with too few days or too few cases. That would
  overburden the graph. 
* That noteably removes the interesting special cases of Taiwan and
  Singapore. I encoure everybody to look at the original data for
  that. 
* Several countries (China, US, France, UK) need to be aggregated to
  make sense. Look at get_csv in the code for details. 
  
## Improvements 

Pull requests welcome! 

## Current statistics 

### Bitmap 

![Corona Statistics](corona_stats.png) 

### PDF 

<a href="https://hkarl.github.io/coronaStats/corona_stats.pdf"> PDF </a>
