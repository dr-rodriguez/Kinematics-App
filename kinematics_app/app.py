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
app.vars['rv_ini'] = ''
app.vars['rv_fin'] = ''
app.vars['rv_step'] = ''

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
    # TODO: Add multi_rv vars to query page
    return render_template('query.html', ra=app.vars['ra'], dec=app.vars['dec'], pmra=app.vars['pmra'],
                           pmdec=app.vars['pmdec'], rv=app.vars['rv'], dist=app.vars['dist'], name=app.vars['name'],
                           rv_ini=app.vars['rv_ini'], rv_fin=app.vars['rv_fin'], rv_step=app.vars['rv_step'])

# Calculate for known values
@app.route('/results', methods=['GET', 'POST'])
def app_results():
    # Grab the data
    for key in request.form.keys():
        if key == 'type_flag':
            continue
        app.vars[key] = request.form[key]

    # Convert to numbers
    df = dict()
    for key in app.vars:
        if key in ['name']: continue  # don't convert

        # TODO: Add multi_dist functionality
        if request.form['type_flag'] == 'normal':
            if key in ['rv_ini', 'rv_fin', 'rv_step']: continue
        if request.form['type_flag'] == 'multi_rv':
            if key in ['rv']: continue

        temp = number_convert(app.vars[key])
        if math.isnan(temp):
            return render_template('error.html', headermessage='Error',
                                   errmess='<p>Error converting number: ' + app.vars[key] + '</p>')
        else:
            df[key] = temp

    # Calculate xyz, uvw
    if request.form['type_flag'] == 'normal':
        x, y, z = xyz(df['ra'], df['dec'], df['dist'])
        u, v, w = uvw(df['ra'], df['dec'], df['dist'], df['pmra'], df['pmdec'], df['rv'])
    if request.form['type_flag'] == 'multi_rv':
        rv_array = np.arange(df['rv_ini'], df['rv_fin'], df['rv_step'])
        if rv_array[-1] != df['rv_fin']:
            rv_array = np.append(rv_array, df['rv_fin'])
        arr_len = len(rv_array)
        x, y, z = xyz([df['ra']] * arr_len,
                      [df['dec']] * arr_len,
                      [df['dist']] * arr_len)
        u, v, w = uvw([df['ra']] * arr_len,
                      [df['dec']] * arr_len,
                      [df['dist']] * arr_len,
                      [df['pmra']] * arr_len,
                      [df['pmdec']] * arr_len,
                      rv_array)

    # TODO: Add rv/dist to output data frame
    if request.form['type_flag'] == 'normal':
        data = pd.DataFrame({'X': [x], 'Y': [y], 'Z': [z], 'U': [u], 'V': [v], 'W': [w]})
    else:
        if request.form['type_flag'] == 'multi_rv':
            data = pd.DataFrame({'RV':rv_array, 'X': x, 'Y': y, 'Z': z, 'U': u, 'V': v, 'W': w})

    # Figures
    source = ColumnDataSource(data=data)
    tools = "resize, pan, wheel_zoom, box_zoom, reset"
    plot_size = 350
    point_size = 10
    point_color = 'black'

    hover_flags = [True, True]  # for XYZ and for UVW plots
    if request.form['type_flag'] == 'multi_rv':  # disable for multi_rv plots, but only for XYZ
        hover_flags[0] = False

    # Create the main plots
    # XYZ Plots
    p1 = my_plot('X', 'Y', source, 'X (pc)', 'Y (pc)', x_range=None, y_range=None,
                 point_size=point_size, point_color=point_color, plot_size=plot_size, tools=tools,
                 type_flag=request.form['type_flag'], hover_flag=hover_flags[0])
    p2 = my_plot('Y', 'Z', source, 'Y (pc)', 'Z (pc)', x_range=p1.y_range, y_range=None,
                 point_size=point_size, point_color=point_color, plot_size=plot_size, tools=tools,
                 type_flag=request.form['type_flag'], hover_flag=hover_flags[0])
    p3 = my_plot('X', 'Z', source, 'X (pc)', 'Z (pc)', x_range=p1.x_range, y_range=p2.y_range,
                 point_size=point_size, point_color=point_color, plot_size=plot_size, tools=tools,
                 type_flag=request.form['type_flag'], hover_flag=hover_flags[0])

    # UVW Plots
    p4 = my_plot('U', 'V', source, 'U (km/s)', 'V (km/s)', x_range=None, y_range=None,
                 point_size=point_size, point_color=point_color, plot_size=plot_size, tools=tools,
                 type_flag=request.form['type_flag'], hover_flag=hover_flags[1])
    p5 = my_plot('V', 'W', source, 'V (km/s)', 'W (km/s)', x_range=p4.y_range, y_range=None,
                 point_size=point_size, point_color=point_color, plot_size=plot_size, tools=tools,
                 type_flag=request.form['type_flag'], hover_flag=hover_flags[1])
    p6 = my_plot('U', 'W', source, 'U (km/s)', 'W (km/s)', x_range=p4.x_range, y_range=p5.y_range,
                 point_size=point_size, point_color=point_color, plot_size=plot_size, tools=tools,
                 type_flag=request.form['type_flag'], hover_flag=hover_flags[1])

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

    # TODO: Decide on final colors for groups
    # g_color = ['blue', 'green', 'red', 'yellow', 'magenta', 'cyan', 'grey']
    # g_color = ['#7fc97f','#beaed4','#fdc086','#ffff99','#386cb0','#f0027f','#bf5b17'] #Accent
    # g_color = ['#1b9e77','#d95f02','#7570b3','#e7298a','#66a61e','#e6ab02','#a6761d'] #Dark2
    g_color = ['#0000CD', '#FF0000', '#008000', '#FF00FF', '#7FFFD4', '#9400D3', '#FF8C00']  # Colors from Faherty paper

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

# Function to make the basic plots
def my_plot(xvar, yvar, source, xlabel, ylabel, point_size=10,
            point_color='black', plot_size=350, tools="resize, pan, wheel_zoom, box_zoom, reset",
            x_range=None, y_range=None, type_flag='normal', hover_flag=True):
    p = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools, x_range=x_range, y_range=y_range)
    p.scatter(xvar, yvar, source=source, size=point_size, color=point_color)
    p.xaxis.axis_label = xlabel
    p.yaxis.axis_label = ylabel

    # TODO: Update for multi_dist
    if type_flag == "normal":
        tooltip = {"(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}
    if type_flag == 'multi_rv':
        tooltip = {"RV": "@RV", "(X,Y,Z)": "(@X, @Y, @Z)", "(U,V,W)": "(@U, @V, @W)"}

    if hover_flag:
        p.add_tools(HoverTool(tooltips=tooltip))

    return p