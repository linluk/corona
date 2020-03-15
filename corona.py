#!/usr/bin/env python3


import sys
import os
import csv
import urllib.request
import re
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.style.use('dark_background')


def download_data():
    baseurl='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
    def _download(_url, _fn):
        return csv.reader(urllib.request.urlopen(_url).read().decode('utf-8').split('\n'), delimiter=',')
    confirmed = [x for x in _download(baseurl + 'time_series_19-covid-Confirmed.csv', os.path.join(sys.path[0], 'confirmed.csv'))]
    deaths = [x for x in _download(baseurl + 'time_series_19-covid-Deaths.csv', os.path.join(sys.path[0], 'deaths.csv'))]
    recovered = [x for x in _download(baseurl + 'time_series_19-covid-Recovered.csv', os.path.join(sys.path[0], 'recovered.csv'))]
    return confirmed, recovered, deaths


def accumulate(data, filter_=None):
    if filter_ is None:
        filter_ = lambda _1, _2: True
    is_date = lambda s: re.search(r'\d+\/\d+\/\d+', s)
    output = {}
    idx2name = {}
    name2idx = {}
    first = True
    for row in data:
        if first:
            first = False
            for i in range(len(row)):
                idx2name[i] = row[i]
                name2idx[row[i]] = i
        else:
            if filter_(name2idx, row):
                idx = 0
                for i in range(len(row)):
                    if is_date(idx2name[i]):
                        if idx in output:
                            output[idx] += int(row[i])
                        else:
                            output[idx] = int(row[i])
                        idx += 1
    return [output[i] for i in output]


def main():
    confirmed, recovered, deaths = download_data()
    filter_italy = lambda _k, _d: _d[_k['Country/Region']] == 'Italy'
    filter_austria = lambda _k, _d: _d[_k['Country/Region']] == 'Austria'
    data = {
        'Austria': {
            'Confirmed': accumulate(confirmed, filter_austria),
            'Deaths': accumulate(deaths, filter_austria),
            'Recovered': accumulate(recovered, filter_austria)
            },
        'Italy': {
            'Confirmed': accumulate(confirmed, filter_italy),
            'Deaths': accumulate(deaths, filter_italy),
            'Recovered': accumulate(recovered, filter_italy)
            },
        'World': {
            'Confirmed': accumulate(confirmed),
            'Deaths': accumulate(deaths),
            'Recovered': accumulate(recovered)
            }
        }
    colors = {
        'Confirmed': 'b',
        'Deaths': 'r',
        'Recovered': 'g'
    }

    fig = plt.figure()
    pos = 1
    for country in data:
        ax = fig.add_subplot(1, 3, pos)
        pos += 1
        for category in data[country]:
            try:
                gr = data[country][category][-1] / data[country][category][-2]
            except:
                gr = 0
            ax.plot(data[country][category], color=colors[category], label=f'{category}' + (f', Growth Rate: {gr:.2f}' if category == 'Confirmed' else '') )
        ax.bar([1],[0], label='Growth Rate', alpha=0.2)
        ax.legend()
        rates = [0]
        X = data[country]['Confirmed']
        ax = ax.twinx()
        ax.set_ylim(0, 8)
        for i in range(len(X) - 1):
            try:
                rate = (X[i + 1] / X[i])
            except:
                rate = 0
            rates.append(rate)
        ax.bar(range(len(X)), rates, label='Growth Rate', alpha=0.2)
        ax.set_title(country)
    plt.show()



if __name__ == '__main__':
    main()




