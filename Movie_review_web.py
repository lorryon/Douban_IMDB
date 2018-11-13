from flask import Flask, render_template, request, redirect
import pandas as pd
import numpy as np
import sqlite3
import matplotlib
from matplotlib import pyplot as plt
from matplotlib import cm
import seaborn as sns
import scipy.stats as st
import matplotlib.gridspec as gridspec
import mpld3

# read in data from DB
conn = sqlite3.connect('douban_us_movie.sqlite')
crsr = conn.cursor()
crsr.execute('SELECT DBrating,IMDBratingUS, IMDBrating, DBreview_count, IMDBreview_count, IMDBgenre, TitleEN FROM Movie WHERE DBreview_count is not NULL and IMDBreview_count is not NULL')
data = crsr.fetchall()
df_raw = pd.DataFrame(data, columns=['DBrating', 'IMDBratingUS', 'IMDBrating', 'DBreview_count', 'IMDBreview_count', 'Genre', 'Title'])
df = df_raw.copy()
df = df[(df['DBrating']!='') & (df['DBrating']!='0')]

# remove comma from count
df['IMDBreview_count'] = df['IMDBreview_count'].str.replace(',', '')

# specify data type
df['DBrating'] = df['DBrating'].astype(float)
df['IMDBrating'] = df['IMDBrating'].astype(float)
df['DBreview_count']=df['DBreview_count'].astype(int)
df['IMDBreview_count'] = df['IMDBreview_count'].astype(int)

# create dummy variables for genre
df_genre = df['Genre'].str.replace('D/r/a/m/a/', 'Drama').str.replace('/', ' ').str.split()
genre = []
for i, j in df_genre.iteritems():
    if j is None:
        continue
    else: genre = genre + j
# Add columns to specify genre for each film
uniq_genre = list(set(genre))
for i in uniq_genre:
        df[i] = df_genre.apply(lambda x: i in x if x is not None else False)
df['All Genre'] = True

# Flask web app to display
app = Flask(__name__)

app.data = df
@app.route('/')
def main():
    return render_template('main_page.html')#, fig1_display=fig1)

@app.route('/plot', methods=['POST'])
def plot():
    # read the genre submitted from request
    app.genre = request.form['genre']

    # Plot the graph
    fig = plt.figure(figsize = (6,4))
    plt.style.use('seaborn-darkgrid')
    clr=sns.hls_palette(1, l=.7, s=.6) # color for each plot
    gspec = gridspec.GridSpec(4,4)

    top_hist = plt.subplot(gspec[0,1:])
    side_hist = plt.subplot(gspec[1:,0])
    lower_right = plt.subplot(gspec[1:,1:])

    # Variables
    genre = app.genre
    ind = app.data[genre]
    IMDB_rating = app.data[ind]['IMDBrating']
    DB_rating = app.data[ind]['DBrating']

    lower_right.scatter(IMDB_rating,DB_rating,color=clr,s=4)
    top_hist.hist(IMDB_rating,bins=31,color=clr)
    side_hist.hist(DB_rating,bins=31,orientation='horizontal',color=clr)
    side_hist.invert_xaxis()
    identity = np.arange(0,11)
    lower_right.plot(identity, identity, color='black', linewidth=1)

    for ax in [top_hist,lower_right]:
        ax.set_xlim(1,10)
    for ax in [side_hist,lower_right]:
        ax.set_ylim(1,10)
    lower_right.set_xlabel('IMDB Rating('+ genre +')',fontsize='large')
    side_hist.set_ylabel('Douban Rating('+ genre +')',fontsize='large')

    plt.tight_layout()

    # Convert plot to html script using mpld3
    app.plot = mpld3.fig_to_html(fig)
    return render_template('plot_page.html', fig_display = app.plot)#, fig1_display=fig1)

if __name__=='__main__':
    app.debug=True
    app.run()
