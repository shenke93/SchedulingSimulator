'''
These are the functions used in the automatic analyser
'''
import numpy as np
import pandas as pd
from itertools import product
import matplotlib.pyplot as plt
import matplotlib

def add_column_type(df, from_col='ArticleName', choice='BigPack'):
    '''
    Add a column according to a certain type definition
    '''
    choices = ['BigPack', 'Marque', 'PastaType', 'BigPack-simple']
    newname = choice

    if newname == choices[0]:
        stringlist = [['8X', ' 8'], ['10X', ' 10'], ['12X', ' 12'], ['16X',' 16'], 
                      ['18X', ' 18'] ,['20X', ' 20']]
    elif newname == choices[1]:
        stringlist = ['DLL 365', 'VALUE', 'AMBRA', 'EVERYDAY', 'WINNY', 'CARREFOUR', 'ALDI', 'ECO+', 'TOSCA', 'CASA ITALIANA',
                     'EUROSHOPPER', 'AH', 'PASTA MARE', 'OKE', 'TOP BUDGET', 'FIORINI', 'BIO VILLAGE', 'MONOPP', 'RINATURA',
                     'JUMBO', 'BONI', 'CASINO', 'TURINI']
    elif newname == choices[2]:
        stringlist = [['MACARONI', 'MAC.'], 'FUSILLI', ['SPIRELLI', 'SPIRAL', 'TORSADES'], ['HORENTJE', 'HELICES'], 
                      ['VERMICELLI', 'VERMICELL'], ['NOODLES', 'NOUILLES'], 'TORTI',
                     ['PENNE', 'PIPE'], ['ELLEBOOGJE', 'ELLEBOOG', 'COQUILLETTE', 'COQ.'], 'NONE']
    elif newname == choices[3]:
        stringlist = [ ['SMALL', ' 8', ' 10', ' 12'], ['LARGE', ' 16', ' 18', ' 20'], 'NONE']
    else:
        raise NameError("The choice '{}' is not defined".format(newname))
    
    # Generate a new column with categories in the dataframe
    bp = np.full(df.shape[0], 'Other')
    name = df[from_col]
    for s in stringlist:
        if type(s) == list:
            new_s = ('|'.join(s))
            bp = np.where(name.str.contains(new_s), s[0], bp)
        else:
            # if newname == 'BigPack':
            #     bp = np.where(name.str.contains(s), s + 'X', bp)
            # else:
            bp = np.where(name.str.contains(s), s, bp)
    df[newname] = bp
    return df

def add_breaks(production, maxtime=7200):
    add_df = pd.DataFrame([], columns = production.columns)
    prid = -1
    for firstnumber, secondnumber in zip(production[:-1].T, production[1:].T):
        oldenddate = production.loc[firstnumber, 'EndDateUTC']
        newstartdate = production.loc[secondnumber, 'StartDateUTC']
        diff = (newstartdate - oldenddate).total_seconds()
        oldprid = production.loc[firstnumber, 'ProductionRequestId']
        newprid = production.loc[secondnumber, 'ProductionRequestId']
        # This loop counts out the breaks and splits it in periods of maxtime and one period of maxtime + diff
        while diff > 0:
            #print(diff)
            if (maxtime is not None) and (diff > maxtime):
                filldict = {'ProductionRequestId': int(prid),
                                     'StartDateUTC': oldenddate,
                                     'EndDateUTC': oldenddate + pd.Timedelta(maxtime, 's'),
                                     'Duration': maxtime,
                                     'ReasonId': 0,
                                     'ArticleName': 'NONE',
                                     'ArticleCode': '000000EU',
                                     'Quantity': int(maxtime/3600),
                                     'Type': 'Break'}
                filldict = {k: v for k, v in filldict.items() if k in list(production.columns)}
                new_row = pd.Series(filldict)
                #print(maxtime)
                #print(maxtime/3600)
                diff -= maxtime
                oldenddate = oldenddate + pd.Timedelta(maxtime, 's')
            else: # diff <= maxtime
                # overwrite the break time
                filldict = {'ProductionRequestId': int(prid),
                     'StartDateUTC': oldenddate,
                     'EndDateUTC': newstartdate,
                     'Duration': diff,
                     'ReasonId': 0,
                     'ArticleName': 'NONE',
                     'ArticleCode': '000000EU',
                     'Quantity': int(diff/3600),
                     'Type': 'Break'}
                filldict = {k: v for k, v in filldict.items() if k in list(production.columns)}
                new_row = pd.Series(filldict)
                diff -= diff

            prid -= 1
            add_df = add_df.append(new_row, ignore_index=True)
    production = production.append(add_df, ignore_index=True)
    production = production.sort_values('StartDateUTC').reset_index(drop=True)
    return production

