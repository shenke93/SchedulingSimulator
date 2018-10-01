package platform;

import java.io.FileInputStream;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;

import machine.Machine;
import shopfloor.Job;
// import shopfloor.Operation;

/**
 * This class is used to configure the target shcedule.
 * 
 *
 */
public class Config {
	private static final String name = "Config";
	public static boolean history = true;
	
	
	/**
	 * Time related parameters
	 */
//	public static final int defaultStartupDuration = 1200; 		//sec
//	public static final int durationPowerOn = defaultStartupDuration;

//	public static boolean workOnWeekend = true;	// True: production can be scheduled at weekends. False: no production scheduled at weekends.	
//	public static final int startHourOfWeek = 6;	//start/end hour (of 24h) within a week
//	public static final int numWeeks = 2;
//	public static int numDays = 14;

	public static final LocalDateTime startTimeLine = LocalDateTime.of(2016, 11, 7, 1, 0, 0); // start time of timeline
	public static final LocalDateTime endTimeLine = LocalDateTime.of(2017, 11, 9, 23, 0, 0); // end time of timeline
	public static final LocalDateTime startTimeSchedule = LocalDateTime.of(2016, 11, 7, 8, 46, 35); // zero time of original schedule
	public static final LocalDateTime dueTimeSchedule = LocalDateTime.of(2017, 11, 9, 14, 5, 36); // due time of original schedule
	
	/**
	 * Equipment related parameters
	 */
	public static LinkedList<Machine> listMachines = new LinkedList<Machine>();
	public static int numMachines;
	
	/**
	 * Shopfloor setting parameters
	 */
	private static String shopFloorConfiguration; // This string used to mark shopfloor settings, possible values "single machine".

	public static List<Integer> inputJobID = new LinkedList<Integer>();
	public static LinkedList<Job> listJobs = new LinkedList<Job>();
	public static int numJobs;
//	public static List<Operation> listOperations = new LinkedList<Operation>();

	
//	public static final int[] productType = new int[]{0, 1}; //{0, 1, 2, 3, 4, 5, 6, 7, 8, 9};	//{0, 1, 2, 3}
//	public static final int numProdType = productType.length;

	/*
	 *	Set home folder and file directories
	 */
	public static final String homeFolder = "C:\\Users\\admin_kshen\\Desktop\\Data";
	public static String instanceName = "soubryInstance";
	public static String instanceFile = "C:\\Users\\admin_kshen\\Desktop\\Data\\Soubry.xls";
	
	public Config(String config) {
		shopFloorConfiguration =config;
	}
	/**
	 * Get experiment instances from an excel file.
	 */
	public void getInstance() {
		if (shopFloorConfiguration.equalsIgnoreCase("single machine")) {
//			getOperations();
			getJobs();
			getMachines();
		}
	}
	
	/**
	 * Create operations based on the given instance.
	 * 
	 */
//	private void getOperations() {
//		// listOperations.clear();
//		String xlsFile = instanceFile;
//		try {
//			HSSFWorkbook wb = Config.readFile(xlsFile);
//			HSSFSheet sheet = wb.getSheet(instanceName + "ProcessingTime");
//			int startRow = 1;
//			int startColumn = 2;
//			int endRow = sheet.getPhysicalNumberOfRows();
//			int operationID, jobID;
//			for (int rowIdx = startRow; rowIdx < endRow; ++rowIdx) {
//				List<Integer> machineIDs = new LinkedList<Integer>();
//				HSSFRow row = sheet.getRow(rowIdx);
//				jobID = (int) row.getCell(0).getNumericCellValue() - 1;
//				operationID = (int) row.getCell(1).getNumericCellValue() - 1;
//				for (int column = startColumn; column < row.getLastCellNum(); column++) {
//					if ((int) row.getCell(column).getNumericCellValue() > 0) {
//						machineIDs.add(column - startColumn);
//					}
//				}
//				// listOperations.add(new Operation(jobID, operationID, machineIDs));
//			}
//			// UDUT
////			System.out.println(Arrays.toString(listOperations.toArray()));
//		} catch (IOException e) {
//			e.printStackTrace();
//		}
//	}
	
