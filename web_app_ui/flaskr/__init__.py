from flask import (Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for)
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import requests as req
import csv
# Create and configure the app
app = Flask(__name__)
app.config.from_mapping(SECRET_KEY='dev')


# Load data from the model


# Route for the home page
@app.route('/', methods=('GET', 'POST'))
def map_func():

    df = pd.read_csv('flaskr/static/final_prediction_agg_10.csv', index_col=0)
    df = df[df.pred==1] # keep information on areas to avoid

    if request.method == 'POST':
        # Retrieve user entered info
        origin = request.form['origin']
        destination = request.form["destination"]
        report = request.form["report"]

        #destination = request.form['destination']
        time = request.form.get('time')
        error = None

        # Check for required inputs
        if not origin:
            error = 'Origin is required.'

        if not destination:
            error = 'Destinatipn is required'




        # Calculate areas to avoid within the active region of the route
        if error is None:
            GOOGLE_API_KEY = 'AIzaSyDwV-f6BqltCAtwrl21AWHs9qODkoqRVn4'
            api_key = GOOGLE_API_KEY
            base_url = "https://maps.googleapis.com/maps/api/geocode/json"
            endpoint = f"{base_url}?address={origin}&key={api_key}"

            r = req.get(endpoint)


            results = r.json()['results'][0]
            origin = str(results['geometry']['location']['lat']) + "," + str(results['geometry']['location']['lng'])


            base_url = "https://maps.googleapis.com/maps/api/geocode/json"
            endpoints = f"{base_url}?address={destination}&key={api_key}"
            r = req.get(endpoints)


            results = r.json()['results'][0]
            destination = str(results['geometry']['location']['lat']) + "," + str(results['geometry']['location']['lng'])

            if report is not None and len(report) > 0:
                base_url = "https://maps.googleapis.com/maps/api/geocode/json"
                endpoint = f"{base_url}?address={report}&key={api_key}"
                r = req.get(endpoint)
                results = r.json()['results'][0]
                report = str(results['geometry']['location']['lat']) + "," + str(results['geometry']['location']['lng'])
            else:
                report = None

            val = 0.009
            report_latlon = None
            org_latlon = list(map(float, origin.split(',')))
            dest_latlon = list(map(float, destination.split(',')))
            if report is not None:
                report_latlon = list(map(float, report.split(',')))



            # Calculate active region of the route
            lat_min = min(org_latlon[0],dest_latlon[0])
            lat_max = max(org_latlon[0],dest_latlon[0])
            lon_min = min(org_latlon[1],dest_latlon[1])
            lon_max = max(org_latlon[1],dest_latlon[1])


            # Find top 10 relevant areas to avoid
            avoid = df[(df.NewLat.between(lat_min-val*np.sign(lat_min), lat_max+val*np.sign(lat_max))) &
                       (df.NewLon.between(lon_min+val*np.sign(lon_min), lon_max-val*np.sign(lon_max))) &
                       (df['Time Seg']==time)]
            avoid = avoid.sort_values('Weight', ascending=False)




            # Define avoid input value for the API
            avoid_list = avoid[['NewLat','NewLon']].apply(lambda x: 'bbox:' + str(x['NewLon']-0.00125) +
                                                          ',' + str(x['NewLat']-0.00125) + ',' + str(x['NewLon']+0.00125) +
                                                          ',' + str(x['NewLat']+0.00125), axis=1).values


            print("latlon", report_latlon)


            avoid_param = '|'.join(avoid_list)

            avoid_lat = ','.join([str(lat) for lat in avoid.NewLat])
            avoid_lon = ','.join([str(lon) for lon in avoid.NewLon])

            if report_latlon is not None:
                avoid_lat = avoid_lat + "," + str(report_latlon[0])
                avoid_lon = avoid_lon +"," + str(report_latlon[1])
                csv_row_m = ["0", str(report_latlon[0]), str(report_latlon[1]), "Morning", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "Oceanview/Merced/Ingleside", "4.5", "20", "20", "1"]
                joined_string1 = ",".join(csv_row_m)
                csv_row_a = ["0", str(report_latlon[0]), str(report_latlon[1]), "Afternoon", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "Oceanview/Merced/Ingleside", "4.5", "20", "20", "1"]
                joined_string2 = ",".join(csv_row_a)
                csv_row_e = ["0", str(report_latlon[0]), str(report_latlon[1]), "Evening", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "Oceanview/Merced/Ingleside", "4.5", "20", "20", "1"]
                joined_string3 = ",".join(csv_row_e)
                with open('flaskr/static/final_prediction_agg_10.csv','a') as fd:
                    fd.write(joined_string1)
                    fd.write("\n")
                    fd.write(joined_string2)
                    fd.write("\n")
                    fd.write(joined_string3)
                    fd.write("\n")


            return render_template('map_sf_route.html',
                                   org_input=origin,
                                   org_dest=destination,
                                   time=time,
                                   avoid_bbox=avoid_param,
                                   avoid_lat=avoid_lat,
                                   avoid_lon=avoid_lon)

    return render_template('map_sf.html')

if __name__ == '__main__':
    app.run(debug = True)
