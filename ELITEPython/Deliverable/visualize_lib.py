'''
Joachim David and Ke Shen - 2019
Ghent University
----------------
Visualisation routines for the results of the SchedulerV000
'''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator
from matplotlib.pyplot import cm
import os

def show_ga_results(result):
    #fig, ax = plt.subplots(figsize=(6, 4))
    #result_rolling = result.rolling(int(len(result)/20)).mean()
    #result_rolling.columns = [c + '_rolling_mean' for c in result_rolling.columns]
    result[['best', 'worst', 'mean']].plot()
    ax = plt.gca()
    ax.set(#title='Fitness evolution graph', 
           xlabel='# iterations', ylabel='Predicted cost')
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ran = max(result['best']) - min(result['best'])
    plt.ylim(min(result['best']) - ran*0.05, max(result['best']) + ran*0.05)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=len(result.columns))
    #return plt.gcf()

def plot_gantt(df_task, reason_str, articlename, startdate='StartDateUTC', enddate='EndDateUTC', order=False, downtimes=None, duedate=None):
    ''' 
    Make a gantt plot of the production file
    - df_task is the pandas DataFrame
    - Reason_str determines which tasks get a separate color
    - Articlename determines if a task is put in a separate line
    - Startdate determines the start date of a production
    - Enddate determines the end date of a production
    - Order can give a custom order to the productions
    - Downtimes is an optional dataframe indicating downtimes of the production line
    '''
    df_task = df_task.reset_index(drop=False) # make index unique (necessary)

    first_index = df_task.index[0]
    #print(first_index)
    try:
        firstdate = df_task.loc[first_index, startdate].floor('D')
        df_task.loc[:, 'Vis_Start'] = (df_task.loc[:, startdate] - firstdate).dt.total_seconds()/3600
        df_task.loc[:, 'Vis_End'] = (df_task.loc[:, enddate] - firstdate).dt.total_seconds()/3600
    except:
        df_task.loc[:, 'Vis_Start'] = df_task.loc[:, startdate]
        df_task.loc[:, 'Vis_End'] = df_task.loc[:, enddate]
    if isinstance(downtimes, pd.DataFrame): # if downtimes included in the correct format
        #print(downtimes)
        downtimes.loc[:, 'Vis_Start'] = (downtimes.loc[:, 'StartDateUTC'] - firstdate).dt.total_seconds()/3600
        downtimes.loc[:, 'Vis_End'] = (downtimes.loc[:, 'EndDateUTC'] - firstdate).dt.total_seconds()/3600
    # Plot a line for every line of data in your file
    
    # from cycler import cycler
    # cy = cycler(color=['b','g','orange','c','m','yellow','steelblue', 'tan',
    #                                           'grey', 'cyan', 'lightgreen', 'crimson', 'greenyellow', 'darkviolet', 'fuchsia',
    #                                           'palevioletred', 'moccasin',
    #                                           'rosybrown', 'coral', 'wheat',
    #                                           'linen']*10).by_key()['color']
    if order:
        reasons = list(order)
    else:
        reasons = list(df_task[reason_str].unique())
        reasons.sort()
    #color = plt.cm.get_cmap('gist_rainbow', len(reasons))
    color = cm.gist_rainbow(np.linspace(0, 1, len(reasons)))
    color_dict = dict(zip(reasons, color))
    
    articles = np.sort(df_task[articlename].unique()).tolist()
    exception = 'NONE'
    if exception in articles:
        i = articles.index(exception)
        articles.pop(i)
        articles.insert(0, exception)
    i = 0
    # plot the downtimes as grey zones
    if isinstance(downtimes, pd.DataFrame):
        for item in downtimes.T:
            entry = downtimes.loc[item]
            plt.axvspan(entry['Vis_Start'], entry['Vis_End'], alpha=0.3, facecolor='k')
    
    # plot the jobs in the Gantt chart
    for article in articles:
        df_temp = df_task[df_task[articlename] == article]
        for item in df_temp.T:
            entry = df_temp.loc[item]
            plt.hlines(i, entry['Vis_Start'], entry['Vis_End'], lw=11,
                       colors=color_dict[entry[reason_str]])
            if duedate != None:
                #import pdb; pdb.set_trace()
                plt.hlines(i, entry[duedate], entry[duedate] + 3, lw=11, colors='k')
        i += 1
    plt.yticks(range(0, i), articles, fontsize='x-small')
    plt.margins(0.1)

    # make a custom legend
    lines = []
    import matplotlib.lines as mlines
    #import matplotlib.patches as mpatches
    for item in color_dict:
        line = mlines.Line2D([],[], color=color_dict[item], label=item, linewidth=12, solid_capstyle='butt')
        lines.append(line)
    plt.legend(bbox_to_anchor=(0, 1.05, 1, 1.05), loc='lower left', borderaxespad=0., handles=lines, mode='expand', ncol=len(color_dict))

    plt.ylabel('Job')
    plt.yticks(fontsize='xx-small')
    try:
        timerange = np.arange(0, np.max(df_task['Vis_End'])+24, 24)
        label = pd.date_range(df_task[startdate].iloc[0].floor('D'), periods = len(timerange))
        label = label.strftime("%Y-%m-%d")
        plt.xticks(timerange, label, rotation=90)
        plt.xlim(timerange.min(), timerange.max())
        plt.xlabel('Time[h]')
        # from matplotlib.ticker import 
        # plt.xaxis.set_major_formatter()
        #import matplotlib.ticker as ticker
        #ax.xaxis.set_major_locator(ticker.MultipleLocator(1.00))
        return label
    except:
        #plt.xticks(np.linspace(df_task[startdate].min(), df_task[enddate].max(), 10), rotation=90)
        pass
    
    
    
    

