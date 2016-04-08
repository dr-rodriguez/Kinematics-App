from flask import Flask, redirect, render_template, request
from druvw import xyz, uvw
import pandas as pd
from bokeh.plotting import figure, gridplot
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
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
    tools = "resize, pan, wheel_zoom, box_zoom, reset, lasso_select, box_select, hover"
    plot_size = 350
    point_size = 10
    point_color = 'black'

    p1 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools)
    p1.scatter('X', 'Y', source=source, size=point_size, color=point_color)
    p1.xaxis.axis_label = 'X (pc)'
    p1.yaxis.axis_label = 'Y (pc)'

    p2 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools, x_range=p1.y_range)
    p2.scatter('Y', 'Z', source=source, size=point_size, color=point_color)
    p2.xaxis.axis_label = 'Y (pc)'
    p2.yaxis.axis_label = 'Z (pc)'

    p3 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools, x_range=p1.x_range, y_range=p2.x_range)
    p3.scatter('X', 'Z', source=source, size=point_size, color=point_color)
    p3.xaxis.axis_label = 'X (pc)'
    p3.yaxis.axis_label = 'Z (pc)'

    p4 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools)
    p4.scatter('U', 'V', source=source, size=point_size, color=point_color)
    p4.xaxis.axis_label = 'U (km/s)'
    p4.yaxis.axis_label = 'V (km/s)'

    p5 = figure(width=plot_size, plot_height=plot_size, title=None, x_range=p4.y_range, tools=tools)
    p5.scatter('V', 'W', source=source, size=point_size, color=point_color)
    p5.xaxis.axis_label = 'V (km/s)'
    p5.yaxis.axis_label = 'W (km/s)'

    p6 = figure(width=plot_size, plot_height=plot_size, title=None, x_range=p4.x_range, y_range=p5.y_range, tools=tools)
    p6.scatter('U', 'W', source=source, size=point_size, color=point_color)
    p6.xaxis.axis_label = 'U (km/s)'
    p6.yaxis.axis_label = 'W (km/s)'

    # Hover tooltips
    p1.select(HoverTool).tooltips = {"(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}
    p2.select(HoverTool).tooltips = {"(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}
    p3.select(HoverTool).tooltips = {"(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}
    p4.select(HoverTool).tooltips = {"(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}
    p5.select(HoverTool).tooltips = {"(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}
    p6.select(HoverTool).tooltips = {"(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}

    # Nearby Young Moving Groups
    nymg_plot(p1, p2, p3, p4, p5, p6)

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
    simbad_query = customSimbad.query_object(app.vars['name'])

    try:
        df = simbad_query.to_pandas()
    except AttributeError: # no result
        return render_template('error.html', headermessage='Error',
                                   errmess='<p>Error querying Simbad for: ' + app.vars['name'] + '</p>')

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

# Function to plot the NYMG ovals
def nymg_plot(p1,p2,p3,p4,p5,p6):
    g_name = ['bPMG', 'TWA', 'THA', 'COL', 'CAR', 'ARG', 'ABDMG']
    g_U = [-10.94, -9.95, -9.88, -12.24, -10.34, -21.78, -7.12]
    g_Ue = np.array([2.06, 4.02, 1.51, 1.03, 1.28, 1.32, 1.39])
    g_V = [-16.25, -17.91, -20.7, -21.32, -22.31, -12.08, -27.31]
    g_Ve = np.array([1.3, 1.75, 1.87, 1.18, 0.58, 1.97, 1.31])
    g_W = [-9.27, -4.65, -0.9, -5.58, -5.91, -4.52, -13.81]
    g_We = np.array([1.54, 2.57, 1.31, 0.89, 0.11, 0.5, 2.16])
    g_X = [9.27, 12.49, 11.39, -27.44, 15.55, 14.6, -2.37]
    g_Xe = np.array([31.71, 7.08, 19.29, 13.79, 5.66, 18.6, 20.03])
    g_Y = [-5.96, -42.28, -21.21, -31.32, -58.53, -24.67, 1.48]
    g_Ye = np.array([15.19, 7.33, 9.17, 20.55, 16.69, 19.06, 18.83])
    g_Z = [-13.59, 21.55, -35.4, -27.97, -22.95, -6.72, -15.62]
    g_Ze = np.array([8.22, 4.2, 5.39, 15.09, 2.74, 11.43, 16.59])
    g_color = ['blue', 'green', 'red', 'yellow', 'magenta', 'cyan', 'grey']

    # Hover does not work for Oval :(
    p1.oval(x=g_X, y=g_Y, width=g_Xe * 2, height=g_Ye * 2, color=g_color,
            angle=0, height_units='data', width_units='data', fill_alpha=0.5)
    p1.text(x=g_X, y=g_Y, text=g_name, text_color='black', angle=0, text_alpha=0.5)

    p2.oval(x=g_Y, y=g_Z, width=g_Ye * 2, height=g_Ze * 2, color=g_color,
            angle=0, height_units='data', width_units='data', fill_alpha=0.5)

    p3.oval(x=g_X, y=g_Z, width=g_Xe * 2, height=g_Ze * 2, color=g_color,
            angle=0, height_units='data', width_units='data', fill_alpha=0.5)

    p4.oval(x=g_U, y=g_V, width=g_Ue * 2, height=g_Ve * 2, color=g_color,
            angle=0, height_units='data', width_units='data', fill_alpha=0.5)
    p4.text(x=g_U, y=g_V, text=g_name, text_color='black', angle=0, text_alpha=0.5)

    p5.oval(x=g_V, y=g_W, width=g_Ve * 2, height=g_We * 2, color=g_color,
            angle=0, height_units='data', width_units='data', fill_alpha=0.5)

    p6.oval(x=g_U, y=g_W, width=g_Ue * 2, height=g_We * 2, color=g_color,
            angle=0, height_units='data', width_units='data', fill_alpha=0.5)

    return
