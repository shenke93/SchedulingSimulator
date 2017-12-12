package shopfloor;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Operation {
	private final String name = "Operation";
	
	// Operation attributes
	private int ID;
	private int jobID;
	private Job job; // job j that this operation targets at
	private int idxSequenceInAJob; // operation sequence in a job
	private List<Integer> eligibleMachineIDs = new ArrayList<Integer>(); 


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
	
	public void setJob(Job j) {
		job = j;
	}
	
	@Override
	public String toString() {
		return "JobID: " + jobID + " OpID: " + ID;
	}
}
