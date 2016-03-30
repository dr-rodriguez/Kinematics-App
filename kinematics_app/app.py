from flask import Flask, redirect, render_template, request
from druvw import xyz, uvw
import pandas as pd

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
@app.route('/calculate', methods=['GET', 'POST'])
def app_calculate():
    # Grab the data
    app.vars['ra'] = request.form['ra']
    app.vars['dec'] = request.form['dec']
    app.vars['pmra'] = request.form['pmra']
    app.vars['pmdec'] = request.form['pmdec']
    app.vars['rv'] = request.form['rv']
    app.vars['dist'] = request.form['dist']

    # Convert to numbers
    ra = number_convert(app.vars['ra'])
    dec = number_convert(app.vars['dec'])
    pmra = number_convert(app.vars['pmra'])
    pmdec = number_convert(app.vars['pmdec'])
    rv = number_convert(app.vars['rv'])
    dist = number_convert(app.vars['dist'])

    # Calculate xyz, uvw
    x,y,z = xyz(ra, dec, dist)

    data = pd.DataFrame({'X':[x], 'Y':[y], 'Z':[z]})

    return data.to_html(classes='display', index=False)


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