def group_productions(df_task, considered_reasons):
    group = df_task.groupby('ProductionRequestId')\
            .agg({'Quantity':'last','StartDateUTC':'min', 'EndDateUTC':'max', 'ArticleName':'first'})\
            .sort_values(by='StartDateUTC')
    #print(len(group))
    # all of the uptime is counted here
    group_uptime = df_task[df_task['Type'] == 'RunTime'].groupby('ProductionRequestId')\
                   .agg({'Duration':'sum'})
    group_uptime.columns = ['Uptime']
    group_alltime = df_task.groupby('ProductionRequestId').agg({'Duration':'sum'})
    group_alltime.columns = ['Totaltime']
    group_downtime = df_task[(df_task['Type'] == 'DownTime') 
                             & df_task['ReasonId'].isin(considered_reasons)].groupby('ProductionRequestId')\
                     .agg({'Duration':'sum'})
    group_downtime.columns = ['Downtime']
    group = pd.concat([group_uptime, group_downtime, group_alltime, group], axis=1)
    group.loc[group.ArticleName == 'NONE', 'Uptime'] = group.loc[group.ArticleName == 'NONE', 'Totaltime']
    group = group.sort_values(by='StartDateUTC')
    group.index = group.index.astype(int)
    group = group.fillna(0)
    return group

def remove_breaks(group, min_length=3600):
    df = group.copy()
    j = 0
    while j < len(df):
        temp = df.iloc[j]
        if (temp['ArticleName'] == 'NONE') & (temp['Totaltime'] < min_length):
            # don't turn off the machine (no energy saving)
            curidx = temp.name
            previdx = df.iloc[j-1].name
            if (j > 0): #& (df.loc[previdx, 'ArticleName'] != 'NONE'):
                # extend the previous job
                df.loc[previdx, 'EndDateUTC'] = df.loc[curidx, 'EndDateUTC']
                df.loc[previdx, 'Totaltime'] += df.loc[curidx, 'Totaltime']
                df.loc[previdx, 'Uptime'] += df.loc[curidx, 'Uptime']
                df.loc[previdx, 'Downtime'] += df.loc[curidx, 'Downtime']
                df = df.drop(curidx)
                j -= 1
            else:
                pass
                #print('Something unexpected happened!')
                #print(curidx, df.loc[previdx, 'ArticleName'])
        j += 1
    return df

def construct_downtimes(group, reasons):
    dt = group.copy()
    dt = dt[dt['ReasonId'].isin(reasons)]
    return dt

def save_downtimes(dt, output):
    out = dt.copy()
    out = out[['StartDateUTC', 'EndDateUTC']]
    out = out.reset_index(drop=True)
    out.index.name = 'index'
    out.to_csv(output)

def generate_durations(group, beforedays=None, afterdays=None, randomfactor=None, ignore_break=True, 
                   choice=' '):
    ''' Ignore_break adds functionality to ignore the type which is breaks '''
    out = group[['Uptime', 'Totaltime', 'Quantity', 'StartDateUTC', 'EndDateUTC', 'ArticleName']].copy()
    out.columns = ['Uptime', 'Totaltime', 'Quantity', 'Start', 'End', 'Product']
    out[['Uptime', 'Totaltime']] = out[['Uptime', 'Totaltime']] / 3600
    if choice in ['BigPack', 'Marque', 'PastaType', 'BigPack-simple']:
        out = add_column_type(out , 'Product', choice)
    else:
        pass
    out.columns.values[-1] = 'Type'
    to_convert_dates = ['Start', 'End']

    # add first possible release date
    if beforedays:
        addedtime = np.full(np.array(out['End']).shape, beforedays)
        if randomfactor:
            addedtime += np.random.randint(randomfactor + 1, size=addedtime.shape)
        out['Releasedate'] = pd.to_datetime(out['End']) - pd.to_timedelta(addedtime, unit="D")
        if ignore_break:
            out.loc[out['Type'] == 'NONE', 'Releasedate']= pd.Timestamp.min
        to_convert_dates.append('Releasedate')
    
    # add due date
    if afterdays:
        beforetime = np.full(np.array(out['End']).shape, afterdays)
        if randomfactor:
            beforetime += np.random.randint(randomfactor + 1, size=beforetime.shape)
        out['Duedate'] = pd.to_datetime(out['End']) + pd.to_timedelta(beforetime, unit="D")
        if ignore_break:
            out.loc[out['Type'] == 'NONE', 'Duedate'] = pd.Timestamp.max
        to_convert_dates.append('Duedate')
    
    for col in to_convert_dates:
        out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    out.index.name = 'Product'
    return out
    #out.to_csv(output)

