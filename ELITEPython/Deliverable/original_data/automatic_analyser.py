''' 
Do an automatic analysis of the file below and export them to XML for usage
This is an executable file 
--------------------------
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from os.path import splitext, join, exists
from os import mkdir
import os, sys


sys.path.append(os.path.split(sys.path[0])[0])

from probdist import duration_run_down, Weibull, Lognormal
from lifelines import WeibullFitter, LogNormalFitter
from functions_auto_analyser import *

print(__doc__)

curdir = os.getcwd()

# per choice: (inputfile, target production rate per type, type name)
# outputfolder determined by name of inputfile
choices = {'prod': ('productionfile.csv', 'prod_speed.csv', 'PastaType'),
           'pack': ('packagingfile_old.csv', 'pack_speed.csv', 'BigPack-simple')}
file_used, file_speed, choice_type = choices['prod']

break_pauses = 7200 # seconds # breaks will be split in these periods
turn_off_if = 3600 # seconds # the machine can be turned off if time if larger than this
# turn_off_if has to be smaller than break_pauses in order for this program to run well
assert (turn_off_if < break_pauses)

try:
    df = pd.read_csv(file_used, parse_dates=['StartDateUTC', 'EndDateUTC'])
    df = df.sort_values('StartDateUTC')
    list_reasons = sorted(list(df.ReasonId.unique()))
except:
    raise NameError('{} not found in this folder ({})'.format(file_used, os.curdir))

# Make the output folder is it doesn't exist yet
outfolder = splitext(file_used)[0]
print('Making output folder: ' + outfolder)
if not exists(outfolder):
    mkdir(outfolder)
output_used = join(outfolder,  'outputfile.xml')

# Define all reasons
reasons_relative = [1, 3, 5, 7, 8]
reasons_absolute = [9, 10, 11]
reasons_absolute_conversion = [9, 10]
reasons_absolute_cleaning = [11]
reasons_break = [0]
reasons_availability = [2]
reasons_not_considered = []

considered_reasons = sorted(list(set(reasons_relative + reasons_absolute + reasons_absolute_conversion
                            + reasons_absolute_cleaning + reasons_break + reasons_availability)))

print_all = True; export_all = True

print('Starting XML tree')
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
assert(set(reasons_absolute_cleaning + reasons_absolute_conversion) == set(reasons_absolute)) 

# ADD TYPE COLUMN
print('Adding type column with type = ' + choice_type)
df = add_column_type(df, choice=choice_type)

# NORMALISE THE BREAKS
print('Normalising breaks to have a time of '+ str(break_pauses))
df_task = df.copy()
df_task['ReasonId'] = np.where(df_task.Type == 'RunTime', 100, df_task.ReasonId)
df_task = df_task[['ProductionRequestId', 'StartDateUTC' , 'EndDateUTC', 'Duration', 'ReasonId', 'ArticleName', 'Quantity']]
#df_task = df_task[df_task['StartDateUTC'] < df_task['StartDateUTC'][0] + pd.to_timedelta('14days')]
df_task = df_task[df_task.ArticleName != 'NONE']
#df_task = df_task[df_task.ProductionRequestId.isin(df.ProductionRequestId.unique()[10:40])]
df_task = add_breaks(df_task, maxtime=break_pauses)
df_task = add_column_type(df_task, choice=choice_type)
df_task.head()

# MERGE PER PRODUCTION
from probplot import merge_per_production, merge_per_article
df_agg = merge_per_production(df, [choice_type, 'ProductionRequestId', 'Type', 'ReasonId'], considered_reasons)

# MERGE PER ARTICLE
df_merged = merge_per_article(df_agg, choice_type, list_reasons)

#print(len(df_task))
print('Saving downtimes')
group = group_productions(df_task, considered_reasons)
#print(len(group))
group = remove_breaks(group, turn_off_if)
downtime = construct_downtimes(df_task, considered_reasons)
save_downtimes(downtime, join(outfolder, 'historicalDownPeriods.csv'))

print('Saving job info')
save_durations(group, os.path.join(outfolder,'generated_jobInfoProd.csv'), beforedays=7, afterdays=7, randomfactor=3)

print('Generating product related characteristics')
energycons = generate_energy_per_production(group, file_speed, choice=choice_type, df_merged=df_merged)
# GENERATE THE MEAN PRODUCT RELATED CHARACTERISTIC
tempmean = energycons[(energycons.loc[:, 'Product'] != 'NONE') | (energycons.loc[:, 'Product'] != 'MAINTENANCE')].mean()
tempmean['Product'] = 'MEAN'
energycons = energycons.append(tempmean, ignore_index=True)
energycons.to_csv(join(outfolder, 'generated_productRelatedCharacteristics.csv'), index=False)

startdate = group.StartDateUTC.min()
firstofmonth = (startdate - pd.offsets.MonthBegin(1)).floor('D')
enddate = group.StartDateUTC.max()
lastofmonth = (enddate + pd.offsets.MonthEnd(1)).ceil('D')

print('Constructing energy prices during the period of the file')
prices = construct_energy_2tarifs((firstofmonth, lastofmonth), 12, 8, 21, 6)
prices.to_csv(join(outfolder, 'generated_hourly_energy_price.csv'))
prices.head()

# GENERATE GENERAL WEIBULL
# Generate a general Weibull distribution
print('General Weibull distribution:')
print(len('General Weibull distribution:') * '-')
bool_up = (df.Type == 'RunTime')
bool_down = ((df.Type == 'DownTime') & (df.ReasonId.isin(reasons_relative)))
continue_obs = ((df.Type == 'DownTime') & (df.ReasonId.isin(reasons_absolute + reasons_not_considered + reasons_availability)))
stop_obs = (df.Type == 'Break')
uptime, downtime, obs_up, obs_down = duration_run_down(list(df.Duration / 3600), list(bool_up), list(bool_down), list(continue_obs), list(stop_obs), observation=True)
wf = WeibullFitter()
try:
    wf.fit(uptime, obs_up)
    weib = Weibull(wf.lambda_, wf.rho_)
except:
    print(uptime)
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
cu = 300

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
t_plot = np.linspace(1, float(minimum * 2), 50)
total, prev, unexp = total_cost_maintenance(t_plot, weib, cp, cu, True)
#import pdb; pdb.set_trace()
plt.plot(t_plot, total, label='total cost')
plt.plot(t_plot, prev, label='preventive')
plt.plot(t_plot, unexp, label='unexpected')
plt.legend()
plt.ylabel('Cost per hour')
plt.xlabel(f'Suggested time between planned maintenance: {PM} hours')
plt.ylim(bottom=-total[-1]*0.1, top=total[-1]*1.5)
plt.ioff()
plt.show()


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
print('Generating conversion times between the types')
print('Exporting the conversion time matrix')
mean_conversions = generate_conversion_table(df_task, reasons_absolute_conversion + reasons_absolute_cleaning, 'ProductionRequestId', choice_type)

if print_all:
    print(mean_conversions)
#import pdb; pdb.set_trace()

print('Adapting the conversion time matrix - Redefining diagonal')
new_mc = adapt_standard_matrix(mean_conversions)

if print_all:
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

# print('Generating cleaning times between the types')
# print('Exporting the cleaning time matrix')
# mean_cleaning = generate_conversion_table(df_task, reasons_absolute_cleaning, 'ProductionRequestId', choice_type)

# print('Adapting the cleaning time matrix - Redefining diagonal')
# new_mc = adapt_standard_matrix(mean_cleaning)

# if print_all:
#     print(mean_cleaning)
#     print(new_mc)
# if export_all:
#     newname = splitext(output_used)[0] + '_cleaning.csv'
#     # fill the nan values with another value from the data
#     temp = np.array(new_mc).flatten()
#     temp = temp[~np.isnan(temp)]
#     mean = np.max(temp)
#     mean_export = new_mc.fillna(0)
#     # export
#     new_mc.fillna(mean).to_csv(newname)
#     conversion_times = ET.SubElement(files, "cleaning_times")
#     conversion_times.text = os.path.split(newname)[1]

# cleaning_sum = pd.DataFrame(0, index=l, columns=['Time'])
# cleaning_num = pd.DataFrame(0, index=l, columns=['Time'])

# for item in length_list:
#     item_type = item[2]
#     convert_rest = item[5]
#     cleaning_sum.loc[item_type, 'Time'] += convert_rest
#     cleaning_num.loc[item_type, 'Time'] += 1
# cleaning_avg = cleaning_sum / cleaning_num

# if print_all:
#     print(cleaning_avg)
# if export_all:
#     newname = splitext(output_used)[0] + '_cleaning.csv'
#     cleaning_avg.to_csv(newname)
#     cleaning_times = ET.SubElement(files, "cleaning_time")
#     cleaning_times.text = os.path.split(newname)[1]


if export_all:
    tree = ET.ElementTree(root)
    tree.write(output_used)
