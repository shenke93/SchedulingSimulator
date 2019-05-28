'''
These are the functions used in the automatic analyser
'''
import numpy as np
import pandas as pd

def add_column_type(df, from_col='ArticleName', choice='BigPack'):
    '''
    Add a column according to a certain type definition
    '''
    choices = ['BigPack', 'Marque', 'PastaType', 'BigPack-simple']
    newname = choice

    if newname == choices[0]:
        stringlist = [' 8', ' 10', ' 12', ' 16', ' 18' ,' 20']
    elif newname == choices[1]:
        stringlist = ['DLL 365', 'VALUE', 'AMBRA', 'EVERYDAY', 'WINNY', 'CARREFOUR', 'ALDI', 'ECO+', 'TOSCA', 'CASA ITALIANA',
                     'EUROSHOPPER', 'AH', 'PASTA MARE', 'OKE', 'TOP BUDGET', 'FIORINI', 'BIO VILLAGE', 'MONOPP', 'RINATURA',
                     'JUMBO', 'BONI', 'CASINO', 'TURINI']
    elif newname == choices[2]:
        stringlist = [['MACARONI', 'MAC.', 'ZITTI'], 'FUSILLI', ['SPIRELLI', 'SPIRAL', 'TORSADES'], ['HORENTJE', 'HELICES'], 
                      ['VERMICELLI', 'VERMICELL'], ['NOODLES', 'NOUILLES'], 'TORTI',
                     ['PENNE', 'PIPE'], ['ELLEBOOGJES', 'COQUILLETTE', 'COQ.'], 'NONE']
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
            if newname == 'BigPack':
                bp = np.where(name.str.contains(s), s + 'X', bp)
            else:
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
            if diff > maxtime:
                new_row = pd.Series({'ProductionRequestId': int(prid),
                                     'StartDateUTC': oldenddate,
                                     'EndDateUTC': oldenddate + pd.Timedelta(maxtime, 's'),
                                     'Duration': maxtime,
                                     'ReasonId': 0,
                                     'ArticleName': 'NONE',
                                     'Quantity': int(maxtime/3600)})
                #print(maxtime)
                #print(maxtime/3600)
                diff -= maxtime
                oldenddate = oldenddate + pd.Timedelta(maxtime, 's')
            else: # diff <= maxtime
                # overwrite the break time
                new_row = pd.Series({'ProductionRequestId': int(prid),
                     'StartDateUTC': oldenddate,
                     'EndDateUTC': newstartdate,
                     'Duration': diff,
                     'ReasonId': 0,
                     'ArticleName': 'NONE',
                     'Quantity': int(diff/3600)})
                diff -= diff

            prid -= 1
            add_df = add_df.append(new_row, ignore_index=True)
    production = production.append(add_df, ignore_index=True)
    production = production.sort_values('StartDateUTC').reset_index(drop=True)
    return production

def group_productions(df_task, considered_reasons):
    group = df_task.groupby('ProductionRequestId').agg({'Quantity':'first','StartDateUTC':'min', 'EndDateUTC':'max', 'ArticleName':'first'}).sort_values(by='StartDateUTC')
    #print(len(group))
    # all of the uptime is counted here
    group_uptime = df_task[df_task.ReasonId.isin([100])].groupby('ProductionRequestId').agg({'Duration':'sum'})
    group_uptime.columns = ['Uptime']
    group_alltime = df_task.groupby('ProductionRequestId').agg({'Duration':'sum'})
    group_alltime.columns = ['Totaltime']
    group_downtime = df_task[df_task.ReasonId.isin(considered_reasons)].groupby('ProductionRequestId').agg({'Duration':'sum'})
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
    out.index.name = 'ID'
    out.to_csv(output)

def save_durations(group, output, beforedays=None, afterdays=None, randomfactor=None, ignore_break=True, 
                   choice=' '):
    ''' Ignore_break adds functionality to ignore the type which is breaks '''
    out = group[['Uptime', 'Totaltime', 'Quantity', 'StartDateUTC', 'EndDateUTC', 'ArticleName']].copy()
    out.columns = ['Uptime', 'Totaltime', 'Quantity', 'Start', 'End', 'Product']
    out[['Uptime', 'Totaltime']] = out[['Uptime', 'Totaltime']] / 3600
    out = add_column_type(out , 'Product', choice)
    out.columns.values[-1] = 'Type'
    to_convert_dates = ['Start', 'End']

    # add first possible release date
    if beforedays:
        addedtime = np.full(np.array(out['End']).shape, beforedays)
        if randomfactor:
            addedtime += np.random.randint(randomfactor + 1, size=addedtime.shape)
        out['Releasedate'] = pd.to_datetime(out['End']) - pd.to_timedelta(addedtime, unit="D")
        if ignore_break:
            out.loc[out['Product'] == 'NONE', 'Releasedate']= pd.Timestamp.min
        to_convert_dates.append('Releasedate')
    
    # add due date
    if afterdays:
        beforetime = np.full(np.array(out['End']).shape, afterdays)
        if randomfactor:
            beforetime += np.random.randint(randomfactor + 1, size=beforetime.shape)
        out['Duedate'] = pd.to_datetime(out['End']) + pd.to_timedelta(beforetime, unit="D")
        if ignore_break:
            out.loc[out['Product'] == 'NONE', 'Duedate'] = pd.Timestamp.max
        to_convert_dates.append('Duedate')
    
    for col in to_convert_dates:
        out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    out.index.name = 'ID'
    out.to_csv(output)

