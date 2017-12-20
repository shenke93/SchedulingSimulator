package shopfloor;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;
import machine.State;
import platform.Config;
import platform.KeyJobOperation;
import platform.Logger;
import platform.Utils;

/**
 * This class simulates the actual shop floor. Input data are received from the Config class. 
 * 
 *
 */
public class ShopFloor {
	
	private final String name = "ShopFloor";
	
	// Input info
	private LinkedList<Machine> listMachines = new LinkedList<Machine>();
	private LinkedList<Operation> listOperations = new LinkedList<Operation>();	
	private LinkedList<Job> listJobs = new LinkedList<Job>();
	
	// Variables used in production simulation
	private LocalDateTime currentTime = Config.startTimeSchedule;	//it keeps up with the latest time of all machines
	private LinkedList<Job> listExedJobs = new LinkedList<Job>();	//a job is considered executed once its last operation is completed
	
	private int[] productQuantity = new int[Config.numProdType];	//accumulated amount of produced products (whose last operation is completed)
	private int TotalProductQuantity; 	//the sum of all types of products

	// TODO (Remove) temporary variables for simulation
	LinkedList<LocalDateTime> timeList = new LinkedList<LocalDateTime>();

	public ShopFloor(String config) {
		if (config.equalsIgnoreCase("single machine")) {
			createOperations();
			createJobs();
			createMachines();
		} else {
			System.err.println("ShopFloor type unrecognized!");
		}
	}
	
	/**
	 * Initialize operations from production planning for the shopfloor.
	 */
	private void createOperations() {
		listOperations.clear();
		for (Operation op : Config.listOperations) {
			listOperations.add(op.getInitializedCopy());
			// System.out.println("create operation");
		}
	}
	
	/**
	 * Initialize operations from production planning for the shopfloor.
	 */
	private void createJobs() {
		listJobs.clear();
		for (Job job : Config.listJobs) {
			listJobs.add(job.getInitializedCopy());
			if (listJobs.getLast().getQuantity() <= 0) {
				System.err.println("[" + name + "] Job" + listJobs.getLast().getID() + 
						" has quantity " + listJobs.getLast().getQuantity());
			}
		}
	}
	
	/**
	 * Initialize machines from production planning for the shopfloor.
	 */
	private void createMachines() {
		listMachines.clear();
		for (Machine m : Config.listMachines) {
			listMachines.add(m.getInitializedCopy());
		}
	}
	
	/**
	 * @return makespan for processing all jobs (seconds).
	 */
	public long getMakespan() {
		return ChronoUnit.SECONDS.between(Config.startTimeSchedule, currentTime);
	}
	
	public void terminateSimulation() {
		for (Machine m : listMachines) {
			m.terminateSimulation();
		}
	}
	
	public LinkedList<Machine>	getMachines() {
		return listMachines;
	}
	
	public LinkedList<Job> getJobs() {
		return listJobs;
	}
	
