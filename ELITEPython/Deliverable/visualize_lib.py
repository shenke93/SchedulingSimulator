''' Visualisation routines for the results of the SchedulerV000'''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def show_results(best_result, worst_result):
    plt.plot(best_result)
    plt.plot(worst_result)
    plt.title('Result versus number of iterations')
    return plt.gcf()

def plot_gantt(df_task, reason_str, articlename, startdate='StartDateUTC', enddate='EndDateUTC'):
    df_task['Start'] = (df_task[startdate] - df_task[startdate].iloc[0].floor('D')).dt.total_seconds()/3600
    df_task['End'] = (df_task[enddate] - df_task[startdate].iloc[0].floor('D')).dt.total_seconds()/3600
    # Plot a line for every line of data in your file
    from cycler import cycler
    cy = cycler(color=['b','g','orange','c','m','yellow','steelblue', 'tan',
                                              'lawngreen', 'cyan', 'darkorange', 'crimson', 'greenyellow', 'darkviolet', 'fuchsia',
                                              'palevioletred', 'moccasin',
                                              'rosybrown', 'coral', 'wheat',
                                              'linen']*10).by_key()['color']
    reasons = list(df_task[reason_str].unique())
    color_dict = dict(zip(reasons, list(cy)))
    # for reason, color in zip(reasons, cy):
    #     df_temp = df_task[df_task[reason_str] == reason]
    #     plt.hlines(df_temp[articlename], df_temp['Start'], df_temp['End'], colors=color, lw=4, label=reason)
    
    articles = np.sort(df_task[articlename].unique()).tolist()
    exception = 'NONE'
    if exception in articles:
        i = articles.index(exception)
        articles.pop(i)
        articles.insert(0, exception)
    i = 0
    for article in articles:
        df_temp = df_task[df_task[articlename] == article]
        for item in df_temp.T:
            entry = df_temp.loc[item]
            #import pdb; pdb.set_trace()
            plt.hlines(i, entry['Start'], entry['End'], lw=4, label=entry[reason_str], colors=color_dict[entry[reason_str]])
        i += 1
    plt.yticks(range(0, i), articles)
    #plt.hlines(cps, s_process, f_process, colors="green", lw=4)
    #plt.hlines(cps, s_unload, f_unload, color="blue", lw=4)
    plt.margins(0.1)
    #plt.legend(loc=4)

    lines = []
    import matplotlib.lines as mlines
    for item in color_dict:
        line = mlines.Line2D([],[], color=color_dict[item], label=item)
        lines.append(line)
    plt.legend(bbox_to_anchor=(0, 1.02, 1, 1.02), loc='lower left', borderaxespad=0., handles=lines, mode='expand', ncol=len(color_dict))
    
    # ####
    # handles, labels = plt.gca().get_legend_handles_labels()
    # by_label = dict(zip(labels, handles))
    # key_list = sorted(by_label)
    # value_list = [by_label[key] for key in key_list]
    # plt.legend(value_list, key_list, loc='lower right')
    # ####

    plt.xlabel('Time[h]')
    timerange = np.arange(0, np.max(df_task['End'])+24, 24)
    label = pd.date_range(df_task[startdate].iloc[0].floor('D'), periods = len(timerange))
    plt.xticks(timerange, label, rotation=90)
    plt.xlim(timerange.min(), timerange.max())
    return label

def calculate_energy_cost(df_tasks, df_cost, df_cons, return_table=False):
    lastenddate = df_tasks.iloc[-1]['EndDateUTC']
    new_row = pd.Series({'ProductionRequestId': -1000,
                     'StartDateUTC': lastenddate,
                     'EndDateUTC': lastenddate + pd.Timedelta(1, 's'),
                     'Duration': 1,
                     'ReasonId': 0,
                     'ArticleName': 'NONE'})
    df_tasks = df_tasks.append(new_row, ignore_index=True)
    #print(df_tasks)
    
    # Set timedateindex
    df_tasks = df_tasks.merge(df_cons, how='left', left_on='ArticleName', right_on='Product').set_index('StartDateUTC', drop=True)
    
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
    total_sum = out_table['Price'].sum()
    
    if return_table:
        return total_sum, out_table
    else:
        return total_sum

def show_energy_plot(tasks, prices, energy, title='Schedule', colors='ArticleName'):
    c, table = calculate_energy_cost(tasks, prices, energy, True)

    plt.suptitle(title + ' (Result: {:.2f} €)'.format(c), y=0.02)
    plt.subplot(4,1,(3,4))
    timerange = plot_gantt(tasks, colors, 'ArticleName')

    plt.subplot(4,1,1)
    plt.title('Energy price')
    plt.xlim(timerange[0], timerange[-1])
    plt.plot(table.Euro, drawstyle='steps-post')
    plt.ylim(bottom=-table.Euro.max()*0.05)

    plt.subplot(4,1,2)
    plt.title('Energy consumption')
    plt.xlim(timerange[0], timerange[-1])

    plt.plot(table.Power, drawstyle='steps-post')
    plt.ylim(bottom=0)
    plt.tight_layout()