package shopfloor;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;

public class Job {
	
	// Job information not related with scheduling (init with constructor)
	private int ID;
	public String name;
	
	// Job attributes related with scheduling
//	private int quantity;
//	private int productType; 
	private LocalDateTime releaseTime; // In our case, releaseTime is time zero
	private LocalDateTime dueTime;	// In our case, dueTime is the completion time of jobs in the record
//	private int weight;
	private int processingTime; // In our case, processingTime is the difference of ActualEndTime and ActualStartTime in the record
	
	// Variables related to operations
//	private LinkedList<Operation> requiredOperations = new LinkedList<Operation>();
//	private Iterator<Operation> iterOperation;

	// Assistance variables 
//	private Operation currentOperation;
//	private long duration, totalDuation;
//	private Machine currentMachine;
	
	
	public Job(int ID, String name) {
		this.ID = ID;
		this.name = name;
	}
	
	public int getProcessingTime() {
		return processingTime;
	}
	
	public void setProcessingTime(int time) {
		this.processingTime = time;
	}
	
	public LocalDateTime getReleaseTime() {
		return releaseTime;
	}
	
	public void setReleaseTime(LocalDateTime releaseTime) {
		this.releaseTime = releaseTime;
	}

	public LocalDateTime getDueTime() {
		return dueTime;
	}
	
	public void setDueTime(LocalDateTime dueTime) {
		this.dueTime = dueTime;
	}
	
	/**
	 * Add {@code op} to the {@code requiredOperations} list and 
	 * link {@code op} to this job.
	 * @param op
	 */
//	public void addRequiredOperation(Operation op) {
//			op.setJob(this);
//			requiredOperations.add(op);		
//	}


	public int getID() {
		return ID;
	}


//	public LinkedList<Operation> getRequiredOperations() {
//		return requiredOperations;
//	}

//	@Override
//	public String toString() {
//		return "JobID: " + (id+1) + " Quantity " + quantity + " ReleaseTime: " 
//				+ "RequiredOperations: " + Arrays.toString(requiredOperations.toArray())
//				+ " ReleaseTime: " + releaseTime + " DueTime: " + dueTime;
//	}
	
	/**
	 * Get a copy of {@code Job} with {@code id, dueTime and releaseTime}.
	 * @return
	 */
//	public Job getInitializedCopy() {
//		Job job = new Job(this.ID, this.name);
//		job.setDueTime(this.dueTime);
//		job.setReleaseTime(this.releaseTime);
////		job.setQuantity(this.quantity);
//		return job;
//	}
	
//	public int getQuantity() {
//		return quantity;
//	}
	
//	public int getProductType() {
//		return productType;
//	}
	
//	public void setQuantity(int q) {
//		quantity = q;
//	}
	
//	public void setCurrentMachine(Machine m) {
//		currentMachine = m;
//	}
	
	// For flexible-job-shop
//	public void setCurrentOperation(Operation op) {
//		currentOperation = op;
//	}
	
	/**
	 * Calculate Processing time of a work piece (operation with quantity).
	 * Update current machine time.
	 */
//	public void setDuration() {
//		duration = quantity * currentMachine.getCycleProduction(this.id, currentOperation.getID());
//		Logger.printSimulationInfo(currentMachine.getCurrentTime(), this.name, "Duration of current workpieces: " 
//				+ "Job " + (id+1) + " Operation " + (currentOperation.getID()+1) + ": " 
//				+ Machine.calculateDay(duration) + "d " + Machine.calculateHour(duration) + "h " + Machine.calculateMin(duration) 
//				+ "m " + Machine.calculateSec(duration) + "s");
//		currentMachine.setCurrentTime(currentMachine.getCurrentTime().plusSeconds(duration));
//	}

//	public long getDuration() {
//		return duration;
//	}
	
}
