''' 
Do an automatic analysis of the file below and export them to XML for usage
This is an executable file '''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from os.path import splitext, join, exists
from os import mkdir
import os, sys

sys.path.append('..')

from probdist import duration_run_down, Weibull, Lognormal
from lifelines import WeibullFitter, LogNormalFitter

curdir = os.getcwd()

choices = {'prod': ('productionfile.csv', 'prod_speed.csv', 'productionfile_outputfile.xml', 'PastaType'),
           'pack': ('packagingfile_old.csv', 'pack_speed.csv', 'packagingfile_old_outputfile.xml', 'BigPack-simple')}
file_used, file_speed, file_info, choice_type = choices['prod']

break_pauses = 7200 # seconds # breaks will be split in these periods
turn_off_if = 3600 # seconds # the machine can be turned off if time if larger than this!!!! 
# turn_off_if has to be smaller than break_pauses in order for this program to run well
assert (turn_off_if < break_pauses)

try:
    df = pd.read_csv(file_used, parse_dates=['StartDateUTC', 'EndDateUTC'])
    df = df.sort_values('StartDateUTC')
    list_reasons = sorted(list(df.ReasonId.unique()))
except:
    raise NameError('{} not found in this folder ({})'.format(file_used, os.curdir()))

# Make the output folder is it doesn't exist yet
outfolder = splitext(file_used)[0]
if not exists(outfolder):
    mkdir(outfolder)
output_used = join(outfolder,  'outputfile.xml')

# Define all reasons
reasons_relative = [1, 3, 5, 7, 8]
reasons_absolute = [9, 10, 11]
reasons_absolute_between = [9, 10]
reasons_absolute_own = [11]
reasons_break = [0]
reasons_availability = [2]
reasons_not_considered = []

considered_reasons = sorted(list(set(reasons_relative + reasons_absolute + reasons_absolute_between 
                            + reasons_absolute_own + reasons_break + reasons_availability)))

print_all = True; export_all = True

if export_all:
    import xml.etree.ElementTree as ET
    root = ET.Element("failure-info")

# assert that all reasons have been defined
# INITIAL CHECKS
try:
    assert(set(reasons_relative + reasons_absolute + reasons_break + reasons_availability + reasons_not_considered) == set(list_reasons))
except:
    print(reasons_relative, reasons_absolute, reasons_break, reasons_availability, reasons_not_considered, list_reasons)
    raise
assert(set(reasons_absolute_between + reasons_absolute_own) == set(reasons_absolute)) 

def add_column_type(df, from_col='ArticleName', choice='BigPack'):
    choices = ['BigPack', 'Marque', 'PastaType', 'BigPack-simple']
    newname = choice

    if newname == choices[0]:
        stringlist = [' 8', ' 10', ' 12', ' 16', ' 18' ,' 20']
    elif newname == choices[1]:
        stringlist = ['DLL 365', 'VALUE', 'AMBRA', 'EVERYDAY', 'WINNY', 'CARREFOUR', 'ALDI', 'ECO+', 'TOSCA', 'CASA ITALIANA',
                     'EUROSHOPPER', 'AH', 'PASTA MARE', 'OKE', 'TOP BUDGET', 'FIORINI', 'BIO VILLAGE', 'MONOPP', 'RINATURA',
                     'JUMBO', 'BONI', 'CASINO', 'TURINI']
    elif newname == choices[2]:
        stringlist = [['MACARONI', 'MAC.'], 'FUSILLI', ['SPIRELLI', 'SPIRAL', 'TORSADES'], ['HORENTJE', 'HELICES'], 
                      ['VERMICELLI', 'VERMICELL'], ['NOODLES', 'NOUILLES'], 'TORTI',
                     ['PENNE', 'PIPE'], ['ELLEBOOGJES', 'COQUILLETTE', 'COQ.'], 'ZITTI', 'MIE', 'NONE']
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

# ADD TYPE COLUMN
df = add_column_type(df, choice=choice_type)


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
                                     'Quantity': maxtime/3600})
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
                     'Quantity': diff/3600})
                diff -= diff
            #oldprid = production.loc[firstnumber, 'ProductionRequestId']
            #newprid = production.loc[secondnumber, 'ProductionRequestId']
            #if oldprid != newprid:
            #    print('Not the same!')
            #    #print(firstnumber, diff, newstartdate)
            prid -= 1
