'''
Do an automatic analysis of the file below and export them to XML for usage
This is an executable file
--------------------------
Run the executable from the folder where you want the output
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns; sns.set_style('white')
#matplotlib.use('Agg')
from os.path import splitext, join, exists
from os import mkdir
import os, sys

# Define all reasons
reasons_relative = [7]
reasons_absolute = [9, 10, 11]
reasons_absolute_conversion = [9, 10]
reasons_absolute_cleaning = [11]
reasons_break = []
reasons_availability = [0, 1, 2, 3, 5, 8]
reasons_not_considered = []

# Define cost of preventive maintenance and of unexpected maintenance
cp = 100
cu = 250

assert(set(reasons_absolute_cleaning + reasons_absolute_conversion) == set(reasons_absolute)),\
    'Absolute reasons are incorrectly defined'
considered_reasons = sorted(list(set(reasons_relative + reasons_absolute + reasons_absolute_conversion
                            + reasons_absolute_cleaning + reasons_break + reasons_availability)))

print_all = True; export_all = True
turn_off_if = 3600 # seconds # the machine can be turned off if time if larger than this
break_pauses = None # seconds # breaks will be split in these periods

# turn_off_if has to be smaller than break_pauses in order for this program to run well
if (turn_off_if is not None) and (break_pauses is not None):
    assert (turn_off_if < break_pauses), 'Variable break_pauses should be larger then turn_off_if'

def plot_hist(runtime, obs_run, cutoff_perc, fitter):
    # alpha ~ MTBF only if beta close to 1
    from probdist import make_hist_frame, sturges_rule
    from lifelines import KaplanMeierFitter
    #kmf = KaplanMeierFitter()
    numbins = sturges_rule(len(runtime))

    maxt = np.percentile(np.array(runtime), cutoff_perc)
    mint = 0

    df_hist, ran = make_hist_frame(runtime, obs_run, numbins=numbins, range=(mint, maxt), return_bins=True)
    t = np.linspace(np.min(ran), np.max(ran), 100)
    plt.figure(figsize=(10,5))
    x = np.linspace(0, maxt, numbins)
    c_fail = df_hist['FailCDF']
    p_fail = df_hist['Failures']/len(runtime)
    plt.bar(ran[:-1] + (ran[1]-ran[0])/2, p_fail, width=ran[1]-ran[0], edgecolor='k')
    plt.bar(ran[:-1] + (ran[1]-ran[0])/2, c_fail, width=ran[1]-ran[0], 
            alpha=0.1, edgecolor='k'#, yerr=df_hist['Std']**(0.5)
            )
    plt.xlabel(r'time (h)')
    plt.ylabel(r'F(t)')
    plt.plot(t , fitter.failure_cdf(t), 'r', label=fitter)
    ax = plt.gca()
    #ax.fill_between(t, weib_low.failure_cdf(t), weib_high.failure_cdf(t), alpha=0.3, color='r', zorder=3)
    #kmf.fit(runtime, event_observed=obs_run)
    #plt.plot(1-kmf.survival_function_, color='g', drawstyle=('steps-post'))
    plt.xlim(0, maxt)
    plt.legend()
    return df_hist, ran


sys.path.append(os.path.split(sys.path[0])[0])

from probdist import duration_run_down, Weibull, Lognormal
from lifelines import WeibullFitter, LogNormalFitter
from functions_auto_analyser import add_column_type, add_breaks, group_productions, remove_breaks, construct_downtimes,\
                                    save_downtimes, generate_durations, generate_energy_per_production,\
                                    construct_energy_2tarifs, adapt_standard_matrix, ConversionTable

print(__doc__)

curdir = os.path.dirname(sys.argv[0])
os.chdir(os.path.dirname(sys.argv[0]))

# per choice: (inputfile, target production rate per type, type name)
# outputfolder determined by name of inputfile
choices = {'production': ('productionfile.csv', 'prod_speed.csv', 'PastaType'),
           'packaging': ('packagingfile_old.csv', 'pack_speed.csv', 'BigPack-simple')}
for choice in choices:
    print(f'Executing for: {choice}')
    file_used, file_speed, choice_type = choices[choice]
    try:
        df = pd.read_csv(file_used, parse_dates=['StartDateUTC', 'EndDateUTC'])
        df = df.sort_values('StartDateUTC')
        list_reasons = sorted(list(df.ReasonId.unique()))
    except:
        raise NameError('{} not found in this folder ({})'.format(file_used, os.curdir))

    # Make the output folder if it doesn't exist yet
    outfolder = splitext(file_used)[0]
    outfolder = os.path.join(curdir, outfolder)
    if not exists(outfolder):
        print('Making output folder: ' + outfolder)
        mkdir(outfolder)
    output_used = os.path.join(outfolder,  'outputfile.xml')

    print('> Starting XML tree')
    if export_all:
        import xml.etree.ElementTree as ET
        root = ET.Element("failure-info")

    # assert that all reasons have been defined
    # INITIAL CHECKS
    try:
        assert(set(reasons_relative + reasons_absolute + reasons_break + \
                   reasons_availability + reasons_not_considered) == set(list_reasons)),\
                       'Not all reasons have been defined'
    except:
        print(reasons_relative, reasons_absolute, reasons_break, reasons_availability, 
              reasons_not_considered, list_reasons)
        raise
    

    print(df.head())

    df = add_column_type(df, choice=choice_type)

    # NORMALISE THE BREAKS
    print('Normalising breaks to have a time of '+ str(break_pauses))
    df_task = df.copy()
    # Set the ReasonId to 100 if there is RunTime
    df_task['ReasonId'] = np.where(df_task['Type'] == 'RunTime', 100, df_task['ReasonId'])
    df_task = df_task[['ProductionRequestId', 'StartDateUTC' , 'EndDateUTC', 
                       'Duration', 'ReasonId', 'ArticleName', 'Quantity']]
    df_task = df_task[df_task['ArticleName'] != 'NONE']
    df_task = add_breaks(df_task, maxtime=break_pauses)
    
    # ADD TYPE COLUMN
    print('Adding type column with type = ' + choice_type)
    df_task = add_column_type(df_task, choice=choice_type)
    #df_task.head()
    
    #print(df_task.head())

    # # MERGE PER PRODUCTION
    # from probplot import merge_per_production
    # df_agg = merge_per_production(df, [choice_type, 'ProductionRequestId', 'Type', 'ReasonId'], 
    #                               considered_reasons)

    # # MERGE PER ARTICLE
    # from probplot import merge_per_article
    # df_merged = merge_per_article(df_agg, choice_type, list_reasons)

    #print(len(df_task))
    print('Saving downtimes')
    group = group_productions(df_task, considered_reasons)
    print(group.head())
    
    
    
    #print(len(group))
    group = remove_breaks(group, turn_off_if)
    downtime = construct_downtimes(df_task, considered_reasons)
    save_downtimes(downtime, join(outfolder, 'historicalDownPeriods.csv'))

    print('Saving job info')
    dur = generate_durations(group, beforedays=7, afterdays=7, randomfactor=3, choice=choice_type)
    #dur.to_csv(os.path.join(outfolder,'generated_jobInfoProd.csv'))
    
    print('Generating product related characteristics')
    dur = dur.merge(pd.read_csv(file_speed, index_col = 0), left_index=True, 
                        right_on='ProductionRequestId', how='left')\
                        .set_index('ProductionRequestId').fillna(1.0)
    energycons = generate_energy_per_production(dur)#, choice=choice_type, df_merged=df_merged)
    # GENERATE THE MEAN PRODUCT RELATED CHARACTERISTIC
    #tempmean = energycons[(energycons.loc[:, 'Product'] != 'NONE') | (energycons.loc[:, 'Product'] != 'MAINTENANCE')].mean()
    #tempmean['Product'] = 'MEAN'
    #energycons = energycons.append(tempmean, ignore_index=True)
    energycons.to_csv(join(outfolder, 'generated_jobInfoProd.csv'), index=True)
    
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
    # bool_up = (df.Type == 'RunTime')
    # bool_down = ((df.Type == 'DownTime') & (df.ReasonId.isin(reasons_relative)))
    # continue_obs = ((df.Type == 'DownTime') & (df.ReasonId.isin(reasons_absolute + reasons_not_considered + reasons_availability)))
    # stop_obs = (df.Type == 'Break')
    
    bool_up = (df['Type'] == 'RunTime') # List of all RunTimes
    bool_down = (df['Type'].isin(['DownTime', 'Break'])) & (df['ReasonId'].isin(reasons_relative)) # List of all DownTimes in calculation
    bool_ignore = (df['Type'].isin(['DownTime', 'Break'])) & (df['ReasonId'].isin(reasons_availability + reasons_absolute)) # List of all breaks to ignore
    bool_break = (df['Type'].isin(['DownTime', 'Break'])) & (df['ReasonId'].isin(reasons_break)) # List of all breaks to stop observation
    
    uptime, downtime, obs_up, obs_down = duration_run_down(list(df['Duration'] / 3600), list(bool_up), list(bool_down), 
                                                           list(bool_ignore), list(bool_break), observation=True)
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
        general_dist.set("mean", str(weib.mean_time()))
        plot_hist(uptime, obs_up, 99, weib)
        plt.title(f'Probability of failure in time [general], reasons: ' +  ', '.join([str(x) for x in reasons_relative]))
        plt.savefig(rf'./{file_used.split(".")[0]}/figures/fail_prob_{file_used.split(".")[0]}_general.pdf', dpi=2400, layout='tight')
        plt.savefig(rf'./{file_used.split(".")[0]}/figures/fail_prob_{file_used.split(".")[0]}_general.png', dpi=2400, layout='tight')
        plt.close()


    # GENERATE REPAIR TIME DEFINITION
    # Generate a lognormal distribution for the repair time
    print('Repair time')
    print(len('Repair time') * '-')

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


    minimum = pm_recommend(weib, cp, cu)
    PM = int(minimum)
    if print_all:
        print('Time between planned maintenance:', PM, 'hours = less then ', int(np.ceil(PM / 24)), 'days')
    if export_all:
        maint_time = ET.SubElement(root, 'maint_time')
        maint_time.text = str(PM)
        repair_time = ET.SubElement(root, 'repair_time')
        repair_time.text = str(logn.mean_time())
    plt.plot(minimum, total_cost_maintenance(minimum, weib, cp, cu), 'o')
    t_plot = np.linspace(1, float(minimum * 2), 50)
    total, prev, unexp = total_cost_maintenance(t_plot, weib, cp, cu, True)
    #import pdb; pdb.set_trace()
    plt.plot(t_plot, total, label='total cost')
    plt.plot(t_plot, prev, label='preventive')
    plt.plot(t_plot, unexp, label='unexpected')
    plt.legend()
    plt.ylabel('Cost per hour')
    plt.xlabel('t[hours]')
    plt.title(f'Suggested time between planned maintenance: {PM} hours\n= less then {int(np.ceil(PM / 24))} days')
    plt.ylim(bottom=-total[-1]*0.1, top=total[-1]*1.5)
    plt.savefig(join(outfolder, 'PM_recommended'))
    plt.close()


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
        bool_up = (df_select.Type == 'RunTime') # List of all RunTimes
        # List of all DownTimes in calculation
        bool_down = (df_select.Type.isin(['DownTime', 'Break'])) &\
                    (df_select.ReasonId.isin(reasons_relative)) 
        # List of all breaks to ignore
        bool_ignore = (df_select.Type.isin(['DownTime', 'Break'])) &\
                      (df_select.ReasonId.isin(reasons_availability + reasons_absolute)) 
        # List of all breaks to stop observation
        bool_break = (df_select.Type.isin(['DownTime', 'Break'])) & (df_select.ReasonId.isin(reasons_break)) 

        uptime, downtime, obs_up, obs_down = duration_run_down(list(df_select.Duration / 3600), list(bool_up), list(bool_down), 
                                                               list(bool_ignore), list(bool_break), observation=True)
        wf = WeibullFitter()

        try:
            wf.fit(uptime, obs_up)
            weib = Weibull(wf.lambda_, wf.rho_)
        except:
            print(uptime)
            print(item)
            import pdb; pdb.set_trace()
            raise
        if print_all:
            print(weib)
        if export_all:
            new_element = ET.SubElement(fail_dist, 'dist')
            new_element.set("lambda", str(wf.lambda_))
            new_element.set("rho", str(wf.rho_))
            new_element.text = item
            plot_hist(uptime, obs_up, 99, weib)
            plt.title(f'Probability of failure in time [{item}], reasons: ' +  ', '.join([str(x) for x in reasons_relative]))
            plt.savefig(f'./{file_used.split(".")[0]}/figures/fail_prob_{file_used.split(".")[0]}_{item}.pdf', dpi=2400, layout='tight')
            plt.savefig(f'./{file_used.split(".")[0]}/figures/fail_prob_{file_used.split(".")[0]}_{item}.png', dpi=2400, layout='tight')
            plt.close()
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

    ct = ConversionTable(df_task, reasons_absolute, 'ProductionRequestId', choice_type)
    # ct.generate_conversion_table()
    median_conversions = ct.return_median_conversions()
    
    num_conversions = ct.return_num_conversions()
    #mean_conversions = generate_conversion_table(df_task, reasons_absolute_conversion + reasons_absolute_cleaning, 
    #                                             'ProductionRequestId', choice_type)

    #if print_all:
    #    print(mean_conversions)
    #import pdb; pdb.set_trace()

    print('Adapting the conversion time matrix - Redefining diagonal')
    #new_mc = adapt_standard_matrix(mean_conversions)
    new_mc = median_conversions
    
    def fillna_matrix(mat):
        if np.isnan(mat.loc['NONE', 'NONE']):
            mat.loc['NONE', 'NONE'] = 0
        
        if mat.loc[:, 'NONE'].isnull().any():
            import warnings
            warnings.warn('There are null values in the NONE column')
            for i in mat.index:
                if np.isnan(mat.loc[i, 'NONE']):
                    mat.loc[i, 'NONE'] = (mat.loc[:, 'NONE']).max()
                    
        if mat.loc['NONE', :].isnull().any():
            import warnings
            warnings.warn('There are null values in the NONE row')
            for i in mat.columns:
                if np.isnan(mat.loc['NONE', i]):
                    mat.loc['NONE', i] = (mat.loc['NONE', :]).max()
        
        #assert not mat.loc[:, 'NONE'].isnull().any(), 'Null values in the column'
        #assert not mat.loc['NONE', :].isnull().any(), 'Null values in the row'
        from itertools import product
        for i, j in product(mat.index, mat.columns):
            if (i == j) and np.isnan(mat.loc[i, j]):
                warnings.warn('There are null values on the diagonal')
                mat.loc[i, j] = mat.loc[i, 'NONE'] + mat.loc['NONE', j] 
            elif (i!=j) and np.isnan(mat.loc[i, j]):
                warnings.warn('There are null values on the non-diagonal')
                mat.loc[i, j] = (mat.loc[i, 'NONE'] + mat.loc['NONE', j]) * 2
        return mat

    if print_all:
        print(new_mc)

    if export_all:
        new_mc.to_csv(splitext(output_used)[0] + '_conversions_rough.csv')
        newname = splitext(output_used)[0] + '_conversions.csv'
        # fill the nan values with another value from the data
        new_mc = fillna_matrix(new_mc)
        
        #temp = np.array(new_mc).flatten()
        #temp = temp[~np.isnan(temp)]
        #mean = np.max(temp) * 2
        #mean_export = new_mc.fillna(0)
        # export
        new_mc.to_csv(newname)
        num_conversions.to_csv(splitext(output_used)[0] + '_num_conversions.csv')
        conversion_times = ET.SubElement(files, "conversion_times")
        conversion_times.text = os.path.split(newname)[1]    

    sns.heatmap(new_mc, annot=True, fmt=".0f")
    plt.tight_layout()
    plt.savefig(splitext(output_used)[0] + '_conversions.png', dpi=2400, figsize=(6, 8))
    plt.close()
    
    sns.heatmap(num_conversions, annot=True, fmt=".0f")
    plt.tight_layout()
    plt.savefig(splitext(output_used)[0] + '_num_conversions.png', dpi=2400, figsize=(6, 8))
    plt.close()
    


    #print('Generating cleaning times between the types')
    #print('Exporting the cleaning time matrix')
    #mean_cleaning = generate_conversion_table(df_task, reasons_absolute_cleaning, 'ProductionRequestId', choice_type)

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
