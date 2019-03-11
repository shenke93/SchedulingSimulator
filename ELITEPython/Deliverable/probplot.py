"""
@Joachim David, joachim.david@ugent.be, January 2019
Probability plotting tool (library)
-----------------------------------------------------------------------------------
Provides plotting functionality to a runtime schedule.
"""

import numpy as np
import pandas as pd
from re import search, sub, findall
import matplotlib.pyplot as plt
from scipy.stats import lognorm
import scipy



import matplotlib.pyplot as plt
from cycler import cycler

def merge_per_production(df, columnnames, reasons_relative=None, reasons_absolute=None, add_next=False):
    #all_reasons = list(reasons_relative) + list(reasons_absolute)
    if reasons_relative == None and reasons_absolute == None:
        reasons_relative = df[columnnames[-1]].unique()
    df_orig = df.copy()
    df = df.groupby(columnnames).agg({'Duration': np.sum}, as_index=False).unstack(
        level=(-2, -1)).fillna(0)
    # This is still correct
    newcolumns = [l + str(v) for l, v in zip(df.columns.get_level_values(1), df.columns.get_level_values(2))]
    df.columns = newcolumns
    df = df.rename({'RunTime1': 'RunTime'}, axis='columns')
    if reasons_absolute:
        df['Preparations'] = df.loc[:, ['DownTime' + str(i) for i in reasons_absolute]].sum(axis=1)
    df['DownTime'] = df.loc[:, ['DownTime' + str(i) for i in reasons_relative]].sum(axis=1)
    df['TotalDuration'] = df.DownTime + df.RunTime
    df = df[df['TotalDuration'] != 0]
    df['DownTimeRate'] = df.DownTime / df.TotalDuration
    df['RunTimeRate'] = df.RunTime / df.TotalDuration

    #weightarray = []
    #for article in df.index.get_level_values(0).unique().tolist():
    #    total = df.loc[(article, slice(None))].TotalDuration.sum()
    #    temp = df.loc[(article, slice(None))].TotalDuration / total
    #    weightarray.extend(temp.tolist())
    #df['Weight'] = weightarray
    l = list(df.columns)
    regstr = '|'.join(['[a-zA-Z]' + str(r) + '$' for r in reasons_relative])
    reason_l = [e for e in l if search(regstr, e)]
    def eval_number(elem): return int(sub("[^0-9]", '', elem))
    reason_l.sort(key=eval_number)
    newindex = reason_l + ['DownTime']
    newindex += ['RunTime', 'TotalDuration', 'DownTimeRate', 'RunTimeRate']
    if reasons_absolute:
        regstr = '|'.join(['[a-zA-Z]' + str(r) + '$' for r in reasons_absolute])
        reason_l = [e for e in l if search(regstr, e)]
        reason_l.sort(key=eval_number)
        newindex += reason_l + ['Preparations']
    df = df[newindex]
    if add_next:
        df = add_next_type(df, df_orig, columnnames[0])
    return df

def add_next_type(df_agg, df, columnname):
    df = df.sort_values('StartDateUTC')
    previous = list(df.ProductionRequestId.unique()[:-1]) 
    next = list(df.ProductionRequestId.unique()[1:])
    newname_list = []
    for n in next:
            new = df[df['ProductionRequestId'] == n].iloc[0][columnname]
            newname_list.append(new)
    new_df = pd.DataFrame(data ={'Next': next,
                        'NextType': newname_list},
                        index=previous)
    new_df = new_df.reindex(list(df_agg.index.get_level_values(1)))

    old_index = df_agg.index
    df_agg = df_agg.reset_index()
    new_df = new_df.reset_index()
    output = pd.concat([df_agg, new_df], axis=1)
    output.index = old_index

    return output

def merge_per_article(df, grouper, reasons_considered):
    listofDownTimes = ['DownTime' + str(i) for i in reasons_considered]
    newdict = dict.fromkeys(listofDownTimes, 'sum')
    newdict
    newdict['DownTime'] = 'sum'
    newdict['RunTime'] = 'sum'
    newdict['TotalDuration'] = 'sum'
    newdict

    df_plot = df.groupby(grouper).agg(newdict).fillna(0).astype('int')
    df_plot['DownTimeRate'] = df.groupby(grouper).apply(lambda x: np.average(x['DownTimeRate'],
                                                        weights=x['TotalDuration']))
    df_plot['DownTimeStd'] = df.groupby(grouper).apply(lambda x: np.cov(x['RunTimeRate'],
                                                       aweights=x['TotalDuration'])) ** (1/2)
    df_plot['Availability'] = df.groupby(grouper).apply(lambda x: np.average(x['RunTimeRate'],
                                                        weights=x['TotalDuration']))
    for i in reasons_considered:
        tempstr = 'DownTimeRate' + str(i)
        df_plot[tempstr] = df_plot['DownTime' + str(i)] / df_plot['DownTime'] * df_plot['DownTimeRate']
    df_plot.DownTimeStd = df_plot.DownTimeStd.astype(np.float)
    df_plot = df_plot.fillna(0)
    return df_plot

