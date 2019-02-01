System requirements: 
	python 3.6.4 or higher
	IPython notebook (For customized visualization)
	Required 3rd-party modules: numpy v1.14.1,
								pandas v0.22.0, (For visualization of results)
								matplotlib v3.0.3 (For visualization of results)

How to use:
	Double click or execute from the command line window: execution.bat
								
Following data files are required as the input of the scheduler:
Attributes marked by * are not available before the production, only used in the demo.

-jobInfo.csv
	Information of jobs.
    Format: ID(Int), ID of a job. 
			*Duration(Float), processing time of a job.
			*Start(Date), start timestamp of a job.
			*End(Date), end timestamp of a job.
			Quantity(Float), objective quantity of a job. 
			Product(Category), product type of a job.
			
-energyPrice.csv
	Information of energy price.
	Format: Date(Date), timestamp of an hour. 
			Euro(Float), hourly energy price (euro / MWh).
			
-productRelatedCharacteristics.csv
	Information of product related characteristics.
	Format: Product(Category), name of product type.
			UnitPrice(Float), price of raw material (euro / kg).
			Power(Float), power of job of such product (MW).
			TargetProductionRate(Float), production speed of job of such product (kg / h).

-*historicalDownPeriods.csv
	Information of down periods in historical records.
	Format: ID(Int), ID of a downtime period.
			StartDateUTC(Date), start timestamp of a downtime period.
			EndDateUTC(Date), end timestamp of a downtime period.

-hourlyFailureRate.csv
	Failure rate pattern derived from the failure model.
	Format: Influence(Float), failure rate (harzard rate) of each hour.
	
	
After executing the scheduler, three intermediate files are generated to help to visualize the result.

-originalRecords.csv
	Execution informatino of the original schedule.
	Format: ID(Int), ID of a job.
			Start(Date), start time stamp of a job.
			End(Date), end time stamp of a job.
			Duration(Float), execution duration of a job.
			
-executionRecords.csv
	Execution informatino of the candidate schedule proposed by the scheduler. 
	This file can be used as a guideline for production.
	Format: ID(Int), ID of a job.
			Start(Date), start time stamp of a job.
			End(Date), end time stamp of a job.
			Duration(Float), execution duration of a job.
			
-downDurationRecords.csv
	Information of down periods during execution of jobs.
	Format: ID(Int), ID of a downtime period.
			Start(Date), start timestamp of a downtime period.
			End(Date), end timestamp of a downtime period.

visualize.ipynb: Ipython notebook for customized visualization. 
