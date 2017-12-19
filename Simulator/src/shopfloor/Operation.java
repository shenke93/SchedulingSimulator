package shopfloor;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;
import platform.Config;
import platform.Logger;
import platform.Utils;

public class Operation {
	private final String name = "Operation";
	
	// Operation attributes
	private int ID;
	private int jobID;

	private Job job; // job j that this operation targets at
	private int idxSequenceInAJob; // operation sequence in a job
	private List<Integer> eligibleMachineIDs = new ArrayList<Integer>(); 

	// Decision variable
	private Machine machine = null;	//machine i
	private LinkedList<LocalDateTime> startTime = new LinkedList<LocalDateTime>();
	private LinkedList<LocalDateTime> endTime = new LinkedList<LocalDateTime>();

	public Operation(int jobID, int opID, List<Integer> machineIDs) {
		this.jobID = jobID;
		this.ID = opID;
		setEligibleMachineIDs(machineIDs);
	}
	
	public Operation(Machine mach, Job job) {
		machine = mach;
		this.job = job;
	}
	
	private void setEligibleMachineIDs(List<Integer> machineIDs) {
		eligibleMachineIDs.addAll(machineIDs);
		
		//Machine IDs are stored in an ascending order
		Collections.sort(eligibleMachineIDs);
	}
	
	public List<Integer> getEligibleMachineIDs() {
		return eligibleMachineIDs;
	}

	public void setMachine(Machine m) {
		this.machine = m;
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
	
	public void setProcessingMachine(Machine m) {
		machine = m;
	}
	
	public int getProcessingMachineID() {
		return machine.getID();
	}
	
	public Machine getProcessingMachine() {
		return machine;
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
	
	public LocalDateTime getFirstStartTime() {
		return startTime.getFirst();
	}
	
	public LocalDateTime getLastEndTime() {
		return endTime.getLast();
	}
	
	
	public void setEndTime(LinkedList<LocalDateTime> endTime) {
		this.endTime = endTime;
	}

	public void setStartEndTimeForward(LocalDateTime firstStartTime) {
		setFirstStartTime(firstStartTime);
		setRestStartEndTimeForward();
	}
	
	private void setFirstStartTime(LocalDateTime st) {
		startTime.removeAll(startTime);
		if (Utils.isOnWeekendIncludingPowerOnOff(st)) {
			st = Utils.shiftToNextWorkingWeek(st);
		}
		startTime.add(st);
	}
	
	private void setRestStartEndTimeForward() {
		Logger.printSimulationInfo(name + (jobID+1) + (ID+1), "setRestStartEndTimeForward() of operation" + 
						+ (machine.getID()+1) + (job.getID()+1) + (ID+1) + idxSequenceInAJob);
//		System.out.println("Job quantity: " + job.getQuantity());
//		System.out.print("Production cycle of machine" + machine.getID() + ": ");
//		System.out.println(machine.getCycleProduction(this));
		long duration2BeAccommodated = job.getQuantity() * machine.getCycleProduction(job.getID(), ID);
		if (Config.workOnWeekend) {
			setFirstEndTime(startTime.getFirst().plusSeconds(duration2BeAccommodated));
		}
		else {
			//lastSecOfRelative1stWeek: relative to the first start time of current operation
			LocalDateTime lastSecOfRelative1stWeek = Utils.getEndOfSameWeek(startTime.getFirst());
			long freeDurationOfRelative1stWeek = 
					ChronoUnit.SECONDS.between(startTime.getFirst(), lastSecOfRelative1stWeek);
			if (freeDurationOfRelative1stWeek >= duration2BeAccommodated) {
				//Current operation does not have to be split
				setFirstEndTime(startTime.getFirst().plusSeconds(duration2BeAccommodated));
			}
			else {
				//Split current operation by the feasible number of workpieces in each sub-operation
				int prodCycle = machine.getCycleProduction(job.getID(), ID);
				int subQuantity = (int) Math.floor(freeDurationOfRelative1stWeek / prodCycle);
				setFirstEndTime(startTime.getFirst().plusSeconds(subQuantity * prodCycle));
				addStartTimeToTail(Utils.getStartOfNextWeek(lastSecOfRelative1stWeek));
				int restQuantity = job.getQuantity() - subQuantity;
				while (restQuantity * prodCycle > Config.freeDurationOfNormalWeek) {
					subQuantity = (int) Math.floor(Config.freeDurationOfNormalWeek / prodCycle);
					addEndTimeToTail(startTime.getLast().plusSeconds(subQuantity * prodCycle));
					addStartTimeToTail(startTime.getLast().plusWeeks(1));
					restQuantity -= subQuantity;
				}
				addEndTimeToTail(startTime.getLast().plusSeconds(restQuantity * prodCycle));
			}
		}
	}
	
	public void setFirstEndTime(LocalDateTime et) {
		endTime.removeAll(endTime);
		endTime.add(et);
	}
	
	public void addStartTimeToTail(LocalDateTime st) {
		startTime.add(st);
	}
	
	public void addEndTimeToTail(LocalDateTime et) {
		endTime.add(et);
	}
	
	public int getSequenceIndexInAJob () {
		return idxSequenceInAJob;
	}
	
	public void setSequenceIndexInAJob (int idx) {
		idxSequenceInAJob = idx;
	}
	
	public boolean isLastInAJob() {
		if (idxSequenceInAJob == job.getRequiredOperations().size() - 1) {
			return true;
		}
		return false;
	}
	
	
	
	
}
