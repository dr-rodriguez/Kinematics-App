from flask import Flask, redirect, render_template, request
from druvw import xyz, uvw
import pandas as pd
from bokeh.plotting import figure, gridplot
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from astroquery.simbad import Simbad
import math
import numpy as np

app = Flask(__name__)

# Global Variables
app.vars = dict()
app.vars['ra'] = '165.46627797'
app.vars['dec'] = '-34.70473119'
app.vars['pmra'] = '-66.19'
app.vars['pmdec'] = '-13.90'
app.vars['rv'] = '13.40'
app.vars['dist'] = '53.7'
app.vars['name'] = ''

# Redirect to the main page
@app.route('/')
@app.route('/index')
@app.route('/index.html')
@app.route('/query.html')
def app_home():
    return redirect('/query')

# Main page for queries
@app.route('/query', methods=['GET', 'POST'])
def app_query():
    return render_template('query.html', ra=app.vars['ra'], dec=app.vars['dec'], pmra=app.vars['pmra'],
                           pmdec=app.vars['pmdec'], rv=app.vars['rv'], dist=app.vars['dist'], name=app.vars['name'])

# Calculate for known values
@app.route('/results', methods=['GET', 'POST'])
def app_results():
    # Grab the data
    for key in request.form.keys():
        app.vars[key] = request.form[key]

    # Convert to numbers
    df = dict()
    for key in app.vars:
        if key in ['name']: continue # don't convert
        temp = number_convert(app.vars[key])
        if math.isnan(temp):
            return render_template('error.html', headermessage='Error',
                                   errmess='<p>Error converting number: ' + app.vars[key] + '</p>')
        else:
            df[key] = temp

    # Calculate xyz, uvw
    x, y, z = xyz(df['ra'], df['dec'], df['dist'])
    u, v, w = uvw(df['ra'], df['dec'], df['dist'], df['pmra'], df['pmdec'], df['rv'])

    data = pd.DataFrame({'X': [x], 'Y': [y], 'Z': [z], 'U': [u], 'V': [v], 'W': [w]})

    source = ColumnDataSource(data=data)
    # Figures
    tools = "resize, pan, wheel_zoom, box_zoom, reset, lasso_select, box_select"
    plot_size = 350

    p1 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools)
    p1.scatter('X', 'Y', source=source)
    p1.xaxis.axis_label = 'X (pc)'
    p1.yaxis.axis_label = 'Y (pc)'

    p2 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools, x_range=p1.y_range)
    p2.scatter('Y', 'Z', source=source)
    p2.xaxis.axis_label = 'Y (pc)'
    p2.yaxis.axis_label = 'Z (pc)'

    p3 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools, x_range=p1.x_range, y_range=p2.x_range)
    p3.scatter('X', 'Z', source=source)
    p3.xaxis.axis_label = 'X (pc)'
    p3.yaxis.axis_label = 'Z (pc)'

    p4 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools)
    p4.scatter('U', 'V', source=source)
    p4.xaxis.axis_label = 'U (km/s)'
    p4.yaxis.axis_label = 'V (km/s)'

    p5 = figure(width=plot_size, plot_height=plot_size, title=None, x_range=p4.y_range, tools=tools)
    p5.scatter('V', 'W', source=source)
    p5.xaxis.axis_label = 'V (km/s)'
    p5.yaxis.axis_label = 'W (km/s)'

    p6 = figure(width=plot_size, plot_height=plot_size, title=None, x_range=p4.x_range, y_range=p5.y_range, tools=tools)
    p6.scatter('U', 'W', source=source)
    p6.xaxis.axis_label = 'U (km/s)'
    p6.yaxis.axis_label = 'W (km/s)'

    # Groups
    p1.oval(x=[1, 2, 3], y=[1, 2, 3], width=0.2, height=40, color="#CAB2D6",
           angle=0, height_units="screen")

    p = gridplot([[p1, p2, p3],[p4, p5, p6]], toolbar_location="left")
    script, div = components(p)

    return render_template('results.html', table=data.to_html(classes='display', index=False), script=script, plot=div)

# Called when you click Resolve on Simbad button
@app.route('/simbad', methods=['GET', 'POST'])
def app_simbad():
    app.vars['name'] = request.form['name']

    # Get the relevant information from Simbad
    customSimbad = Simbad()
    customSimbad.remove_votable_fields('coordinates')
    customSimbad.add_votable_fields('ra(d)', 'dec(d)', 'pmra', 'pmdec', 'rv_value', 'plx')
    df = customSimbad.query_object(app.vars['name']).to_pandas()

    # TODO: Add error handling

    # Clear and set values
    clear_values()
    app.vars['ra'] = df['RA_d'][0]
    app.vars['dec'] = df['DEC_d'][0]
    app.vars['pmra'] = df['PMRA'][0]
    app.vars['pmdec'] = df['PMDEC'][0]
    app.vars['rv'] = df['RV_VALUE'][0]
    app.vars['dist'] = 1000./df['PLX_VALUE'][0]

    return redirect('/query')

# Called when you click clear button
@app.route('/clear')
def app_clear():
    clear_values()
    return redirect('/query')

# Function to clear values
def clear_values():
    for key in app.vars.keys():
        app.vars[key] = ''

# Function to convert to numbers and have proper error handling
def number_convert(x):
    try:
        val = float(x)
    except ValueError:
        val = np.nan
    return val