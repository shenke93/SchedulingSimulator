package shopfloor;

import java.time.LocalDateTime;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;

public class Job {
	public String name = "Job";
	
	// Job attributes
	private int id;
	private int quantity;
	private int productType; // attribute not initialized
	private LocalDateTime releaseTime;
	private LocalDateTime dueTime;
	private int weight;
	// private int processingTime;
	
	// Variables related to operations
	private LinkedList<Operation> requiredOperations = new LinkedList<Operation>();
	private Iterator<Operation> iterOperation;

	// Dynamic variables during the simulation
	private Operation currentOperation;
	private long duration, totalDuation;
	private Machine currentMachine;
	
	
	public Job(int id) {
		this.id = id;
	}


	public void setReleaseTime(LocalDateTime releaseTime) {
		this.releaseTime = releaseTime;
	}


	public void setDueTime(LocalDateTime dueTime) {
		this.dueTime = dueTime;
	}
	
	/**
	 * Add {@code op} to the {@code requiredOperations} list and 
	 * link {@code op} to this job.
	 * @param op
	 */
	public void addRequiredOperation(Operation op) {
		op.setJob(this);
		requiredOperations.add(op);		
	}


	public int getID() {
		return id;
	}


	public LinkedList<Operation> getRequiredOperations() {
		return requiredOperations;
	}

	@Override
	public String toString() {
		return "JobID: " + (id+1) + " Quantity " + quantity + " ReleaseTime: " + releaseTime + " DueTime: " + dueTime;
	}
	
	/**
	 * Get a copy of {@code Job} with {@code id, dueTime and releaseTime}.
	 * @return
	 */
	public Job getInitializedCopy() {
		Job job = new Job(this.id);
		job.setDueTime(this.dueTime);
		job.setReleaseTime(this.releaseTime);
		job.setQuantity(this.quantity);
		return job;
	}
	
	public int getQuantity() {
		return quantity;
	}
	
	public int getProductType() {
		return productType;
	}
	
	public void setQuantity(int q) {
		quantity = q;
	}
	
	public void setCurrentMachine(Machine m) {
		currentMachine = m;
	}
	
	// For flexible-job-shop
	public void setCurrentOperation(Operation op) {
		currentOperation = op;
	}
	
	public void setDuration() {
		duration = quantity * currentMachine.getCycleProduction(this.id, currentOperation.getID());
	}
}
