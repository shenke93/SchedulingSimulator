System requirements: 
	python 3.6.4 or higher
	IPython notebook (For customized visualization)
	Required 3rd-party modules: numpy v1.14.1,
								pandas v0.22.0, (For visualization of results)
								matplotlib v3.0.3 (For visualization of results)

How to use:
	Double click or execute from the command line window: execute.exe
								
Following data files are required as the input of the scheduler:
Attributes marked by * are not available before the production, only used in the demo.

-original_folder (original_data)
	Information about the folder which contains all the following files

-failure_info_path (productionfile)
	Folder containing all the failure info about the jobs
	
-energy_price_file (generated_hourly_energy_price.csv)
	Information of energy price.
	Format: Date(Date), timestamp of an hour. 
			Euro(Float), hourly energy price (euro / MWh).
			
-historical_down_periods_file (*historicalDownPeriods.csv)
	Information of down periods in historical records.
	Format: ID(Int), ID of a downtime period.
			StartDateUTC(Date), start timestamp of a downtime period.
			EndDateUTC(Date), end timestamp of a downtime period.
	
-job_info_file (generated_jobInfoProd.csv)
	Information of jobs.
    Format: ID(Int), ID of a job.
			[*Duration(Float), processing time of a job.
			or
			[*Quantity, quantity of the job production
			[*TargetProductionRate, target production rate when working
			Product(Category), product type of a job.
			*Type, type of the production
			Releasedate, date after which the production should be planned
			Duedate, date before which the production should be planned
			*Start(Date), start timestamp of a job.
			*End(Date), end timestamp of a job.
			*UnitPrice, unit price of the product
			*Power, relative power consumption of the job
			*Weight, used when the product is produced before the releasedate 
			         or after the due date

- failure_xml_file (outputfile.xml)
	Xml file with information about the job distributions,
	maintenance times, and so on.	

	
	
After executing the scheduler, the following intermediate files are generated to help to visualize the result.
They are put inside the folder 'Scheduling/Results_yyyymmdd_hhmm' to keep different runs separate.

if export = True
-iterations_results.csv
	Contains a csv file with the results of each iteration
-evolution.png
	Is a png file with the visualisation of each iteration
-output_init (original_jobs.csv)
	Contains a csv file with the original order of the jobs
	- ProductionRequestId
	- Uptime
	- Totaltime
	- Quantity if available
	- Start
	- End
	- Product
	- Type
	- Releasedate
	- Duedate
	- TargetProductionRate
	- UnitPrice
	- Power
	- Weight
	
-output_final (final_jobs.csv)
	Contains a csv file with the final order of the jobs
-output_results_init (results_orig.csv)
	Contains a csv file with an overview of all calculated costs for the initial schedule
-output_results_final (results_final.csv)
	Contains a csv file with an overview of all calculated costs for the final result

if export_paper = True
	(make some extra files in pdf format)
	
if export_indeff = True
-output_init_small (original_jobs_small.csv)
	Makes a simplified file with the job numbers and start and end date for the original file
-output_final_small (final_jobs_small.csv)
	Makes a simplified file with the job numbers and start and end date for the final file
	

visualize.ipynb: Ipython notebook for customized visualization. 