#             else:
#                 new_row = pd.Series({'ProductionRequestId': oldprid,
#                                      'StartDateUTC': oldenddate,
#                                      'EndDateUTC': newstartdate,
#                                      'Duration': diff,
#                                      'ReasonId': 0,
#                                      'ArticleName': production.loc[firstnumber, 'ArticleName']})
            
            add_df = add_df.append(new_row, ignore_index=True)
        else:
            pass
    production = production.append(add_df, ignore_index=True)
    production = production.sort_values('StartDateUTC').reset_index(drop=True)
    return production

# PREPARATION

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
        else:
            pass
    production = production.append(add_df, ignore_index=True)
    production = production.sort_values('StartDateUTC').reset_index(drop=True)
    return production

# GENERATE RANDOM TABLE WITH ENERGY CONSUMPTION
df_task = df.copy()
df_task['ReasonId'] = np.where(df_task.Type == 'RunTime', 100, df_task.ReasonId)
df_task = df_task[['ProductionRequestId', 'StartDateUTC' , 'EndDateUTC', 'Duration', 'ReasonId', 'ArticleName', 'Quantity']]
#df_task = df_task[df_task['StartDateUTC'] < df_task['StartDateUTC'][0] + pd.to_timedelta('14days')]
df_task = df_task[df_task.ArticleName != 'NONE']
#df_task = df_task[df_task.ProductionRequestId.isin(df.ProductionRequestId.unique()[10:40])]
df_task = add_breaks(df_task, maxtime=break_pauses)
df_task = add_column_type(df_task, choice=choice_type)
df_task.head()

from probplot import merge_per_production, merge_per_article
df_agg = merge_per_production(df, [choice_type, 'ProductionRequestId', 'Type', 'ReasonId'], considered_reasons)
df_merged = merge_per_article(df_agg, choice_type, list_reasons)

def group_productions(df_task):
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

#print(len(df_task))
group = group_productions(df_task)
#print(len(group))
group = remove_breaks(group, turn_off_if)
downtime = construct_downtimes(df_task, considered_reasons)
save_downtimes(downtime, join(outfolder, 'historicalDownPeriods.csv'))

def save_durations(group, output, beforedays=None, afterdays=None, randomfactor=None, ignore_break=True):
    out = group[['Uptime', 'Totaltime', 'Quantity', 'StartDateUTC', 'EndDateUTC', 'ArticleName']].copy()
    out.columns = ['Uptime', 'Totaltime', 'Quantity', 'Start', 'End', 'Product']
    out[['Uptime', 'Totaltime']] = out[['Uptime', 'Totaltime']] / 3600
    out = add_column_type(out , 'Product', 'PastaType')
    out.columns.values[-1] = 'Type'
    to_convert_dates = ['Start', 'End']
    
    # add due date before
    if afterdays:
        beforetime = np.full(np.array(out['End']).shape, afterdays)
        if randomfactor:
            beforetime += np.random.randint(randomfactor + 1, size=beforetime.shape)
        out['After'] = pd.to_datetime(out['End']) - pd.to_timedelta(beforetime, unit="D")
        if ignore_break:
            out.loc[out['Product'] == 'NONE', 'After'] = pd.Timestamp.min
        to_convert_dates.append('After')
    
    # add first possible production date
    if beforedays:
        addedtime = np.full(np.array(out['End']).shape, beforedays)
        if randomfactor:
            addedtime += np.random.randint(randomfactor + 1, size=addedtime.shape)
        out['Before'] = pd.to_datetime(out['End']) + pd.to_timedelta(addedtime, unit="D")
        if ignore_break:
            out.loc[out['Product'] == 'NONE', 'Before']= pd.Timestamp.max
        to_convert_dates.append('Before')

    for col in to_convert_dates:
        out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    out.index.name = 'ID'
    out.to_csv(output)

save_durations(group, os.path.join(outfolder,'generated_jobInfoProd.csv'), beforedays=7, afterdays=7, randomfactor=3)


