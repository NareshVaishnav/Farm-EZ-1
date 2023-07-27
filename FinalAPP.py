from flask import Flask, render_template, request, redirect, url_for
from geopy.geocoders import Nominatim
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import folium
from flask_cors import CORS
from flask_pymongo import PyMongo
sns.set()

app = Flask(__name__)


CORS(app)

app.config['MONGO_DBNAME'] = 'FarmEz'
app.config['MONGO_URI'] = 'mongodb+srv://nareshvaishnavrko11:nareshrko11@cluster0.hudqzdr.mongodb.net/FarmEz'

mongo = PyMongo(app)


raw_data = pd.read_csv('FinalDataset2.csv')
raw_data = raw_data.drop(['Latitude', 'Longitude'], axis=1)

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/popup')
def popup():
    return render_template('popup.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/crop')
def home():
    return render_template('cindex.html')


@app.route('/chart', methods=['POST'])
def chart():
    
    raw_data['DISTRICT_NAME'] = raw_data['DISTRICT_NAME'].str.replace(' ', '')
    district = request.form['district']
    df = raw_data[raw_data['DISTRICT_NAME'] == district]
    
    df_sum = df.append(df.sum(numeric_only=True), ignore_index=True)
    sum_row = df_sum.iloc[[-1]]
    n_row = sum_row.drop('DISTRICT_NAME', axis=1)
    p_row = n_row.drop('TALUKA_NAME', axis=1)
    q_row = p_row.astype(int)
    max_row = q_row.loc[q_row.sum(axis=1).idxmax()]
    max_col = max_row.idxmax()
    row_to_analyze = q_row.iloc[0]
    top_5 = row_to_analyze.nlargest(5).index.tolist()
    
    crop1 = request.form['crop1']
    crop2 = request.form['crop2']
    crop3 = request.form['crop3']
    crop4 = request.form['crop4']
    crop5 = request.form['crop5']

    selected_crops = [crop1, crop2, crop3, crop4, crop5]
    lat_df = sum_row[selected_crops]

    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(20, 10))
    plt.figure(figsize=(8, 6))
    sns.set_style('whitegrid')
    palette = 'Paired'
    ax = sns.barplot(data=lat_df, palette=palette)
    ax.tick_params(labelsize=12)
    ax.set_xlabel('Crops', fontsize=14)
    ax.set_ylabel('Yield', fontsize=14)
    ax.set_title('Crop Yield by Crop Type', fontsize=18)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('static/chart1.png')


    colors = sns.color_palette('Paired')
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(lat_df.values[0], colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, 
                                    wedgeprops=dict(width=0.6, edgecolor='w'))
    ax.set_title('Pie Chart', fontsize=15)
    ax.legend(wedges, lat_df.columns, title='Crops', loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
    plt.tight_layout()
    plt.savefig('static/chart2.png', bbox_inches='tight')

    # selected_crops = [crop1, crop2, crop3, crop4, crop5]
    top_districts = []
    for i in selected_crops:
        crop_data = raw_data[['DISTRICT_NAME'] + [i]]
        crop_data = crop_data.groupby('DISTRICT_NAME').sum().reset_index()
        crop_data['Total'] = crop_data[[i]].sum(axis=1)
        crop_data = crop_data.sort_values('Total', ascending=False).reset_index(drop=True)
        top_3 = crop_data.head(3)['DISTRICT_NAME'].tolist()
        top_districts.append((i, top_3))

        
    crops = []
    for crop in selected_crops:
        if lat_df[crop].iloc[0] == 0:
            crops.append((crop, f'does not grow in {district}.'))
        else:
            crops.append((crop, f'grows in {district}.'))

    return render_template('cindex.html', crops=crops, max_crop=max_col, top_5=top_5, top_districts=top_districts)

farmers_data = pd.read_csv('F_Dataset.csv')
farmers_data['District'] = farmers_data['District'].str.strip()

@app.route('/farmer')
def farmindex():
    return render_template('findex.html')

@app.route('/submit', methods=['POST'])
def register():
    if request.method == 'POST':
        fullName = request.form['full-name']
        Age = request.form['Age']
        email = request.form['email']
        phone = request.form['phone']
        district = request.form['district']
        taluka = request.form['taluka']
        landsize = request.form['landsize']
        address = request.form['address']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        otherinfo = request.form['other-info']
        mongo.db.farmers.insert_one({
            'full-name': fullName,
            'Age': Age,
            'email': email,
            'phone': phone,
            'district': district,
            'taluka': taluka,
            'landsize': landsize,
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'other-info': otherinfo
        })
        # Redirect to success page...
        return redirect(url_for('popup'))
    else:
        return 'Error'

@app.route('/map', methods=['GET', 'POST'])
def display_map():

    if request.method == 'POST':
        district = request.form['district'].strip()

        # Query the MongoDB database for the latitude and longitude of the given district
        # and store the results in a list of dictionaries
        locations = list(mongo.db.farmers.find({'district': district}, {'_id': 0, 'latitude': 1, 'longitude': 1}))
        if not locations:
            return render_template('mindex.html', district=district, error='No records found for this district.')
        # Create a Folium map centered on the first location in the list
        map = folium.Map(location=[locations[0]['latitude'], locations[0]['longitude']], zoom_start=10)
        # Add markers for all the locations in the list
        for location in locations:
            # Query the MongoDB database for the user information
            row = mongo.db.farmers.find_one({'district': district, 'latitude': location['latitude'], 'longitude': location['longitude']})
            # Create a string with the user information to be displayed in the pop-up
            # if user_info is not None:
            popup_html = f'<table style="width: 300px;"><tr><th>Farmer Name:</th><td>{row["full-name"]}</td></tr><tr><th>Phone No:</th><td>{row["phone"]}</td></tr><tr><th>Land size:</th><td>{row["landsize"]} acre</td></tr></table>'
            folium.Marker(location=[location['latitude'], location['longitude']], popup=popup_html).add_to(map)

        # Convert the map to HTML and pass it to the template
        map_html = map._repr_html_()
        return render_template('mindex.html', district=district, map_html=map_html)

    # If the request method is not 'POST', return the default map page
    return render_template('mindex.html', district='', map_html='', error='')

########---------Hindi Routes-------########

@app.route('/hi')
def hindiindex():
    return render_template('index_hi.html')

@app.route('/hisignin')
def hindisignin():
    return render_template('signin_hi.html')

@app.route('/hisignup')
def hindisignup():
    return render_template('signup_hi.html')

@app.route('/hiabout')
def hindiin():
    return render_template('aboutus_hi.html')

@app.route('/hicontact')
def hindicontact():
    return render_template('contact_hi.html')

@app.route('/hipopup')
def hindipopup():
    return render_template('popup_hi.html')


@app.route('/himap', methods=['GET', 'POST'])
def himapindex():
    if request.method == 'POST':
        district = request.form['district'].strip()

        # Query the MongoDB database for the latitude and longitude of the given district
        # and store the results in a list of dictionaries
        locations = list(mongo.db.farmers.find({'district': district}, {'_id': 0, 'latitude': 1, 'longitude': 1}))
        if not locations:
            return render_template('mindex_hi.html', district=district, error='No records found for this district.')
        # Create a Folium map centered on the first location in the list
        map = folium.Map(location=[locations[0]['latitude'], locations[0]['longitude']], zoom_start=10)
        # Add markers for all the locations in the list
        for location in locations:
            # Query the MongoDB database for the user information
            row = mongo.db.farmers.find_one({'district': district, 'latitude': location['latitude'], 'longitude': location['longitude']})
            # Create a string with the user information to be displayed in the pop-up
            popup_html = f'<table style="width: 300px;"><tr><th>Farmer Name:</th><td>{row["full-name"]}</td></tr><tr><th>Phone No:</th><td>{row["phone"]}</td></tr><tr><th>Land size:</th><td>{row["landsize"]} acre</td></tr></table>'
            # Add a marker with the pop-up to the map
            folium.Marker(location=[location['latitude'], location['longitude']], popup=popup_html,icon=folium.Icon(color='darkgreen')).add_to(map)
        # Convert the map to HTML and pass it to the template
        map_html = map._repr_html_()
        return render_template('mindex_hi.html', district=district, map_html=map_html)

    # If the request method is not 'POST', return the default map page
    return render_template('mindex_hi.html', district='', map_html='', error='')

@app.route('/hifarmer')
def hifarmindex():
    return render_template('findex_hi.html')

@app.route('/hisubmit', methods=['POST'])
def hisubmit():
    if request.method == 'POST':
        fullName = request.form['full-name']
        Age = request.form['Age']
        email = request.form['email']
        phone = request.form['phone']
        district = request.form['district']
        taluka = request.form['taluka']
        landsize = request.form['landsize']
        address = request.form['address']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        otherinfo = request.form['other-info']
        mongo.db.farmers.insert_one({
            'full-name': fullName,
            'Age': Age,
            'email': email,
            'phone': phone,
            'district': district,
            'taluka': taluka,
            'landsize': landsize,
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'other-info': otherinfo
        })
        # Redirect to success page...
        return redirect(url_for('popup'))
    else:
        return 'Error'
@app.route('/hicrop')
def hicrop():
    return render_template('cindex_hi.html')

@app.route('/hichart', methods=['POST'])
def hichart():
    
    raw_data['DISTRICT_NAME'] = raw_data['DISTRICT_NAME'].str.replace(' ', '')
    district = request.form['district']
    df = raw_data[raw_data['DISTRICT_NAME'] == district]
    
    df_sum = df.append(df.sum(numeric_only=True), ignore_index=True)
    sum_row = df_sum.iloc[[-1]]
    n_row = sum_row.drop('DISTRICT_NAME', axis=1)
    p_row = n_row.drop('TALUKA_NAME', axis=1)
    q_row = p_row.astype(int)
    max_row = q_row.loc[q_row.sum(axis=1).idxmax()]
    max_col = max_row.idxmax()
    row_to_analyze = q_row.iloc[0]
    top_5 = row_to_analyze.nlargest(5).index.tolist()
    
    crop1 = request.form['crop1']
    crop2 = request.form['crop2']
    crop3 = request.form['crop3']
    crop4 = request.form['crop4']
    crop5 = request.form['crop5']

    selected_crops = [crop1, crop2, crop3, crop4, crop5]
    lat_df = sum_row[selected_crops]

    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(20, 10))
    plt.figure(figsize=(8, 6))
    sns.set_style('whitegrid')
    palette = 'Paired'
    ax = sns.barplot(data=lat_df, palette=palette)
    ax.tick_params(labelsize=12)
    ax.set_xlabel('Crops', fontsize=14)
    ax.set_ylabel('Yield', fontsize=14)
    ax.set_title('Crop Yield by Crop Type', fontsize=18)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('static/chart1.png')


    colors = sns.color_palette('Paired')
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(lat_df.values[0], colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, 
                                    wedgeprops=dict(width=0.6, edgecolor='w'))
    ax.set_title('Pie Chart', fontsize=15)
    ax.legend(wedges, lat_df.columns, title='Crops', loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
    plt.tight_layout()
    plt.savefig('static/chart2.png', bbox_inches='tight')

    # selected_crops = [crop1, crop2, crop3, crop4, crop5]
    top_districts = []
    for i in selected_crops:
        crop_data = raw_data[['DISTRICT_NAME'] + [i]]
        crop_data = crop_data.groupby('DISTRICT_NAME').sum().reset_index()
        crop_data['Total'] = crop_data[[i]].sum(axis=1)
        crop_data = crop_data.sort_values('Total', ascending=False).reset_index(drop=True)
        top_3 = crop_data.head(3)['DISTRICT_NAME'].tolist()
        top_districts.append((i, top_3))

        
    crops = []
    for crop in selected_crops:
        if lat_df[crop].iloc[0] == 0:
            crops.append((crop, f'does not grow in {district}.'))
        else:
            crops.append((crop, f'grows in {district}.'))

    return render_template('cindex_hi.html', crops=crops, max_crop=max_col, top_5=top_5, top_districts=top_districts)

#---------------Marathi Routes-------------

@app.route('/ma')
def marathiindex():
    return render_template('index_ma.html')

@app.route('/masignin')
def marathisignin():
    return render_template('signin_ma.html')

@app.route('/masignup')
def marathisignup():
    return render_template('signup_ma.html')

@app.route('/maabout')
def marathiin():
    return render_template('aboutus_ma.html')

@app.route('/macontact')
def marathicontact():
    return render_template('contact_ma.html')

@app.route('/mapopup')
def marathipopup():
    return render_template('popup_ma.html')

@app.route('/mamap', methods=['GET', 'POST'])
def mamapindex():
    if request.method == 'POST':
        district = request.form['district'].strip()

        # Query the MongoDB database for the latitude and longitude of the given district
        # and store the results in a list of dictionaries
        locations = list(mongo.db.farmers.find({'district': district}, {'_id': 0, 'latitude': 1, 'longitude': 1}))
        if not locations:
            return render_template('mindex_ma.html', district=district, error='No records found for this district.')
        # Create a Folium map centered on the first location in the list
        map = folium.Map(location=[locations[0]['latitude'], locations[0]['longitude']], zoom_start=10)
        # Add markers for all the locations in the list
        for location in locations:
            # Query the MongoDB database for the user information
            row = mongo.db.farmers.find_one({'district': district, 'latitude': location['latitude'], 'longitude': location['longitude']})
            # Create a string with the user information to be displayed in the pop-up
            popup_html = f'<table style="width: 300px;"><tr><th>Farmer Name:</th><td>{row["full-name"]}</td></tr><tr><th>Phone No:</th><td>{row["phone"]}</td></tr><tr><th>Land size:</th><td>{row["landsize"]} acre</td></tr></table>'
            # Add a marker with the pop-up to the map
            folium.Marker(location=[location['latitude'], location['longitude']], popup=popup_html).add_to(map)
        # Convert the map to HTML and pass it to the template
        map_html = map._repr_html_()
        return render_template('mindex_ma.html', district=district, map_html=map_html)

    # If the request method is not 'POST', return the default map page
    return render_template('mindex_ma.html', district='', map_html='', error='')

@app.route('/mafarmer')
def mafarmindex():
    return render_template('findex_ma.html')

@app.route('/masubmit', methods=['POST'])
def masubmit():
    if request.method == 'POST':
        fullName = request.form['full-name']
        Age = request.form['Age']
        email = request.form['email']
        phone = request.form['phone']
        district = request.form['district']
        taluka = request.form['taluka']
        landsize = request.form['landsize']
        address = request.form['address']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        otherinfo = request.form['other-info']
        mongo.db.farmers.insert_one({
            'full-name': fullName,
            'Age': Age,
            'email': email,
            'phone': phone,
            'district': district,
            'taluka': taluka,
            'landsize': landsize,
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'other-info': otherinfo
        })
        # Redirect to success page...
        return redirect(url_for('popup'))
    else:
        return 'Error'

@app.route('/macrop')
def macrop():
    return render_template('cindex_ma.html')

@app.route('/machart', methods=['POST'])
def machart():
    
    raw_data['DISTRICT_NAME'] = raw_data['DISTRICT_NAME'].str.replace(' ', '')
    district = request.form['district']
    df = raw_data[raw_data['DISTRICT_NAME'] == district]
    
    df_sum = df.append(df.sum(numeric_only=True), ignore_index=True)
    sum_row = df_sum.iloc[[-1]]
    n_row = sum_row.drop('DISTRICT_NAME', axis=1)
    p_row = n_row.drop('TALUKA_NAME', axis=1)
    q_row = p_row.astype(int)
    max_row = q_row.loc[q_row.sum(axis=1).idxmax()]
    max_col = max_row.idxmax()
    row_to_analyze = q_row.iloc[0]
    top_5 = row_to_analyze.nlargest(5).index.tolist()
    
    crop1 = request.form['crop1']
    crop2 = request.form['crop2']
    crop3 = request.form['crop3']
    crop4 = request.form['crop4']
    crop5 = request.form['crop5']

    selected_crops = [crop1, crop2, crop3, crop4, crop5]
    lat_df = sum_row[selected_crops]

    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(20, 10))
    plt.figure(figsize=(8, 6))
    sns.set_style('whitegrid')
    palette = 'Paired'
    ax = sns.barplot(data=lat_df, palette=palette)
    ax.tick_params(labelsize=12)
    ax.set_xlabel('Crops', fontsize=14)
    ax.set_ylabel('Yield', fontsize=14)
    ax.set_title('Crop Yield by Crop Type', fontsize=18)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('static/chart1.png')


    colors = sns.color_palette('Paired')
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(lat_df.values[0], colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, 
                                    wedgeprops=dict(width=0.6, edgecolor='w'))
    ax.set_title('Pie Chart', fontsize=15)
    ax.legend(wedges, lat_df.columns, title='Crops', loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
    plt.tight_layout()
    plt.savefig('static/chart2.png', bbox_inches='tight')

    # selected_crops = [crop1, crop2, crop3, crop4, crop5]
    top_districts = []
    for i in selected_crops:
        crop_data = raw_data[['DISTRICT_NAME'] + [i]]
        crop_data = crop_data.groupby('DISTRICT_NAME').sum().reset_index()
        crop_data['Total'] = crop_data[[i]].sum(axis=1)
        crop_data = crop_data.sort_values('Total', ascending=False).reset_index(drop=True)
        top_3 = crop_data.head(3)['DISTRICT_NAME'].tolist()
        top_districts.append((i, top_3))

        
    crops = []
    for crop in selected_crops:
        if lat_df[crop].iloc[0] == 0:
            crops.append((crop, f'does not grow in {district}.'))
        else:
            crops.append((crop, f'grows in {district}.'))

    return render_template('cindex_ma.html', crops=crops, max_crop=max_col, top_5=top_5, top_districts=top_districts)


if __name__ == '__main__':
    app.run(port=5500, debug=True)