	/**
	 * Create jobs (with quantities) based on the given instance.
	 * 
	 * 
	 */
	private void getJobs() {
		listJobs.clear();
		String xlsFile = instanceFile;
		try {
			HSSFWorkbook wb = Config.readFile(xlsFile);
			HSSFSheet sheet = wb.getSheet(instanceName);
			int startRow = 1;
			int endRow = sheet.getPhysicalNumberOfRows();
			
			int jobID = 0;
			@SuppressWarnings("unused")
			int operationID = 0;
			Config.inputJobID.add(jobID);
			Job job = new Job(jobID);
			job.setQuantity(1);
			job.setReleaseTime(Config.startTimeSchedule);
			job.setDueTime(Config.dueTime);
			
			// Iterator<Operation> iter = listOperations.iterator();
//			System.out.println("listOperations.size = " + listOperations.size());

			// Set job attributes
			for (int rowIdx = startRow; rowIdx < endRow; rowIdx++) {
				HSSFRow row = sheet.getRow(rowIdx);
				// System.out.println("rowIdx: "+row);
				// New row compared to the previous row
				if (jobID < (int) row.getCell(0).getNumericCellValue() - 1) {
					// UDUT 
					
					System.out.println(job.toString());			
					// System.out.println(Arrays.toString(job.getRequiredOperations().toArray()));
					listJobs.add(job);
					operationID = 0;
					++jobID;
					Config.inputJobID.add(jobID);
					job = new Job(jobID);
					job.setQuantity((int) row.getCell(2).getNumericCellValue());
					job.setReleaseTime(Config.startTimeSchedule);
					job.setDueTime(Config.dueTime);
				}
				else {
					job.setQuantity((int) row.getCell(2).getNumericCellValue());
					++operationID;
					// System.out.println("Operations: "+operationID);
				}
				// job.addRequiredOperation(iter.next());
			}
			// UDUT 
			System.out.println(job.toString());
			// System.out.println(Arrays.toString(job.getRequiredOperations().toArray()));
			listJobs.add(job);
			Config.numJobs = Config.inputJobID.size();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Create machines based on the given instance.
	 */
	private void getMachines() {
		String xlsFile = instanceFile;
		try {
			HSSFWorkbook wb = Config.readFile(xlsFile);
			HSSFSheet sheetProcessingTime = wb.getSheet(instanceName + "ProcessingTime");
			HSSFSheet sheetProductionPower = wb.getSheet(instanceName + "ProductionPower");
			int startRow = 1;
			int endRow = sheetProcessingTime.getPhysicalNumberOfRows();
			
			// Get all machines in the instance
			Config.numMachines = sheetProcessingTime.getRow(1).getLastCellNum() - 1;
			for (int idx = 0; idx < Config.numMachines; ++idx) {
				listMachines.add(new Machine(idx));
			}
			
			// Set production power profile (cycle time and power) of each machine
//			int processingTime;
//			double productionPower;
//			int jobID = 0;
//			int operationID = 0;
//			int startIdxMachine = 2;
//			HSSFRow rowProcessingTime, rowProductionPower;
//			for (int rowIdx = startRow; rowIdx < endRow; rowIdx++) {
//				rowProcessingTime = sheetProcessingTime.getRow(rowIdx);
//				rowProductionPower = sheetProductionPower.getRow(rowIdx);
//				if (jobID != (int) rowProcessingTime.getCell(0).getNumericCellValue() - 1) {
//					++jobID;
//					operationID = 0;
//				}
//				
//				for (int idxMachine = startIdxMachine; idxMachine < rowProcessingTime.getLastCellNum(); ++idxMachine) {
//					processingTime = (int) rowProcessingTime.getCell(idxMachine).getNumericCellValue();
//					productionPower = (double) rowProductionPower.getCell(idxMachine).getNumericCellValue();
//					
//					if (processingTime > 0) {
//						listMachines.get(idxMachine - startIdxMachine).setProductionPowerProfile(jobID, operationID, processingTime, productionPower);
//					}
//				}
//				++operationID;
//			}
//			// UDUT 
//			 System.out.print(Arrays.toString(listMachines.toArray()));
//			
//			// Set job and operation sequence-dependent setup times for each machine
//			// TODO
			
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * creates an {@link HSSFWorkbook} the specified OS filename.
	 * @throws IOException 
	 */
	public static HSSFWorkbook readFile(String filename) throws IOException {
		FileInputStream fis = new FileInputStream(filename);
		try {
	        return new HSSFWorkbook(fis);
	    } finally {
	        fis.close();
	    }
	}
}