def energy_per_production(group, file_speed, choice=None, df_merged=None):
    articlenum = len(group.ArticleName.unique())
    fs = pd.read_csv(file_speed, index_col=0)
    fs = fs[fs.ProductDescription.isin(list(group.ArticleName))].reset_index(drop=True)
    #print(fs.ProductDescription)
    rand1 = pd.Series(np.random.random_sample((len(fs),)) * 1 + 2)    # unit price
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
    return energycons

energycons = energy_per_production(group, file_speed, choice=choice_type, df_merged=df_merged)
energycons.to_csv(join(outfolder, 'generated_productRelatedCharacteristics.csv'), index=False)


startdate = group.StartDateUTC.min()
firstofmonth = (startdate - pd.offsets.MonthBegin(1)).floor('D')
enddate = group.StartDateUTC.max()
lastofmonth = (enddate + pd.offsets.MonthEnd(1)).ceil('D')
lastofmonth

def construct_energy_2tarifs(ran, daytarif, nighttarif, starttime, endtime):
    ind = pd.date_range(freq='H', start=ran[0], end=ran[1])
    prices = pd.DataFrame([daytarif] * len(ind), index=ind)
    night = (ind.weekday >= 5) | (ind.hour < endtime) | (ind.hour >= starttime) # saturday or sunday, after 21 and before 6
    prices[night] = nighttarif
    prices.columns = ['Euro']
    prices.index.name = 'Date'
    #prices = prices.loc[prices['Euro'].diff(1) != 0]
    return prices

prices = construct_energy_2tarifs((firstofmonth, lastofmonth), 12, 8, 21, 6)
prices.to_csv(join(outfolder, 'generated_hourly_energy_price.csv'))
prices.head()

# GENERATE GENERAL WEIBULL
# Generate a general Weibull distribution
print('General Weibull distribution:')
print(len('General Weibull distribution:') * '-')
bool_up = (df.Type == 'RunTime')
bool_down = ((df.Type == 'DownTime') &(df.ReasonId.isin(reasons_relative)))
continue_obs = ((df.Type == 'DownTime') &(df.ReasonId.isin(reasons_absolute + reasons_not_considered + reasons_availability)))
stop_obs = (df.Type == 'Break')
uptime, downtime, obs_up, obs_down = duration_run_down(list(df.Duration / 3600), list(bool_up), list(bool_down), list(continue_obs), list(stop_obs), observation=True)
wf = WeibullFitter()
try:
    wf.fit(uptime, obs_up)
    weib = Weibull(wf.lambda_, wf.rho_)
except:
    print(uptime)
    print(item)
    raise
if print_all:
    print(weib)
if export_all:
    general_dist = ET.SubElement(root, 'general_dist')
    general_dist.text = 'weibull'
    general_dist.set("lambda", str(wf.lambda_))
    general_dist.set("rho", str(wf.rho_))


# GENERATE REPAIR TIME DEFINITION
# Generate a lognormal distribution for the repair time
print('Repair time')
print(len('Repair time') * '-')

bool_up = (df.Type == 'RunTime')
bool_down = ((df.Type == 'DownTime') & (df.ReasonId.isin(reasons_relative)))
continue_obs = ((df.Type == 'DownTime') &(df.ReasonId.isin(reasons_absolute + reasons_not_considered + reasons_availability)))
stop_obs = (df.Type == 'Break')
uptime, downtime, obs_up, obs_down = duration_run_down(list(df.Duration / 3600), list(bool_up), list(bool_down), list(continue_obs), list(stop_obs), observation=True)
lnf = LogNormalFitter()
try:
    lnf.fit(downtime, obs_down)
    logn = Lognormal(lnf.sigma_, lnf.mu_)
except:
    raise
if print_all:
    print(logn)
if export_all:
    repair_dist = ET.SubElement(root, 'repair_dist')
    repair_dist.text = 'lognormal'
    repair_dist.set("sigma", str(lnf.sigma_))
    repair_dist.set("mu", str(lnf.mu_))
    repair_dist.set("mean", str(logn.mean_time()))



# GENERATE PM SUGGESTED TIME
# Generate the suggested time between planned maintenance
from probdist import total_cost_maintenance, pm_recommend
cp = 100
cu = 2000

minimum = pm_recommend(weib, cp, cu)
PM = int(minimum)
if print_all:
    print('Time between planned maintenance:', PM, 'hours = less then', int(np.ceil(PM / 24)), 'days')
