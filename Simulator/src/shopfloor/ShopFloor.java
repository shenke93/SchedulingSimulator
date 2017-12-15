package shopfloor;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;
import machine.State;
import platform.Config;

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

	public ShopFloor(String config) {
		createOperations();
		createJobs();
		createMachines();
	}
	
	/**
	 * Initialize operations from production planning for the shopfloor.
	 */
	private void createOperations() {
		listOperations.clear();
		for (Operation op : Config.listOperations) {
			listOperations.add(op.getInitializedCopy());
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
		// TODO Question: Def of makespan
		return ChronoUnit.SECONDS.between(Config.startTimeSchedule, currentTime);
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
			for (Operation op : m.getOperations()) {
				startTime = op.getStartTime().getFirst();
				
				// TODO Consider buffer
				
				// Pre-processing idling and setup
				if (m.getExecutedOperations().size() == 0) {
					duration = ChronoUnit.SECONDS.between(Config.startTimeSchedule, startTime.minusSeconds(Config.durationPowerOn));
					if (duration > 0) {
						m.stayOff(duration);
					}
					m.powerOn();
				}
				else {
					// TODO Consider changeover
				}
				
				// Perform current operation of current job
				System.out.println(m.getCurrentTime() + "Current operation" + op.getID() + " starts...");
				m.performAnOperation(op);
				System.out.println(m.getCurrentTime() + "Current operation" + op.getID() + " ends...");
			}
			
			// TODO: Question: why machine power off here
			if (m.getExecutedOperations().size() > 0) {
				m.powerOff();
			}
			// System.out.println(currentTime);
			if (m.getCurrentTime().isAfter(currentTime)) {
				currentTime = m.getCurrentTime();
			}
			
			for (Job job: listJobs) {
				listExedJobs.add(job);
				productQuantity[job.getProductType()] = job.getQuantity();	
			}
			
			aggregateInfo();
			// TODO Consider energy
			
		}
	}
	
	private void aggregateInfo() {
		// Product
		TotalProductQuantity = 0;
		for (int type = 0; type < Config.numProdType; ++type) {
			TotalProductQuantity += productQuantity[type];
		}
	}
	
}