def calculate_energy_table(df_tasks, df_cost):
    lastenddate = df_tasks.iloc[-1]['EndDateUTC']
    new_row = pd.Series({'StartDateUTC': lastenddate,
                     'EndDateUTC': lastenddate + pd.Timedelta(1, 's'),
                     'ArticleName': 'NONE',
                     'Type': 'NONE'})
    df_tasks = df_tasks.append(new_row, ignore_index=True)
    df_tasks = df_tasks.set_index('StartDateUTC', drop=True)
    #print(df_tasks)

    # Set timedateindex
    #df_tasks = df_tasks.merge(df_cons, how='left', left_on='ArticleName', right_on='Product').set_index('StartDateUTC', drop=True)
    
    import pdb; pdb.set_trace()

    # Concatenate the list of tasks and the energy cost on axis 0
    out_table = pd.concat([df_tasks, df_cost]).sort_index()

    startind = df_cost.index[df_cost.index < df_tasks.index[0]].max()
    out_table = out_table[startind: df_tasks.index[-1]]

    # Determine the length of each time interval
    # Make a new index with all changes and their length in hours
    alldates = out_table.index
    times = -pd.Series(((alldates - pd.Timestamp("1970-01-01")) / pd.Timedelta('1s'))).diff(-1)
    out_table = out_table.reset_index(drop=True)
    out_table['Difftime'] = times
    out_table.index = alldates
    out_table = out_table.iloc[:-1]
    out_table = out_table[['Product', 'Difftime', 'Euro', 'Power']].ffill().bfill()

    out_table = out_table[out_table.Difftime > 0]

    out_table['Price'] = (out_table['Difftime'] * out_table['Euro'] * out_table['Power']) / 3600
    out_table = out_table[df_tasks.index[0]: df_tasks.index[-1]]

    # Obsolete: calculates the total sum of the cost
    total_sum = out_table['Price'].sum()
    
    return out_table

# def calculate_energy_cost(df_tasks, df_cost, df_cons, return_table=False):
#     lastenddate = df_tasks.iloc[-1]['EndDateUTC']
#     new_row = pd.Series({'ProductionRequestId': -1000,
#                         'StartDateUTC': lastenddate,
#                         'EndDateUTC': lastenddate + pd.Timedelta(1, 's'),
#                         'Duration': 1,
#                         'ReasonId': 0,
#                         'ArticleName': 'NONE'})
#     df_tasks = df_tasks.append(new_row, ignore_index=True)
#     #print(df_tasks)
    