def generate_energy_per_production(group, fixed_price=8, variable_price=4, fixed_energy=8, variable_energy=4):
    
    #articlenum = len(group.ArticleName.unique())
    #fs = pd.read_csv(file_speed, index_col=0)
    
    #file_speed = file_speed[file_speed['ProductionRequestId'].isin(group.index.tolist())]\
    #             .reset_index(drop=True)
    # group = group.merge(file_speed, left_index=True, right_on='ProductionRequestId', how='left')\
    #                     .set_index('ProductionRequestId').fillna(1.0)
    rand1 = pd.Series(np.random.random_sample((len(group),)) * 4 + 8, index=group.index, name='UnitPrice')    # unit price
    rand2 = pd.Series(np.random.random_sample((len(group),)) * 4 + 8, index=group.index, name='Power')  # power
    rand3 = pd.Series(np.random.randint(1, 10, (len(group),)), index=group.index, name='Weight') #weights
    
    energycons = pd.concat([group, 
                            rand1,
                            rand2,
                            rand3], axis=1)
    
    energycons.loc[energycons['Type']=='NONE', 'UnitPrice'] = 0.0
    energycons.loc[energycons['Type']=='NONE', 'Power'] = 0.0
    energycons.loc[energycons['Type']=='NONE', 'Weight'] = 0
    energycons.loc[energycons['Type']=='NONE', 'Quantity'] = \
        energycons.loc[energycons['Type']=='NONE', 'Totaltime']
    return energycons

def construct_energy_2tarifs(ran, daytarif, nighttarif, starttime, endtime):
    ind = pd.date_range(freq='H', start=ran[0], end=ran[1])
    prices = pd.DataFrame([daytarif] * len(ind), index=ind)
    night = (ind.weekday >= 5) | (ind.hour < endtime) | (ind.hour >= starttime) # saturday or sunday, after 21 and before 6
    prices[night] = nighttarif
    prices.columns = ['Euro']
    prices.index.name = 'Date'
    #prices = prices.loc[prices['Euro'].diff(1) != 0]
    return prices