def generate_energy_per_production(group, file_speed, choice=None, df_merged=None):
    articlenum = len(group.ArticleName.unique())
    fs = pd.read_csv(file_speed, index_col=0)
    fs = fs[fs.ProductDescription.isin(list(group.ArticleName))].reset_index(drop=True)
    #print(fs.ProductDescription)
    rand1 = pd.Series(np.random.random_sample((len(fs),)) * 0.2 + 0.5)    # unit price
    rand2 = pd.Series(np.random.random_sample((len(fs),)) * 2 + 0.5)  # power
    energycons = pd.concat([pd.Series(fs.ProductDescription), 
                            rand1,
                            rand2, 
                            pd.Series(fs.TargetProductionRate)], axis=1)
    if choice:
        assert(df_merged is not None)
        energycons = add_column_type(energycons, from_col='ProductDescription', choice=choice)
        energycons = energycons.merge(df_merged[['Availability']], left_on=choice, right_index=True)
        energycons = energycons.drop(choice, axis=1)
        energycons.columns = ['Product', 'UnitPrice',  'Power', 'TargetProductionRate', 'Availability']
    else:
        energycons.columns = ['Product', 'UnitPrice',  'Power', 'TargetProductionRate']
    #energycons.insert(1, 'UnitPrice', 5)
    #energycons.insert(len(energycons.columns), 'TargetProductionRate', 3000)
    #energycons.loc[energycons.Product == 'NONE', 'Power'] = 0
    if choice:
        energycons = energycons.append({'Product': 'NONE', 'UnitPrice': 0, 'Power': 0, 'TargetProductionRate': 1,
                                       'Availability': 1}, ignore_index=True)
        energycons = energycons.append({'Product': 'MAINTENANCE', 'UnitPrice': 0, 'Power': 0, 'TargetProductionRate': 1,
                                       'Availability': 1}, ignore_index=True)
    else:
        energycons = energycons.append({'Product': 'NONE', 'UnitPrice': 0, 
                                        'Power': 0, 'TargetProductionRate': 1}, ignore_index=True)
        energycons = energycons.append({'Product': 'MAINTENANCE', 'UnitPrice': 0, 'Power': 0, 
                                        'TargetProductionRate': 1}, ignore_index=True)
    energycons.loc[:, 'Weight'] = 1
    energycons.loc[energycons.Product == 'NONE', 'Weight'] = 0
    energycons.loc[energycons.Product == 'MAINTENANCE', 'Weight'] = 0
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

def generate_conversion_table(df, reasons, unique_col='ProductionRequestId', type_col='PastaType',  duration_col = 'Duration'):
    l = list(df[unique_col].unique())
    length_list = []
    # First make a list
    # It contains the product id, the product type, conversion of the first half of the job, conversion time of the second half of the job
    for prid in l:
        # Save the total length and the type
        df_temp = df[df[unique_col] == prid]
        half_duration = df_temp.Duration.sum() / 2
        #print(df_temp.columns)
        #type of the next production task
        c_type = str(df_temp.loc[:, type_col].iloc[-1])
        #print(c_type)
        #import pdb; pdb.set_trace()

        time_uptonow = np.insert(np.array(np.cumsum((df_temp[duration_col])))[:-1:], 0, 0)

        df_temp.loc[:, 'BeforeDuration'] = time_uptonow

        convert_firsthalf = df_temp[(df_temp['BeforeDuration'] < half_duration) & df_temp.ReasonId.isin(reasons)][duration_col].sum()
        convert_secondhalf = df_temp[(df_temp['BeforeDuration'] >= half_duration) & df_temp.ReasonId.isin(reasons)][duration_col].sum()
        #convert_rest = df_temp[df_temp.ReasonId.isin(reasons)].Duration.sum()

        length_list.append([prid, c_type, convert_firsthalf, convert_secondhalf])

    # Convert the list into a matrix 
    l = list(df[type_col].unique())
    sum_conversions = pd.DataFrame(0, index=l, columns=l)
    num_conversions = pd.DataFrame(0, index=l, columns=l)
    for first, second in zip(length_list[:-1], length_list[1:]):
        first_type = first[1]; second_type = second[1]
        sum_convert = first[3] + second[2]
        #print(first_type, second_type, first[3], second[2])
        sum_conversions.loc[first_type, second_type] += sum_convert
        num_conversions.loc[first_type, second_type] += 1

    mean_conversions = sum_conversions/num_conversions
    return mean_conversions

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