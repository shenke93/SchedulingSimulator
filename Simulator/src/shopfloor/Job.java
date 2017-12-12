package shopfloor;

import java.time.LocalDateTime;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

public class Job {
	public String name = "Job";
	
	// Job attributes
	private int id;
	private int quantity;
	private LocalDateTime releaseTime;
	private LocalDateTime dueTime;
	private int weight;
	// private int processingTime;
	
	// Variables related to operations
	private LinkedList<Operation> requiredOperations = new LinkedList<Operation>();
	private Iterator<Operation> iterOperation;

	
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


	public int getId() {
		return id;
	}


	public LinkedList<Operation> getRequiredOperations() {
		return requiredOperations;
	}

}
