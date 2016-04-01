from flask import Flask, redirect, render_template, request
from druvw import xyz, uvw
import pandas as pd
from bokeh.plotting import figure, gridplot
from bokeh.embed import components
from bokeh.models import ColumnDataSource

app = Flask(__name__)

# Global Variables
app.vars = dict()
app.vars['ra'] = '165.46627797'
app.vars['dec'] = '-34.70473119'
app.vars['pmra'] = '-66.19'
app.vars['pmdec'] = '-13.90'
app.vars['rv'] = '13.40'
app.vars['dist'] = '53.7'

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
    return render_template('query.html', ra=app.vars['ra'], dec=app.vars['dec'],pmra=app.vars['pmra'],
                           pmdec=app.vars['pmdec'],rv=app.vars['rv'],dist=app.vars['dist'])

# Calculate for known values
@app.route('/results', methods=['GET', 'POST'])
def app_results():
    # Grab the data
    for key in request.form.keys():
        app.vars[key] = request.form[key]

    # Convert to numbers
    df = dict()
    for key in app.vars:
        df[key] = number_convert(app.vars[key])

    # Calculate xyz, uvw
    x, y, z = xyz(df['ra'], df['dec'], df['dist'])
    u, v, w = uvw(df['ra'], df['dec'], df['dist'], df['pmra'], df['pmdec'], df['rv'])

    data = pd.DataFrame({'X': [x], 'Y': [y], 'Z': [z], 'U': [u], 'V': [v], 'W': [w]})

    source = ColumnDataSource(data=data)
    # Figures
    tools = "resize, pan, wheel_zoom, box_zoom, reset, lasso_select, box_select"
    plot_size = 350

    # p1 = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools, x_range=None)
    # p1.scatter('X', 'Y', source=source)
    # p1.xaxis.axis_label = 'X (pc)'
    # p1.yaxis.axis_label = 'Y (pc)'

    p1 = basic_plot('X', 'Y', source, xlab='X (pc)', ylab='Y (pc)', tools=tools, plot_size=plot_size)
    p2 = basic_plot('Y', 'Z', source, xlab='Y (pc)', ylab='Z (pc)', tools=tools, plot_size=plot_size)
    p3 = basic_plot('X', 'Z', source, xlab='X (pc)', ylab='Z (pc)', tools=tools, plot_size=plot_size)

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


# Called when you click clear button
@app.route('/clear')
def app_clear():
    clear_values()
    return redirect('/query')

# Function to clear values
def clear_values():
    app.vars['ra'] = ''
    app.vars['dec'] = ''
    app.vars['pmra'] = ''
    app.vars['pmdec'] = ''
    app.vars['rv'] = ''
    app.vars['dist'] = ''

# Function to convert to numbers and have proper error handling
def number_convert(x):
    try:
        val = float(x)
    except ValueError:
        return render_template('error.html', headermessage='Error',
                               errmess='<p>Error converting number: ' + x + '</p>')
    return val

# Function for plotting XYZUVW data
def basic_plot(x, y, source, xlab=None, ylab=None,
               tools="resize, pan, wheel_zoom, box_zoom, reset, lasso_select, box_select",
               x_range=None, y_range=None, plot_size=350):
    p = figure(width=plot_size, plot_height=plot_size, title=None, tools=tools, x_range=x_range, y_range=y_range)
    p.scatter(x=x, y=y, source=source)
    p.xaxis.axis_label = xlab
    p.yaxis.axis_label = ylab
    return p