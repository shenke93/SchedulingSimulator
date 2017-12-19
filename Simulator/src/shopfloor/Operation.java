package shopfloor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;

public class Operation {
	private final String name = "Operation";
	
	// Operation attributes
	private int ID;
	private int jobID;

	private Job job; // job j that this operation targets at
	private int idxSequenceInAJob; // operation sequence in a job
	private List<Integer> eligibleMachineIDs = new ArrayList<Integer>(); 

	// Decision variable
//	private Machine machine = null;	//machine i
	private LinkedList<LocalDateTime> startTime = new LinkedList<LocalDateTime>();
	private LinkedList<LocalDateTime> endTime = new LinkedList<LocalDateTime>();

	public Operation(int jobID, int opID, List<Integer> machineIDs) {
		this.jobID = jobID;
		this.ID = opID;
		setEligibleMachineIDs(machineIDs);
	}
	
	private void setEligibleMachineIDs(List<Integer> machineIDs) {
		eligibleMachineIDs.addAll(machineIDs);
		
		//Machine IDs are stored in an ascending order
		Collections.sort(eligibleMachineIDs);
	}
	
	public List<Integer> getEligibleMachineIDs() {
		return eligibleMachineIDs;
	}

	public void setJob(Job j) {
		job = j;
	}
	
	public Job getJob() {
		return job;
	}
	
	public int getID() {
		return ID;
	}
	
	public int getJobID() {
		return jobID;
	}
	
	@Override
	public String toString() {
		return  "JobID: " + (jobID+1) + " OpID: " + (ID+1) + " EligibleMachineIDs: " + eligibleMachineIDs.toString();
	}
	
	/**
	 * Get a copy of {@code Operation} with {@code jobID, ID, eligibleMachineIDs}.
	 * @return
	 */
	public Operation getInitializedCopy() {
		return new Operation(jobID, ID, eligibleMachineIDs);
	}
	
	public LinkedList<LocalDateTime> getStartTime() {
		return startTime;
	}
	
	// TODO (Remove)
	public void setStartTime(LinkedList<LocalDateTime> startTime) {
		this.startTime = startTime;
	}
}