if export_all:
    maint_time = ET.SubElement(root, 'maint_time')
    maint_time.text = str(PM)
    repair_time = ET.SubElement(root, 'repair_time')
    repair_time.text = str(logn.mean_time() * 10)
plt.plot(minimum, total_cost_maintenance(minimum, weib, cp, cu), 'o')
t_plot = np.linspace(1, minimum * 2, 50)
total, prev, unexp = total_cost_maintenance(t_plot, weib, cp, cu, True)
plt.plot(t_plot, total, label='total cost')
plt.plot(t_plot, prev, label='preventive')
plt.plot(t_plot, unexp, label='unexpected')
plt.legend()
plt.ylabel('Cost per hour')
plt.xlabel(f'Suggested time between planned maintenance: {PM} hours')
plt.ylim(bottom=-total[-1]*0.1, top=total[-1]*1.5)


# GENERATE TYPE-SPECIFIC WEIBULL DIST
# Generate a Weibull distribution for each unique type
l = list(df[choice_type].unique())
print(l)
l.remove('NONE')
weib_dict = {}
availability_dict = {}
if export_all:
    files = ET.SubElement(root, "files")
    inputfile = ET.SubElement(files, "inputfile")
    inputfile.text = file_used
    outputfile = ET.SubElement(files, "outputfile")
    outputfile.text = os.path.split(output_used)[1]
    fail_dist = ET.SubElement(root, "fail_dist")
    fail_dist.text = "weibull"
for item in l:
    print(item)
    print(('-')*len(item))
    df_select = df[(df[choice_type] == item) | (df[choice_type] == 'NONE')]

    from probdist import duration_run_down
    bool_up = (df_select.Type == 'RunTime')
    bool_down = ((df_select.Type == 'DownTime') &(df_select.ReasonId.isin(reasons_relative)))
    continue_obs = ((df_select.Type == 'DownTime') &(df_select.ReasonId.isin(reasons_absolute + reasons_not_considered + reasons_availability)))
    stop_obs = (df_select.Type == 'Break')
    uptime, downtime, obs_up, obs_down = duration_run_down(list(df_select.Duration / 3600), list(bool_up), list(bool_down), list(continue_obs), list(stop_obs), observation=True)
    from probdist import Weibull
    from lifelines import WeibullFitter
    wf = WeibullFitter()
    try:
        wf.fit(uptime, obs_up)
        weib = Weibull(wf.lambda_, wf.rho_)
    except:
        print(uptime)
        print(item)
        raise
    if print_all:
        print(weib)
    if export_all:
        new_element = ET.SubElement(fail_dist, 'dist')
        new_element.set("lambda", str(wf.lambda_))
        new_element.set("rho", str(wf.rho_))
        new_element.text = item
    weib_dict[item] = weib

    df_select_totaluptime = df[(df[choice_type] == item) & (df.Type == 'RunTime')].Duration.sum()
    df_select_totaldowntime = df[(df[choice_type] == item) & (df.Type == 'DownTime') & (df.ReasonId.isin(reasons_availability))].Duration.sum()
    df_availability = df_select_totaluptime / (df_select_totaldowntime + df_select_totaluptime)
    availability_dict[item] = df_availability

if print_all:
    print(availability_dict)
if export_all:
    availability = ET.SubElement(root, "availability")
    availability.text = str(availability_dict)



# GENERATE CONVERSION TIMES
# Make a result for the absolute time between the types
# first make a list of all the production requests and their total length
#import pdb; pdb.set_trace()
#[df.ArticleName != 'NONE']
l = list(df_task.\
         ProductionRequestId.unique())
length_list = []
for prid in l:
    # Save the total length and the type
    df_temp = df_task[df_task.ProductionRequestId == prid]
    totalduration = df_temp.Duration.sum()
    #print(df_temp.columns)
    #import pdb; pdb.set_trace()
    c_type = str(df_temp.loc[:,choice_type].iloc[-1])
    #print(c_type)
    #import pdb; pdb.set_trace()
    

    time_uptonow = np.insert(np.array(np.cumsum((df_temp.Duration)))[:-1:], 0, 0)

    df_temp.loc[:, 'BeforeDuration'] = time_uptonow

    convert_firsthalf = df_temp[(df_temp.BeforeDuration < (totalduration / 2)) & df_temp.ReasonId.isin(reasons_absolute_between)].Duration.sum()
    convert_secondhalf = df_temp[(df_temp.BeforeDuration >= (totalduration / 2)) & df_temp.ReasonId.isin(reasons_absolute_between)].Duration.sum()
    convert_rest = df_temp[df_temp.ReasonId.isin(reasons_absolute_own)].Duration.sum()

    length_list.append([prid, totalduration, c_type, convert_firsthalf, convert_secondhalf, convert_rest])