class ConversionTable(object):
    
    def __init__(self, df, reasons, unique_col='ProductionRequestId', type_col='PastaType', duration_col='Duration'):
        self.df = df
        self.reasons = reasons
        self.unique_col = unique_col
        self.type_col = type_col
        self.duration_col = duration_col
        self.job_list = self.generate_conversion_table()

    def generate_conversion_table(self):
        l = list(self.df[self.unique_col].unique())
        output_list = []
        # First make a list
        # It contains the product id, the product type, conversion of the first half of the job, conversion time of the second half of the job, breaktime between the jobs if short
        for prid in l:
            # Save the total length and the type
            df_temp = self.df[self.df[self.unique_col] == prid]
            half_duration = df_temp[self.duration_col].sum() / 2
            #type of the production task
            c_type = str(list(df_temp[self.type_col])[-1])
            #print(c_type)
            #import pdb; pdb.set_trace()

            time_uptonow = np.insert(np.array(np.cumsum((df_temp[self.duration_col])))[:-1:], 0, 0)

            #df_temp['BeforeDuration'] = time_uptonow

            convert_firsthalf = df_temp[(time_uptonow < half_duration) & df_temp.ReasonId.isin(self.reasons)][self.duration_col].sum()
            convert_secondhalf = df_temp[(time_uptonow >= half_duration) & df_temp.ReasonId.isin(self.reasons)][self.duration_col].sum()
            #convert_rest = df_temp[df_temp.ReasonId.isin(reasons)].Duration.sum()

            output_list.append([prid, c_type, convert_firsthalf, convert_secondhalf])
        return output_list
        
    # Convert into matrix:
    #l = 
    
    def output_matrix(self):
        # Convert into matrix with all separate times for conversions
        l = sorted(list(self.df[self.type_col].unique()))
        indexer = range(len(l))
        mat = [[[] for i in indexer] for j in indexer] 
        for first, second in zip(self.job_list[:-1], self.job_list[1:]):
            first_type = first[1]; second_type = second[1]
            sum_convert = first[3] + second[2]
            mat[l.index(first_type)][l.index(second_type)].append(sum_convert)
        return (l, mat)
            
    
    def return_mean_conversions(self, drop_zeros=True):
        from itertools import product
        # Convert the list into a matrix
        l, mat = self.output_matrix()
        copy_mat = mat.copy()
        for i, j in product(range(len(l)), range(len(l))):
            #all_nonzeros = [k for k in mat[i][j] if k != 0]
            all_complete = mat[i][j]
            mean_conversions = np.mean(all_complete)
            copy_mat[i][j] = mean_conversions
        pd_out = pd.DataFrame(copy_mat, index=l, columns=l)
        return pd_out
    
    def return_median_conversions(self, drop_zeros=True):
        from itertools import product
        # Convert the list into a matrix
        l, mat = self.output_matrix()
        copy_mat = mat.copy()
        for i, j in product(range(len(l)), range(len(l))):
            #all_nonzeros = [k for k in mat[i][j] if k != 0]
            all_complete = mat[i][j]
            median_conversions = np.median(all_complete)
            copy_mat[i][j] = median_conversions
        pd_out = pd.DataFrame(copy_mat, index=l, columns=l)
        return pd_out
    
    def return_num_conversions(self):
        from itertools import product
        # Convert the list into a numeric matrix
        l, mat = self.output_matrix()
        copy_mat = mat.copy()
        for i, j in product(range(len(l)), range(len(l))):
            #all_nonzeros = [k for k in mat[i][j] if k != 0]
            all_complete = mat[i][j]
            num_conversions = len(all_complete)
            copy_mat[i][j] = num_conversions
        pd_out = pd.DataFrame(copy_mat, index=l, columns=l)
        return pd_out
    
    def return_variance_conversions(self):
        from itertools import product
        # Convert into a matrix with the variance of the conversion
        l, mat = self.output_matrix()
        copy_mat = mat.copy()
        for i, j in product(range(len(l)), range(len(l))):
            all_complete = mat[i][j]
            variance_conversions = np.var(all_complete)
            copy_mat[i][j] = variance_conversions
        pd_out = pd.DataFrame(copy_mat, index=l, columns=l)
        return pd_out
    
    def return_std_conversions(self):
        from itertools import product
        # Convert into a matrix with the variance of the conversion
        l, mat = self.output_matrix()
        copy_mat = mat.copy()
        for i, j in product(range(len(l)), range(len(l))):
            all_complete = mat[i][j]
            variance_conversions = np.std(all_complete)
            copy_mat[i][j] = variance_conversions
        pd_out = pd.DataFrame(copy_mat, index=l, columns=l)
        return pd_out


def adapt_standard_matrix(mean_conversions):
    new_mc = mean_conversions.copy()
    # Overwrite the diagonals, since there are more measurements relating to NONE

    # The rows and columns related to the breaks are most reliable, since the mainly happens, while other conversions are much less frequent
    # We will use this row and column to calculate the other values:

    import statistics

    penalty = statistics.mean(list(new_mc.loc[:, 'NONE']) + list(new_mc.loc['NONE', :]))

    from itertools import product
    for i, j in product(list(new_mc.index), list(new_mc.columns)):
        if (i != 'NONE') and (j != 'NONE'): # No earlier used row or column
            # print(i, j)
            conversion = mean_conversions.loc[i, 'NONE'] + mean_conversions.loc['NONE', j]
            if (i != j): # No diagonal element
                # Add penalty time
                conversion += penalty
            new_mc.loc[i, j] = conversion

    new_mc.loc[:, 'NONE'] = new_mc.loc[:, 'NONE'] / 2
    new_mc.loc['NONE', :] = new_mc.loc['NONE', :] / 2
    
    # adapt the main diagonals to have value of zero
    for i in list(new_mc.index):
        new_mc.loc[i, i] = 0
    


    # # Create new value for the diagonals
    # diagonal = []
    # old_diag = pd.Series(np.diag(mean_conversions), index=mean_conversions.index).fillna(np.mean(np.diag(mean_conversions)))
    # row = mean_conversions.loc[:, 'NONE']; col = mean_conversions.loc['NONE', :]
    # row = row.fillna(row.mean()); col = col.fillna(col.mean())
    # new_diag = row + col

    # surplus = (old_diag - new_diag).mean()

    # for ind in list(mean_conversions.index):
    #     new_mc.loc[ind, ind] = new_diag[ind]

    # # get the diagonal values which are not zero
    # old_values = []
    # new_values = []
    # total_diff = 0

    # # Make new empty dataframe
    # mask = new_mc.copy(); mask[:] = 0

    # from itertools import product
    # k = 0
    # for i, j in product(list(new_mc.index), list(new_mc.columns)):
    #     if (i != j) and (i != 'NONE') and (j != 'NONE'): # no diagonal elements and no earlier used row or column
    #         #print(i, j)
    #         conversion = mean_conversions.loc[i, 'NONE'] + mean_conversions.loc['NONE', j]
    #         new_mc.loc[i, j] = conversion
    #         old_val = mean_conversions.loc[i, j]
    #         old_values.append(old_val)
    #         new_val = conversion
    #         new_values.append(new_val)
    #         if old_val > new_val:
    #             total_diff += (old_val - new_val)
    #             k += 1
    #         mask.loc[i, j] = 1
    #         new_mc.loc[i, j] = conversion

    # mean_diff = total_diff / k
    # # add the mean difference to the masked values
    # new_mc[mask == 1] += mean_diff

    # for i, j in product(list(new_mc.index), list(new_mc.columns)):
    #     #print(i, j)
    #     if (i == 'NONE') or (j == 'NONE'): # go to break
    #         #print(i, j)
    #        new_mc.loc[i, j] += surplus # add this to the diagonals
    
    return new_mc

