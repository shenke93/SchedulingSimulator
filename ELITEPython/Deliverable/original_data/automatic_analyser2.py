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
import seaborn as sns
sns.set_style('white')
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

REPAIR_MULT = 1.5

assert(set(reasons_absolute_cleaning + reasons_absolute_conversion) == set(reasons_absolute)),\
    'Absolute reasons are incorrectly defined'
considered_reasons = sorted(list(set(reasons_relative + reasons_absolute + reasons_absolute_conversion
                            + reasons_absolute_cleaning + reasons_break + reasons_availability)))

print_all = True; export_all = True
turn_off_if = None # seconds # the machine can be turned off if time if larger than this
break_pauses = None # seconds # breaks will be split in these periods

# turn_off_if has to be smaller than break_pauses in order for this program to run well
if (turn_off_if is not None) and (break_pauses is not None):
    assert (turn_off_if < break_pauses), 'Variable break_pauses should be larger then turn_off_if'

sys.path.append(os.path.split(sys.path[0])[0])

from probdist import duration_run_down, Weibull, Lognormal
from lifelines import WeibullFitter, LogNormalFitter
from functions_auto_analyser import add_column_type, add_breaks, group_productions, remove_breaks, construct_downtimes,\
                                    save_downtimes, generate_durations, generate_energy_per_production,\
                                    construct_energy_2tarifs, adapt_standard_matrix, ConversionTable, plot_hist,\
                                    heatmap, annotate_heatmap

print(__doc__)

curdir = os.path.split(os.path.abspath(sys.argv[0]))[0]
os.chdir(curdir)

# per choice: (inputfile, target production rate per type, type name)
# outputfolder determined by name of inputfile
choices = {'production': ('productionfile.csv', 'prod_speed.csv', 'PastaType', 'productionfile', 7*24),
           'packaging': ('packagingfile_old.csv', 'pack_speed.csv', 'BigPack-simple','packagingfile_old', 7*24),
           #'production_pertype': ('productionfile.csv', 'prod_speed.csv', 'ArticleCode', 'productionfile_pertype', 7*24),
           }

for choice in choices:
    print(f"Executing for: {choice}")
    file_used, file_speed, choice_type, outfolder, maint_t = choices[choice]
    try:
        df = pd.read_csv(file_used, parse_dates=['StartDateUTC', 'EndDateUTC'])
        df = df.sort_values('StartDateUTC')
        list_reasons = sorted(list(df['ReasonId'].unique()))
    except:
        raise NameError('{} not found in this folder ({})'.format(file_used, os.curdir))

    # Make the output folder if it doesn't exist yet
    #outfolder = splitext(file_used)[0]
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
    

    #print(df.head())
    # Add the column type column to the dataset
    #if choice_type in ['BigPack', 'Marque', 'PastaType', 'BigPack-simple']:
    #    df = add_column_type(df, choice=choice_type)
    #elif choice_type == 'ArticleCode':
    #    pass

    # NORMALISE THE BREAKS
    print('Normalising breaks to have a time of '+ str(break_pauses))
    df_task = df.copy()
    # Set the ReasonId to 100 if there is RunTime
    #df_task['ReasonId'] = np.where(df_task['Type'] == 'RunTime', 100, df_task['ReasonId'])
    df_task = df_task[['ProductionRequestId', 'StartDateUTC' , 'EndDateUTC', 
                       'Duration', 'ReasonId', 'ArticleName', 'ArticleCode', 
                       'Quantity', 'Type']]
    # remove the breaks
    df_task = df_task[df_task['ArticleName'] != 'NONE']
    # add the breaks again in a controlled way
    df_task = add_breaks(df_task, maxtime=break_pauses)
    
    # ADD TYPE COLUMN
    print('Adding type column with type = ' + choice_type)
    if choice_type in ['BigPack', 'Marque', 'PastaType', 'BigPack-simple']:
        df_task = add_column_type(df_task, choice=choice_type)
    elif choice_type == 'ArticleCode':
        pass
    df_task.head()

    ct = ConversionTable(df_task, reasons_absolute, 'ProductionRequestId', choice_type)
    # ct.generate_conversion_table()
    median_conversions = ct.return_median_conversions()
    
    num_conversions = ct.return_num_conversions()
    #mean_conversions = generate_conversion_table(df_task, reasons_absolute_conversion + reasons_absolute_cleaning, 
    #                                             'ProductionRequestId', choice_type)

    var_conversions = ct.return_variance_conversions()
    #if print_all:
    #    print(mean_conversions)
    
    std_conversions = ct.return_std_conversions()
    
    
    if choice == 'production':
        type1, type2 = 'HORENTJE', 'MACARONI'
    elif choice == 'packaging':
        type1, type2 = 'LARGE', 'LARGE'
    numbers = ct.return_all_conversions(type1, type2)
    
    range1 = np.random.random(size=(len(numbers), 1))
    
    plt.scatter(numbers, range1)
    plt.title(f'Scatterplot of changeover time [{type1}, {type2}]')
    plt.xlabel('Changeover time')
    plt.show()
