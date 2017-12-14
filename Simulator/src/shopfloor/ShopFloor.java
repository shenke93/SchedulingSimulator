package shopfloor;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;
import machine.State;
import platform.Config;

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
			// TODO Conditions can be added
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
						m.keepState(Config.off, duration);
					}
					m.setState(Config.on);;
				}
				else {
					// TODO Consider changeover
				}
				
				// Perform current operation of current job
				m.performAnOperation(op);
			}
		}
	}
	
	
}