def colored_graph(df_plot, stringlist, cutoff_perc, before_merge=None):
    plot = df_plot[df_plot["TotalDuration"] > cutoff_perc * df_plot["TotalDuration"].max()] \
        .sort_values(by='Availability')
    # production1['DownTimeRate'].plot('bar', figsize=(15, 10))
    # production1['TotalDuration'].plot('line')
    titles = plot.index.to_series()
    colors = np.full(len(titles), 'grey')
    cy = cycler(color=['b','g','orange','c','m','y','steelblue', 'tan',
                                              'lawngreen', 'cyan', 'darkorange', 'crimson', 'greenyellow', 'darkviolet', 'fuchsia',
                                              'palevioletred', 'moccasin',
                                              'rosybrown', 'coral', 'wheat',
                                              'linen']*2).by_key()['color']
    for s, i in zip(stringlist, cy):
        if type(s) == list:
            new_s = ('|'.join(s))
            colors = np.where(titles.str.contains(new_s), i, colors)
        else:
            colors = np.where(titles.str.contains(s), i, colors)
    plt.figure(figsize=(10, min(len(titles) * 2, 20)))
    plt.barh(np.arange(len(plot)), np.array(plot['Availability']),
             tick_label=plot.index.tolist(),
             xerr=(plot['DownTimeStd']),
             color=colors)  # standard deviation is the root of the weighted variance
    plt.plot(np.array(plot['TotalDuration']) / np.array(plot['TotalDuration']).max(), np.arange(len(plot)),
             color='r',
             linewidth=3)
    plt.xticks(rotation='vertical')
    plt.axvline(1, linestyle='--', color='k')

    if before_merge is not None:
        itlist = list(plot.index)
        max_duration = before_merge.loc[:, 'TotalDuration'].max()
        for l, i, col in zip(itlist, range(len(itlist)), cy):
            runtimerate = before_merge.loc[l, 'RunTimeRate']
            totalduration = before_merge.loc[l, 'TotalDuration']
            size = totalduration / max_duration
            y_function = np.array([i] * len(runtimerate)) + np.random.uniform(low=-0.2, high=0.2, size=len(runtimerate))
            plt.scatter(runtimerate, y_function, s= 30 * size, edgecolors='k', linewidths=0.2, zorder=3, c='k', alpha=0.5)
    plt.gcf()
    return plot

def downtime_graph(df_plot, reasons_considered, cutoff_perc):
    df_plot = df_plot.fillna(0)
    plot = df_plot[df_plot["TotalDuration"] > cutoff_perc * df_plot["TotalDuration"].max()] \
        .sort_values(by='DownTimeRate', ascending=False)
    # production1['DownTimeRate'].plot('bar', figsize=(15, 10))
    # production1['TotalDuration'].plot('line')
    plt.figure(figsize=(10, min(len(plot.index.tolist()) * 2, 20)))
    x = np.arange(len(plot))
    y_c = np.zeros(x.shape)
    for i in reasons_considered:
        tempstr = 'DownTimeRate' + str(i)
        y = np.array(plot[tempstr])
        if i != reasons_considered[-1]:
            plt.barh(x, y, left=y_c, tick_label=plot.index.tolist(), label=tempstr)
        else:
            plt.barh(x, y, left=y_c, xerr=(plot['DownTimeStd']),
                     tick_label=plot.index.tolist(), label=tempstr)
        y_c += y
    plt.plot(np.array(plot['TotalDuration'])/ np.array(plot['TotalDuration']).max(), np.arange(len(plot)), linewidth=3,
             color='r')
    plt.xticks(rotation='vertical')
    plt.legend()
    plt.title('Per-product DownTimeRate')
    plt.gcf()

def plot_distribution(durations, cutoff_perc=100, numbins=None):
    maxt = np.percentile(np.array(durations), cutoff_perc)
    mint = 0
    durations = [d for d in durations if (d <= maxt) & (d >= mint)]
    if numbins == None:
        # Book Reliability and Safety Engineering, suggested number of bins, page 61
        # Sturges' rule for grouping data
        numbins = int(np.round(1 + 3.3 * np.log10(len(durations))))
    hist, bin_edges = np.histogram(np.array(durations), bins=numbins, range=(mint, maxt))
    ran = bin_edges
    normhist = hist / sum(hist) * (cutoff_perc) / 100
    c_fail = np.cumsum(normhist)
    plt.figure(figsize=(10, 5))
    x = np.linspace(0, maxt, numbins)
    plt.bar(ran[:-1] + (ran[1] - ran[0]) / 2, normhist, width=ran[1] - ran[0], edgecolor='k')
    plt.bar(ran[:-1] + (ran[1] - ran[0]) / 2, c_fail, width=ran[1] - ran[0], alpha=0.1, edgecolor='k')
    #plt.title('Failure function F(t)')
    #plt.xlabel('Time between failures [hours]')
    plt.gcf()

def show_gantt(df, start, end):
    plt.figure(figsize=(20, 10))
    # df_task['Start'] = (df_task.StartDateUTC - df_task.StartDateUTC[0].floor('D')).dt.total_seconds()/3600
    # df_task['End'] = (df_task.EndDateUTC - df_task.StartDateUTC[0].floor('D')).dt.total_seconds()/3600
    df_part = df[df.StartDateUTC.between(start, end) & df.EndDateUTC.between(start, end)]
    all_reasons = list(df_part.ReasonId.unique())
    all_reasons.sort()
    plot_gantt(df_part, 'ReasonId', 'ArticleName', order=all_reasons)
    # handles, labels = plt.gca().get_legend_handles_labels()
    # by_label = dict(zip(labels, handles))
    # key_list = sorted(by_label)
    # value_list = [by_label[key] for key in key_list]
    # plt.legend(value_list, key_list, loc='lower right')
    plt.title('Gantt chart, original')
    #try:
    #    plt.savefig('D:/temp/gantt.svg', dpi=1200, bbox_inches='tight')
    #except:
    #    pass
    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    print(__doc__)