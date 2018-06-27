package shopfloor;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;
import platform.Config;

/**
 * This class simulates the actual shop floor. Input data are received from the Config class. 
 * 
 *
 */
public class ShopFloor {
	
	private final String name = "ShopFloor";
	
	// Shopfloor components (Machines, jobs)
	private LinkedList<Machine> listMachines = new LinkedList<Machine>();
//	private LinkedList<Operation> listOperations = new LinkedList<Operation>();	
	private LinkedList<Job> waitingJobs = new LinkedList<Job>();
	
	// Variables used in production simulation
	private LocalDateTime currentTime;	// Reference time, it keeps up with the latest time of all machines, need to be initialized with constructor
	private LinkedList<Job> executedJobs = new LinkedList<Job>();	// List of completion jobs
	
//	private int[] productQuantity = new int[Config.numProdType];	//accumulated amount of produced products (whose last operation is completed)
//	private int TotalProductQuantity; 	//the sum of all types of products

	// TODO (Remove) temporary variables for simulation
//	LinkedList<LocalDateTime> timeList = new LinkedList<LocalDateTime>();
//	HashSet<Job> setLateJobs = new HashSet<Job>();

	public ShopFloor(String config) {
		if (config.equalsIgnoreCase("single machine")) {
//			createOperations();
			createJobs();
			createMachines();
		} else {
			System.err.println("ShopFloor type unrecognized!");
		}
	}
	
	/**
	 * Initialize operations from production planning for the shopfloor.
	 */
//	private void createOperations() {
//		listOperations.clear();
//		for (Operation op : Config.listOperations) {
//			listOperations.add(op.getInitializedCopy());
//			// System.out.println("create operation");
//		}
//	}
	
	/**
	 * Initialize operations from production planning for the shopfloor.
	 */
	private void createJobs() {
		waitingJobs.clear();
		for (Job j : Config.listJobs) {
			waitingJobs.add(j);
//			if (listJobs.getLast().getQuantity() <= 0) {
//				System.err.println("[" + name + "] Job" + listJobs.getLast().getID() + 
//						" has quantity " + listJobs.getLast().getQuantity());
//			}
		}
	}
	
	/**
	 * Initialize machines from production planning for the shopfloor.
	 */
	private void createMachines() {
		listMachines.clear();
		for (Machine m : Config.listMachines) {
			listMachines.add(m);
		}
	}
	
	public void setCurrentTime(LocalDateTime time) {
		this.currentTime = time;
	}
	
	public LocalDateTime getCurrentTime() {
		return currentTime;
	}

	/**
	 * @return difference between current time and start time of schedule
	 */
	public long getTimeDifference() {
		return ChronoUnit.SECONDS.between(Config.startTimeSchedule, currentTime);
	}
	

//	public void getLateJobs() {
//		for (Job j : setLateJobs) {
//			System.out.print((j.getID()+1)+" ");
//		}
//	}
	
//	public long getWeightedTardiness() {
//		long res = 0;
//		for (Job j : setLateJobs) {
//			res += j.getDuration();
//		}
//		return res;
//	}
	
	public void terminateSimulation() {
		for (Machine m : listMachines) {
			m.terminateSimulation();
		}
	}
	
	public LinkedList<Machine>	getMachines() {
		return listMachines;
	}
	
	public LinkedList<Job> getWaitingJobs() {
		return waitingJobs;
	}
	
	public LinkedList<Job> getExecutedJobs() {
		return executedJobs;
	}
	
	// TODO Perform jobs on multiple machines may cause problems
	public void performJobs() {
		LocalDateTime startTime;
		long duration;
		for (Machine m : listMachines) {
			m.setCurrentTime(currentTime);
			// TODO (Remove) Now for simulation, Machine.listOperations is the same of Config.listOperations
//			m.setListOperations(listOperations);
			
			// UDUT
//			System.out.println(Arrays.toString(m.getListOperations().toArray()));
			
		
			String info = "Start performing jobs on " + m.getName() + ": ";
			
			// In our case, preemption of jobs are not allowed
			for (Job j : m.getWaitingJobs()) {
				m.performJob(j);
				currentTime.plusSeconds(j.getProcessingTime());
			}
			
//			for (Operation operation : m.getListOperations()) {
//				info += "JobID " + (operation.getJobID()+1) + " OperationID " + (operation.getID()+1) + ",";
////				System.out.println("op");
//			}
//			Logger.printSimulationInfo(m.getCurrentTime(), name, info);
			
//			for (Operation op : m.getListOperations()) {
				
				// TODO (Remove) Now for simulation, give values to op.startTime 
//				System.out.println(op.toString());
//				System.out.println(op.getJobID());
//				System.out.println(m.getCycleProduction(op.getJobID(), op.getID()));
//				timeList.clear();
//				timeList.add(currentTime);
//				op.setStartTime(timeList);
//				System.out.println("TimeListSize:" + timeList.size());
				
				// TODO (Remove) Now for simulation, assign job to op
//				op.setJob(listJobs.get(op.getJobID()));
//				System.out.println(op.getJob().getID());
				
//				startTime = op.getStartTime().getFirst();
				
				// TODO Consider buffer
				
				// Pre-processing idling and setup
//				if (m.getExecutedOperations().size() == 0) {
//					duration = ChronoUnit.SECONDS.between(Config.startTimeSchedule, startTime.minusSeconds(Config.durationPowerOn));
//					if (duration > 0) {
//						// UDUT
//						System.out.println("Duration: " + duration);
//						m.stayOff(duration);
//					}
//					m.powerOn();
//				}
//				else {
//					// TODO Consider changeover
//				}
				
//				m.powerOn();
				
				// Perform current operation of current job
//				Logger.printSimulationInfo(m.getCurrentTime(), name, "Current Operation " + (op.getID()+1) + " of Job " + (op.getJobID()+1) + " starts...");
//				m.performAnOperation(op);
//				Logger.printSimulationInfo(m.getCurrentTime(), name, "Current Operation " + (op.getID()+1) + " of Job " + (op.getJobID()+1) + " ends...");
//				System.out.println();
//				System.out.println(m.getCycleProduction(op.getJobID(), op.getID()));
				
//				currentTime = m.getCurrentTime();
//				System.out.println(currentTime);
				
//				if (currentTime.isAfter(Config.dueTime)) {
//					setLateJobs.add(op.getJob());
//				}
//			}
			
//			if (m.getExecutedOperations().size() > 0) {
//				m.powerOff();
//			}
			
//			if (m.getCurrentTime().isAfter(currentTime)) {
//				currentTime = m.getCurrentTime();
//			}
			
//			System.out.println(currentTime);
			
		}
		
//		for (Job job: Jobs) {
//			listExedJobs.add(job);
//			productQuantity[job.getProductType()] = job.getQuantity();	
//		}
		
		
		
//		aggregateInfo();
		// TODO Consider energy
		
		// TODO Objective calculation
	}
	
//	private void aggregateInfo() {
//		// Product
//		TotalProductQuantity = 0;
//		for (int type = 0; type < Config.numProdType; ++type) {
//			TotalProductQuantity += productQuantity[type];
//		}
//	}
	
}