	public void performJobs() {
		LocalDateTime startTime;
		long duration;
		for (Machine m : listMachines) {
			m.setCurrentTime(currentTime);
			// TODO (Remove) Now for simulation, Machine.listOperations is the same of Config.listOperations
			m.setListOperations(listOperations);
			
			// UDUT
//			System.out.println(Arrays.toString(m.getListOperations().toArray()));
			
			if (Config.history) {
				System.out.println();
			}
			String info = "The operations to be performed on " + m.getName() + ": ";
			for (Operation operation : m.getListOperations()) {
				info += "JobID " + (operation.getJobID()+1) + " OperationID " + (operation.getID()+1) + ", ";
//				System.out.println("op");
			}
			Logger.printSimulationInfo(m.getCurrentTime(), name, info);
			
			for (Operation op : m.getListOperations()) {
				
				// TODO (Remove) Now for simulation, give values to op.startTime 
//				System.out.println(op.toString());
//				System.out.println(op.getJobID());
//				System.out.println(m.getCycleProduction(op.getJobID(), op.getID()));
				timeList.clear();
				timeList.add(currentTime);
				op.setStartTime(timeList);
				
//				System.out.println("TimeListSize:" + timeList.size());
				
				// TODO (Remove) Now for simulation, assign job to op, assign machine to op
				op.setJob(listJobs.get(op.getJobID()));
				op.setMachine(m);
//				System.out.println(op.getJob().getID());
				
				startTime = op.getStartTime().getFirst();
				
				// TODO Consider buffer
				
				// Pre-processing idling and setup
				if (m.getExecutedOperations().size() == 0) {
					duration = ChronoUnit.SECONDS.between(Config.startTimeSchedule, startTime.minusSeconds(Config.durationPowerOn));
					if (duration > 0) {
						// UDUT
						System.out.println(m.getName() + " PowerOnDuration: " + Machine.calculateHour(duration) + "h " + Machine.calculateMin(duration) 
						+ "m " + Machine.calculateSec(duration) + "s" + "\n");
						m.stayOff(duration);
					}
					m.powerOn();
				}
				else {
					// TODO Consider changeover
					Operation previousOp = m.getExecutedOperations().getLast();
					Changeover changeover = new Changeover(m.getSetupTime(
							new KeyJobOperation(previousOp.getJob().getID(), previousOp.getID()),
							new KeyJobOperation(op.getJob().getID(), op.getID())));
					changeover.setStartEndTimeBackward(op.getFirstStartTime());
					m.setChangeover(changeover);
					
					duration = ChronoUnit.SECONDS.between(previousOp.getLastEndTime(), 
							changeover.getFirstStartTime());
					if (duration >= Config.durationPowerOnOff) {
						Logger.printSimulationInfo(m.getCurrentTime(), name, "Machine is now powered off " + 
								"and will stay off for " + Utils.getDayHourMinSec(duration - Config.durationPowerOnOff));
						m.powerOff();
						m.stayOff(duration - Config.durationPowerOnOff);
						m.powerOn();
					}
					else if (duration > 0) {
						Logger.printSimulationInfo(m.getCurrentTime(), name, "Machine will stay idle for " + 
								Utils.getDayHourMinSec(duration));
						m.stayIdle(duration);
					}
					
					Logger.printSimulationInfo(m.getCurrentTime(), name, "Machine" + (m.getID()+1) + " starts to do a changeover");
					Logger.printSimulationInfo(m.getCurrentTime(), name, "Duration of this changeover is " + 
												Utils.getDayHourMinSec(m.getChangeover().getDuration()));
					
					if (changeover.isSplit()) {
						m.doSplitChangeovers();
						Logger.printSimulationInfo(m.getCurrentTime(), name, "Changeover is split.");
					}
					else {
						m.doACompleteChangeover();
						Logger.printSimulationInfo(m.getCurrentTime(), name, "Changeover is not split.");
					}
					m.addAChangeover(changeover);		
				}
				
				// Perform current operation of current job
				Logger.printSimulationInfo(m.getCurrentTime(), name, "Current Operation " + (op.getID()+1) + " of Job " + (op.getJobID()+1) + " starts...");
				m.performAnOperation(op);
				Logger.printSimulationInfo(m.getCurrentTime(), name, "Current Operation " + (op.getID()+1) + " of Job " + (op.getJobID()+1) + " ends...");
				System.out.println();
//				System.out.println(m.getCycleProduction(op.getJobID(), op.getID()));
				
				// TODO (Remove) for simulation, give endtime to job
				if (m.getCurrentTime().isAfter(currentTime)) {
					currentTime = m.getCurrentTime();
				}
//				System.out.println(currentTime);
				
				timeList.clear();
				timeList.add(currentTime);
				op.setEndTime(timeList);
			}
			
			if (m.getExecutedOperations().size() > 0) {
				m.powerOff();
			}
			
			if (m.getCurrentTime().isAfter(currentTime)) {
				currentTime = m.getCurrentTime();
			}
			
//			System.out.println(currentTime);
		}
		
		for (Job job: listJobs) {
			listExedJobs.add(job);
			productQuantity[job.getProductType()] = job.getQuantity();	
		}
		
		aggregateInfo();
		// TODO Consider energy
		
		// TODO Objective calculation
	}
	
	private void aggregateInfo() {
		// Product
		TotalProductQuantity = 0;
		for (int type = 0; type < Config.numProdType; ++type) {
			TotalProductQuantity += productQuantity[type];
		}
	}
	
}
