## Project 1 part 1: An Analysis of U.S. Petroleum Product Supplied Data 
team: giggling wombat

### What dataset are you going to use?

Link: https://www.eia.gov/opendata/browser/petroleum/cons/wpsup

### What are your research question(s)?

How does the U.S. petroleum product supply change on a weekly basis over time?

Are there clear seasonal patterns or a regular annual change that happens for petroleum product supply?

To what extent do major economic and societal disruptions (e.g., the COVID-19 period, after the Paris Agreement) impact the volume of U.S. petroleum demand?

### Link to notebook: https://github.com/advanced-computing/giggling-wombat/blob/main/project.ipynb

### Target Visualization Description

The primary visualization will be a time-series line chart displaying weekly petroleum products supplied in the U.S.

X-axis: Week

Y-axis: Petroleum product supplied per week
Optional features: Vertical reference line to show specific events


### What are your known unknowns?

Weekly oil supply fluctuates constantly due to specific events. However, since not all of these events can be individually specified, some external factors remain 'known unknowns' in this field.

Which external factors (seasonality, economic shocks, policy changes) most strongly influence short-term fluctuations. 

It is not yet known whether recent years alone or a longer historical period will best highlight relevant trends.

### What challenges do you anticipate?

Short-term volatility may obscure longer-term patterns

Interpreting whether observed changes reflect demand-side behavior or reporting adjustments

So many events that distort oil supply every day, it is challenging to specify all of the events

The data source does not support direct CSV downloads, requiring the use of an API. This presents a challenge for my typical workflow, which usually begins with a downloaded CSV file to start a project.
