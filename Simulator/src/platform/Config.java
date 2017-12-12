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
import shopfloor.Operation;

public class Config {
	private static final String name = "Config";
	
	/**
	 * Time related parameters
	 */
	public static boolean workOnWeekend = false;	//True: production can be scheduled at weekends. False: no production scheduled at weekends.	
	public static final int startHourOfWeek = 6;	//start/end hour (of 24h) within a week
	public static final LocalDateTime startTimeSchedule = LocalDateTime.of(2016, 11, 14, startHourOfWeek, 0, 0);
	public static final LocalDateTime dueTime = workOnWeekend? 
			LocalDateTime.of(2016, 11, 28, startHourOfWeek - 1, 59, 59):LocalDateTime.of(2016, 11, 26, startHourOfWeek - 1, 59, 59);
	
	/**
	 * Equipment related parameters
	 */
	public static LinkedList<Machine> listMachines = new LinkedList<Machine>();
	public static int numMachines;
	
	/**
	 * Production planning related parameters
	 */
	private static final String shopFloorConfiguration = "single machine";

	public static List<Integer> inputJobID = new LinkedList<Integer>();
	public static LinkedList<Job> listJobs = new LinkedList<Job>();
	public static List<Operation> listOperations = new LinkedList<Operation>();
	public static int numJobs;
	
	public static final int[] productType = new int[]{0, 1}; //{0, 1, 2, 3, 4, 5, 6, 7, 8, 9};	//{0, 1, 2, 3}
	public static final int numProdType = productType.length;


	public static String instanceName = "Example";
	public static String instanceFile = "C:\\Users\\admin_kshen\\Desktop\\Data\\Instances.xls";
	
	/**
	 * Get experiment instances from an excel file.
	 */
	public static void getInstance() {
		if (shopFloorConfiguration.equalsIgnoreCase("single machine")) {
			getOperations();
			getJobs();
			getMachines();
		}
	}
	
	/**
	 * Create operations based on the given instance.
	 * 
	 */
	private static void getOperations() {
		listOperations.clear();
		String xlsFile = instanceFile;
		try {
			HSSFWorkbook wb = Config.readFile(xlsFile);
			HSSFSheet sheet = wb.getSheet(instanceName);
			int startRow = 1;
			int startColumn = 2;
			int endRow = sheet.getPhysicalNumberOfRows();
			int operationID, jobID;
			for (int rowIdx = startRow; rowIdx < endRow; ++rowIdx) {
				List<Integer> machineIDs = new LinkedList<Integer>();
				HSSFRow row = sheet.getRow(rowIdx);
				jobID = (int) row.getCell(0).getNumericCellValue() - 1;
				operationID = (int) row.getCell(1).getNumericCellValue() - 1;
				for (int column = startColumn; column < row.getLastCellNum(); column++) {
					if ((int) row.getCell(column).getNumericCellValue() > 0) {
						machineIDs.add(column - startColumn);
					}
				}
				listOperations.add(new Operation(jobID, operationID, machineIDs));
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Create jobs based on the given instance.
	 * 
	 * 
	 */
	private static void getJobs() {
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
			job.setReleaseTime(Config.startTimeSchedule);
			job.setDueTime(Config.dueTime);
			Iterator<Operation> iter = listOperations.iterator();
			// System.out.println("listOperations.size = " + listOperations.size());

			// Set job attributes
			for (int rowIdx = startRow; rowIdx < endRow; rowIdx++) {
				HSSFRow row = sheet.getRow(rowIdx);
				// System.out.println("rowIdx: "+row);
				// New row compared to the previous row
				if (jobID < (int) row.getCell(0).getNumericCellValue() - 1) {
					// UDUT System.out.println(job.toString());			
					// System.out.println(Arrays.toString(job.getRequiredOperations().toArray()));
					listJobs.add(job);
					operationID = 0;
					++jobID;
					Config.inputJobID.add(jobID);
					job = new Job(jobID);
					job.setReleaseTime(Config.startTimeSchedule);
					job.setDueTime(Config.dueTime);
				}
				else {
					++operationID;
					// System.out.println("Operations: "+operationID);
				}
				job.addRequiredOperation(iter.next());
			}
			// UDUT System.out.println(job.toString());
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
	private static void getMachines() {
		String xlsFile = instanceFile;
		try {
			HSSFWorkbook wb = Config.readFile(xlsFile);
			HSSFSheet sheetProcessingTime = wb.getSheet(instanceName + "ProcessingTime");
			HSSFSheet sheetProductionPower = wb.getSheet(instanceName + "ProductionPower");
			int startRow = 1;
			int endRow = sheetProcessingTime.getPhysicalNumberOfRows();
			
			// Get all machines in the instance
			Config.numMachines = sheetProcessingTime.getRow(1).getLastCellNum() - 2;
			for (int idx = 0; idx < Config.numMachines; ++idx) {
				listMachines.add(new Machine(idx));
			}
			
			// Set production power profile (cycle time and power) of each machine
			int processingTime;
			double productionPower;
			int jobID = 0;
			int operationID = 0;
			int startIdxMachine = 2;
			HSSFRow rowProcessingTime, rowProductionPower;
			for (int rowIdx = startRow; rowIdx < endRow; rowIdx++) {
				rowProcessingTime = sheetProcessingTime.getRow(rowIdx);
				rowProductionPower = sheetProductionPower.getRow(rowIdx);
				if (jobID != (int) rowProcessingTime.getCell(0).getNumericCellValue() - 1) {
					++jobID;
					operationID = 0;
				}
				
				for (int idxMachine = startIdxMachine; idxMachine < rowProcessingTime.getLastCellNum(); ++idxMachine) {
					processingTime = (int) rowProcessingTime.getCell(idxMachine).getNumericCellValue();
					productionPower = (double) rowProductionPower.getCell(idxMachine).getNumericCellValue();
					
					if (processingTime > 0) {
						listMachines.get(idxMachine - startIdxMachine).setProductionPowerProfile(jobID, operationID, processingTime, productionPower);
					}
				}
				++operationID;
			}
			// UDUT System.out.print(Arrays.toString(listMachines.toArray()));
			
			// Set job and operation sequence-dependent setup times for each machine
			// TODO
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