#print(length_list)


# Use this list to generate the mean conversion time between product types
l = list(df_task[choice_type].unique())
#l.remove('NONE')
sum_conversions = pd.DataFrame(0, index=l, columns=l)
num_conversions = pd.DataFrame(0, index=l, columns=l)
for first, second in zip(length_list[:-1], length_list[1:]):
    first_type = first[2]; second_type = second[2]
    first_convert = first[4]; second_convert = second[3]
    sum_convert = first_convert + second_convert
    sum_conversions.loc[first_type, second_type] += sum_convert
    num_conversions.loc[first_type, second_type] += 1

mean_conversions = sum_conversions/num_conversions


new_mc = mean_conversions.copy()
# Overwrite the diagonals
diagonal = []
for ind in list(mean_conversions.index):
    total_time = mean_conversions.loc[ind, 'NONE'] + mean_conversions.loc['NONE', ind]
    new_mc.loc[ind, ind] = total_time
    #diagonal.append(total_time)
#di = np.diag_indices(new_mc.shape[0])
#new_mc[di] = diagonal

print(new_mc)
# import pdb; pdb.set_trace()

old_values = []
new_values = []
total_diff = 0
mask = new_mc.copy()
mask[:] = 0
from itertools import product
k = 0
for i, j in product(list(new_mc.index), list(new_mc.columns)):
    #print(i, j)
    if (i != j) and (i != 'NONE') and (j != 'NONE'): # no diagonal elements
        #print(i, j)
        conversion = mean_conversions.loc[i, 'NONE'] + mean_conversions.loc['NONE', j]
        new_mc.loc[i, j] = conversion
        old_val = mean_conversions.loc[i, j]
        old_values.append(old_val)
        new_val = conversion
        new_values.append(new_val)
        if old_val > new_val:
            total_diff += (old_val - new_val)
            k += 1
        mask.loc[i, j] = 1
        new_mc.loc[i, j] = conversion

#import pdb; pdb.set_trace()

mean_diff = total_diff / k
print(mean_diff)
new_mc[mask == 1] += mean_diff

for i, j in product(list(new_mc.index), list(new_mc.columns)):
    #print(i, j)
    if (i == 'NONE') or (j == 'NONE'): # go to break
        #print(i, j)
        new_mc.loc[i, j] += (mean_diff / 2)


#import pdb; pdb.set_trace()

if print_all:
    print(mean_conversions)
    print(new_mc)
if export_all:
    newname = splitext(output_used)[0] + '_conversions.csv'
    # fill the nan values with another value from the data
    temp = np.array(new_mc).flatten()
    temp = temp[~np.isnan(temp)]
    mean = np.max(temp)
    mean_export = new_mc.fillna(0)
    # export
    new_mc.fillna(mean).to_csv(newname)
    conversion_times = ET.SubElement(files, "conversion_times")
    conversion_times.text = os.path.split(newname)[1]

cleaning_sum = pd.DataFrame(0, index=l, columns=['Time'])
cleaning_num = pd.DataFrame(0, index=l, columns=['Time'])

for item in length_list:
    item_type = item[2]
    convert_rest = item[5]
    cleaning_sum.loc[item_type, 'Time'] += convert_rest
    cleaning_num.loc[item_type, 'Time'] += 1
cleaning_avg = cleaning_sum / cleaning_num

if print_all:
    print(cleaning_avg)
if export_all:
    newname = splitext(output_used)[0] + '_cleaning.csv'
    cleaning_avg.to_csv(newname)
    cleaning_times = ET.SubElement(files, "cleaning_time")
    cleaning_times.text = os.path.split(newname)[1]


if export_all:
    tree = ET.ElementTree(root)
    tree.write(output_used)