def plot_hist(runtime, obs_run, cutoff_perc, fitter):
    # alpha ~ MTBF only if beta close to 1
    from probdist import make_hist_frame, sturges_rule
    from lifelines import KaplanMeierFitter
    import matplotlib.pyplot as plt
    #kmf = KaplanMeierFitter()
    numbins = sturges_rule(len(runtime))

    maxt = np.percentile(np.array(runtime), cutoff_perc)
    mint = 0

    df_hist, ran = make_hist_frame(runtime, obs_run, numbins=numbins, range=(mint, maxt), return_bins=True)
    t = np.linspace(np.min(ran), np.max(ran), 100)
    plt.figure(figsize=(10,5))
    #x = np.linspace(0, maxt, numbins)
    c_fail = df_hist['FailCDF']
    p_fail = df_hist['Failures']/len(runtime)
    plt.bar(ran[:-1] + (ran[1]-ran[0])/2, p_fail, width=ran[1]-ran[0], edgecolor='k')
    plt.bar(ran[:-1] + (ran[1]-ran[0])/2, c_fail, width=ran[1]-ran[0], 
            alpha=0.1, edgecolor='k'#, yerr=df_hist['Std']**(0.5)
            )
    plt.xlabel(r'time (h)')
    plt.ylabel(r'F(t)')
    plt.plot(t , fitter.failure_cdf(t), 'r', label=fitter)
    #ax = plt.gca()
    #ax.fill_between(t, weib_low.failure_cdf(t), weib_high.failure_cdf(t), alpha=0.3, color='r', zorder=3)
    #kmf.fit(runtime, event_observed=obs_run)
    #plt.plot(1-kmf.survival_function_, color='g', drawstyle=('steps-post'))
    plt.xlim(0, maxt)
    plt.legend()
    return df_hist, ran

def heatmap(data, row_labels, col_labels, ax=None,
                cbar_kw={}, cbarlabel="", **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.

    Parameters
    ----------
    data
        A 2D numpy array of shape (N, M).
    row_labels
        A list or array of length N with the labels for the rows.
    col_labels
        A list or array of length M with the labels for the columns.
    ax
        A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
        not provided, use current axes or create a new one.  Optional.
    cbar_kw
        A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    cbarlabel
        The label for the colorbar.  Optional.
    **kwargs
        All other arguments are forwarded to `imshow`.
    """

    if not ax:
        ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

    # We want to show all ticks...
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    # ... and label them with the respective list entries.
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=True, bottom=False,
                labeltop=True, labelbottom=False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-30, ha="right",
            rotation_mode="anchor")

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)

    return im, cbar


def annotate_heatmap(im, data=None, valfmt="{x:.2f}",
                    textcolors=["black", "white"],
                    threshold=None, **textkw):
    """
    A function to annotate a heatmap.

    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A list or array of two color specifications.  The first is used for
        values below a threshold, the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """

    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
            verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)

    return texts