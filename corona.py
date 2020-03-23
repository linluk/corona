#!/usr/bin/env python3


import sys
import os
import time
import csv
import urllib.request
import re
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import numpy.polynomial.polynomial as poly


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

def growth_rate(series):
    if len(series) < 3:
        return [.0 for _ in range(len(series))]
    output = [.0, .0]
    for i in range(2, len(series)):
        d1 = series[i - 1] - series[i - 2]
        d2 = series[i] - series[i - 1]
        if d1 <= 0:
            output.append(.0)
        else:
            output.append(d2 / d1)
    return output

def r_square(func, data):
    y_ = sum(y for y in data) / len(data)
    SS_tot = sum((data[i] - y_) ** 2 for i in range(len(data)))
    SS_res = sum((data[i] - func(i)) ** 2 for i in range(len(data)))
    return 1 - SS_res / SS_tot


def main():
    confirmed, recovered, deaths = download_data()
    filter_italy = lambda _k, _d: _d[_k['Country/Region']] == 'Italy'
    filter_austria = lambda _k, _d: _d[_k['Country/Region']] == 'Austria'
    filter_china = lambda _k, _d: _d[_k['Country/Region']] == 'China'
    filter_china_hubei = lambda _k, _d: _d[_k['Country/Region']] == 'China' and _d[_k['Province/State']] == 'Hubei'
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

    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['figure.titlesize'] = 'small'

    timestamp = time.strftime('%Y-%m-%d %H:%M')
    filename = lambda fn: os.path.join(os.path.abspath(sys.path[0]), 'export', fn.lower())

    # country details
    for country in data:
        plt.figure()
        for category in data[country]:
            # growth rate 4 day average
            gr = sum(growth_rate(data[country][category])[-4:]) / 4
            plt.plot(data[country][category], color=colors[category], label=f'{category}, Growth Rate: {gr:.2f}')
        plt.bar([1],[0], label='Growth Rate', alpha=0.2) # a dummy so that it appears in the same legend.
        plt.legend()
        gr = growth_rate(data[country]['Confirmed'])
        plt.twinx()
        plt.ylim((0, 8))
        plt.bar(range(len(gr)), gr, label='Growth Rate', alpha=0.2)
        plt.title(f'{country} Details\n{timestamp}')
        plt.tight_layout()
        plt.savefig(filename(f'{country}.png'))

    # comparison
    plt.figure()
    # numbers from wikipedia, seen on 2020-03-20
    plt.plot([1e5 * c / 60_262_701 for c in accumulate(confirmed, filter_italy) if c > 0], label='Italy', color='g')
    plt.plot([1e5 * c / 1_400_050_000 for c in accumulate(confirmed, filter_china) if c > 0], label='China (Total)', color='y')
    plt.plot([1e5 * c / 58_500_000 for c in accumulate(confirmed, filter_china_hubei) if c > 0], label='China (Hubei only)', color='m')
    plt.plot([1e5 * c / 8_858_775 for c in accumulate(confirmed, filter_austria) if c > 0], label='Austria', color='b')
    plt.legend()
    plt.title(f'Comparison\nConfirmed Cases per 100,000 Poeple\n{timestamp}')
    plt.tight_layout()
    plt.savefig(filename('comparison.png'))

    # austria details
    actual = [c for c in accumulate(confirmed, filter_austria) if c > 0]
    coefs = poly.polyfit(range(len(actual)), actual, 4)
    ffit = poly.Polynomial(coefs)
    plt.figure()
    plt.plot(actual, label='Data', color='b', linestyle='', marker='o')
    r2 = r_square(ffit, actual)
    plt.plot([ffit(x) for x in range(int(len(actual) * 1.3))], label=f'Fitted  R^2: {r2:.3}', color='g')
    plt.legend()
    sfunc = 'f(x) = ' + ' + '.join(f'{coefs[i]:.3f} * x ^ {i + 1}' for i in range(len(coefs)))
    plt.title(f'Polynomial Fitted Curve\nAustria\n{sfunc}\n{timestamp}')
    plt.tight_layout()
    plt.savefig(filename('fitted.png'))

    plt.show()



if __name__ == '__main__':
    main()




