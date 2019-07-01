#Load the packages
import pandas as pd
import requests
#import simplejson as json
from bs4 import BeautifulSoup
#import datetime
from flask import Flask,request,render_template, redirect, url_for
from bokeh.embed import components 

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, DataRange1d, Select
from bokeh.palettes import Blues4
from bokeh.plotting import figure, output_file, save

#Connect the app
app = Flask(__name__)

#app.vars = {}
ticker_list = pd.read_csv('ticker_list.csv')
tickers = ticker_list['ticker'].tolist()
months = ['2018-09','2018-10','2018-11','2018-12']

#Helper Functions
def get_dates(which_month):
    '''
    get the starting and ending date of a month
    
    which_month: a string, indicating the requested month
    
    return a tuple of strings, starting date and ending date.
    '''
    big = [1,3,5,7,8,10,12]
    small = [4,6,9,11]
    
    month = int(which_month.split('-')[1])
    
    sdate = which_month+'-01'
    if month in big:
        edate = which_month+'-31'
    elif month in small:
        edate = which_month+'30'
    else:
        edate = which_month+'28'
    return (sdate, edate)

def get_url(ticker, which_month):
    '''
    from user input construct the conresponding url
    
    ticker: a string, ticker the of the requested stock.
    which_month: a string, indicating the requested month.
    
    return a string of url  
    '''
    url_str="https://www.quandl.com/api/v3/datatables/SHARADAR/SEP.csv?date.gte={0}&date.lte={1}&ticker={2}&api_key=6d9vzXvnMCwRGGsZjcvN"
    
    sdate, edate = get_dates(which_month)
    
    url = url_str.format(sdate,edate,ticker)
    
    return url

def get_data(url):
    '''
    Retrieve data from the website
    
    url: a string.
    
    return a Pandas DataFrame
    '''
    page = requests.get(url)
    
    html = page.content
    soup = BeautifulSoup(html,'html.parser')
    data = soup.text.split('\n')[1:-1]
    heading = soup.text.split('\n')[0]
    heading = heading.split(',')
    
    data2 = [i.split(',') for i in data]
    
    df = pd.DataFrame(data2, columns = heading)
    
    
    #refine the dtypes of the dataframe
    df.iloc[:, 2:9] = df.iloc[:, 2:9].apply(lambda x: x.astype('float'))
    df[['date','lastupdated']] = df[['date','lastupdated']].apply(pd.to_datetime, format='%Y-%m-%d')
    
    return df

def get_dataset(ticker, which_month):
    url = get_url(ticker, which_month)
    df = get_data(url)
    df = df.set_index(['date'])
    df.sort_index(inplace=True)
    return ColumnDataSource(data=df)

def make_plot(source, title):
    plot = figure(x_axis_type="datetime", 
                  plot_width=800, plot_height=400)
    plot.title.text = title

    #plot.vline_stack(['open', 'close'], x='date', source=source)
    plot.line(y='open', x='date', source=source,
             color=Blues4[2], legend="opening price")
    plot.line(y='close', x='date', source=source,
             color=Blues4[0], legend="closing price")
    
    #fixed attributes
    plot.xaxis.axis_label = "Date"
    plot.yaxis.axis_label = "Stock Price"
    plot.axis.axis_label_text_font_style = "bold"
    
    plot.grid.grid_line_alpha = 0.3
    
    return plot

@app.route('/', methods=['GET', 'POST'])
def index():
    #ticker_list = pd.read_csv('ticker_list.csv')
    #tickers = ticker_list['ticker'].tolist()
    #months = ['2018-09','2018-10','2018-11','2018-12']
    if request.method == "GET":
        print('get method')
        current_ticker = request.args.get('ticker')
        current_month = request.args.get('month')
        if current_ticker == None:
            current_ticker = 'XOM'
        if current_month == None:
            current_month = '2018-09'
        print(current_ticker, current_month)
        source = get_dataset(current_ticker, current_month)
        #app.vars['data'] = source
        #app.vars['input'] = (current_ticker, current_month)
        plot = make_plot(source,"Ticker Look-up: Stock Price of {}".format(current_ticker))
        script, div = components(plot)

        return render_template('home.html', script=script, div=div, months = months, tickers = tickers,
current_ticker=current_ticker, current_month=current_month)
    
    else:
        print('post method') 
        current_ticker = request.form.get('ticker')
        current_month = request.form.get('month')
        #app.vars['input'] = (current_ticker, current_month)
        print(current_ticker, current_month)
        return redirect(url_for('graph'))

@app.route('/graph')
def graph():
    #current_ticker, current_month  = app.vars['input']
    current_ticker = request.form.get('ticker')
    current_month = request.form.get('month')
    source = get_dataset(current_ticker, current_month)
    plot = make_plot(source,"Stock Price of {}".format(current_ticker))
    script, div = components(plot)

    return render_template('graph.html', script=script, div=div)

    
@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(port=33507) #Set to false when deploying
