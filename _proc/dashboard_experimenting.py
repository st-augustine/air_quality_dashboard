# %%
import pandas as pd
import streamlit as st 
import numpy as np
import requests
from datetime import date, datetime, timedelta
import sqlite_utils
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import plotly.express as px
#import functions

# %%

st.set_page_config(layout = "wide")
st.title("Air quality")
st.text('This is a web app showing air quality in Tower Hamlets')

# %%
# SETUP DATABASE, TABLE AND SCHEMA
db = sqlite_utils.Database("air-sensors.db")
# WE ARE ONLY COLLECTING NO2 AS THIS IS THE ONLY PARTICLE THAT IS MEASURED AT ALL SITES
tablename = 'NO2'
table = db.table(
    tablename,
    pk=('@MeasurementDateGMT', '@Site'), # pk (primary keys) are columns that uniquely identify each row in the table  
    not_null={"@MeasurementDateGMT", "@Value", "@Site"},# constrains a column so it cannot contain null values 
    column_order=("@MeasurementDateGMT", "@Value", "@Site") #
)

# %%
# EXTRACT THE SITES IN TOWER HAMLETS
#api is link between between us and database 
req = requests.get("https://api.erg.ic.ac.uk/AirQuality/Information/MonitoringSiteSpecies/GroupName=towerhamlets/Json") #requests gets the info from the api 
js = req.json() #json is like a python dictionary 
sites = js['Sites']['Site'] #turns dictionary into list 

# %%
# PREPARE TO SCAN DATA FOR THE LAST 1 WEEK
EndDate = date.today() + timedelta(days = 1)
EndWeekDate = EndDate
StartWeekDate = EndDate - timedelta(weeks = 2)
StartDate = StartWeekDate - timedelta(days = 1)


# %%
# GET THE JSON DATA, UPSERT INTO THE FULL HISTORY DATABASE
while StartWeekDate > StartDate :
    for el in sites:
        url = f'https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/SiteCode={el["@SiteCode"]}/SpeciesCode=NO2/StartDate={StartWeekDate.strftime("%d %b %Y")}/EndDate={EndWeekDate.strftime("%d %b %Y")}/Json'
        print(url)
        req = requests.get(url, headers={'Connection':'close'}) #closes connection to the api
        j = req.json()
        # CLEAN SITES WITH NO DATA OR ZERO VALUE OR NOT NO2 (ONLY MEASURE AVAILABLE AT ALL SITES)
        filtered = [a for a in j['RawAQData']['Data'] if a['@Value'] != '' and a['@Value'] != '0' ] #removes zero and missing values 
        print(filtered)
        if len(filtered) != 0:
            #filtered = functions.convert(filtered, filtered[1], filtered[2], el)
            for element in filtered:
                 element['@Value']=float(element['@Value'])
                 element['@Site']=el['@SiteName']
            filteredList = list(filtered)
            db[tablename].upsert_all(filteredList,pk=('@MeasurementDateGMT', '@Site')) #combo of update and insert, updates record if it already exists if not creates it 
    EndWeekDate = StartWeekDate
    StartWeekDate = EndWeekDate - timedelta(weeks = 2)

# %%
#turns sqlite database into a python database 
conn= sqlite3.connect('air-sensors.db')
sql= """SELECT * FROM NO2; """
data = pd.read_sql(sql, conn)


# %%
fig = px.line(data, x= '@MeasurementDateGMT', y= '@Value', color='@Site',width=1200, height= 700)

fig.update_layout(title='',
                   xaxis_title='Measurement Date',
                   yaxis_title='NO<sub>2</sub> Concentration (µg/m<sup>3</sup>)',
                   legend=dict(orientation="h", entrywidth=250,
                   yanchor="bottom", y=1.02, xanchor="right", x=1),
                   legend_title_text= '', font=dict(size= 18)
                   )

fig.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
fig.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))

#print("plotly express hovertemplate:", fig.data[0].hovertemplate)

fig.update_traces(hovertemplate='<b>Measurement time (GMT) = </b>%{x}<br><b>Value = </b>%{y}<extra></extra>')

fig.update_layout(hoverlabel = dict(
    font_size = 16))

fig.add_hline(y=40,line_dash='dot')

#fig.add_annotation(x=20,y=40, text='Maximum target concentration', showarrow=False,yshift=10)

fig.show()

st.plotly_chart(fig,theme=None)