#     # Set timedateindex
#     df_tasks = df_tasks.merge(df_cons, how='left', left_on='ArticleName', right_on='Product').set_index('StartDateUTC', drop=True)
    
#     # Concatenate the list of tasks and the energy cost on axis 0
#     out_table = pd.concat([df_tasks, df_cost]).sort_index()

#     startind = df_cost.index[df_cost.index < df_tasks.index[0]].max()
#     out_table = out_table[startind: df_tasks.index[-1]]
    
#     # Determine the length of each time interval
#     # Make a new index with all changes and their length in hours
#     alldates = out_table.index
#     times = -pd.Series(((alldates - pd.Timestamp("1970-01-01")) / pd.Timedelta('1s'))).diff(-1)
#     out_table = out_table.reset_index(drop=True)
#     out_table['Difftime'] = times
#     out_table.index = alldates
#     out_table = out_table.iloc[:-1]
#     out_table = out_table[['Product', 'Difftime', 'Euro', 'Power']].ffill().bfill()

#     out_table = out_table[out_table.Difftime > 0]
    
#     out_table['Price'] = (out_table['Difftime'] * out_table['Euro'] * out_table['Power']) / 3600
#     out_table = out_table[df_tasks.index[0]: df_tasks.index[-1]]
#     total_sum = out_table['Price'].sum()
    
#     if return_table:
#         return total_sum, out_table
#     else:
#         return total_sum

def show_energy_plot(tasks, prices, title='Schedule', colors='ArticleName', productions='ArticleName',
                     downtimes=None, failure_rate=None, startdate='Start', enddate='End'):
    ''' Expects a few tables with the following columns:
    dataframe tasks with columns:
        -  StartDateUTC
        -  EndDateUTC
        -  TotalTime (in hours)
        -  ArticleName
        -  Type
    '''
    #table = calculate_energy_table(tasks, prices)

    fig = plt.figure(dpi=50, figsize=(20, 15))
    # first plot the gantt chart and its title
    fig.add_subplot(5, 1, (4,5))
    timerange = plot_gantt(tasks, colors, productions, downtimes=downtimes, startdate=startdate, enddate=enddate)
    if title:
        plt.title(title, y=1.15)

    # now plot the energy prices
    fig.add_subplot(5, 1, 1)
    plt.title('Energy price')
    plt.plot(prices['Euro'], drawstyle='steps-post')
    plt.ylim(bottom=-prices['Euro'].max()*0.05, top=prices['Euro'].max()*1.05)
    plt.xlim(timerange[0], timerange[-1])
    plt.ylabel("€ / kWh")
    
    # plot the energy consumption
    fig.add_subplot(5, 1, 2)
    plt.title('Energy consumption')
    timetasks = tasks[[startdate ,'Power']].set_index(startdate)
    plt.plot(timetasks, drawstyle='steps-post')
    plt.ylim(bottom=-timetasks['Power'].max()*0.05, top=timetasks['Power'].max()*1.05)
    plt.xlim(timerange[0], timerange[-1])
    plt.ylabel("kW")

    # plot the failure rate if available
    if failure_rate is not None:
        fig.add_subplot(5, 1, 3)
        plt.title('Failure rate')
        failure_rate = failure_rate.replace('NaN', np.nan)
        plt.plot(failure_rate, drawstyle='steps-post')
        plt.xlim(timerange[0], timerange[-1])
        plt.ylim(bottom=-0.05, top=1.05)
        plt.ylabel("cdf")

    plt.tight_layout()

def show_gantt(df, start, end):
    plt.figure(figsize=(20, 10))
    df_part = df[df.StartDateUTC.between(start, end) & df.EndDateUTC.between(start, end)]
    all_reasons = list(df.ReasonId.unique())
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