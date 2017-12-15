package machine;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Hashtable;
import java.util.LinkedList;
import java.util.Map;

import platform.Config;
import platform.KeyJobOperation;
import shopfloor.Job;
import shopfloor.Operation;

public class Machine {
	// Equipment attributes
	private int ID; // EquipmentID
	private String name; // Name
	private State OffState;
	private State ProductionState;
	
	// Variables
	private LocalDateTime startTimeOfTheFirstDay;

	private LocalDateTime timeCurrent;
	private Job currentJob;
	private Operation currentOperation;

	
	private State state;
	private LinkedList<String> listState;

	private long durationOff;
	
	private LinkedList<Operation> listExedOperations = new LinkedList<Operation>();
	private LinkedList<Job> listExedJobs = new LinkedList<Job>();	//all the executed jobs

	// Production plan related attributes
	private Map<KeyJobOperation, Integer> cycleProduction = new Hashtable<KeyJobOperation, Integer>();//processing time dependent on job, operation, and machine
	private Map<KeyJobOperation, Double> powerProduction = new Hashtable<KeyJobOperation, Double>();//operation-dependent production power
	
	// Decision variables
	private LinkedList<Operation> listOperations = new LinkedList<Operation>();	//operations assigned to this machine
	
	public Machine(int id) {
		ID = id;
		name = "Machine" + (ID+1);
		
		OffState = new OffState(this);
		ProductionState = new ProductionState(this);
		
		listState = new LinkedList<String>();
		state = OffState;
		
		timeCurrent = Config.startTimeSchedule;

	}
	
	// Setters and Getters
	public State getState() {
		return state;
	}
	
	public void setState(State state) {
		this.state = state;
		
		// TODO: consider actions corresponding to current state
	}
	
	public State getState(String state) {
		if (state.equalsIgnoreCase("Off")) {
			return OffState;
		}
		else if (state.equalsIgnoreCase("Production")) { 
			return ProductionState;
		}
		else {
			throw new IllegalArgumentException("[Machine] Error in input state name: " + state);
		}
	}
	
	public int getID() {
		return ID;
	}
	public String getName() {
		return name;
	}
	
	private void setPowerProduction(Map<KeyJobOperation, Double> powerProduction) {
		this.powerProduction = powerProduction;
	}

	private void setCycleProduction(Map<KeyJobOperation, Integer> cycleProduction) {
		this.cycleProduction = cycleProduction;
	}
	
	public LinkedList<Operation> getOperations() {
		return listOperations;
	}
	
	public LinkedList<Operation> getExecutedOperations() {
		return listExedOperations;
	}

	public Job getCurrentJob() {
		return currentJob;
	}
	
	public Operation getCurrentOperation() {
		return currentOperation;
	}
	
	public double getPowerProduction(Job job, Operation operation) {
		return powerProduction.get(new KeyJobOperation(job.getID(), operation.getID()));
	}
	
	public void addStateToList(LocalDateTime currentTime, String currentState, double power) {
		listState.add(ChronoUnit.SECONDS.between(startTimeOfTheFirstDay, currentTime)
				+ ", " + currentState + ", " + power);
	}
	/**
	 * 
	 * @return current simulation time
	 */
	public LocalDateTime getCurrentTime() {
		return timeCurrent;
	}
	
	public void setCurrentTime(LocalDateTime time) {
		timeCurrent = time;
	}
	
	// Functional methods
	/**
	 * 
	 * @param state machine state to be initialized
	 */
	public void initState(State state) {
		if (this.state == null) {
			this.state = state;
		} else {
			System.out.println("InitialState Wrong: State exist!");
			System.exit(0);
		}
	}
	/**
	 * 
	 * @return name of machine current state
	 */
	public String getMachineState() {
		return state.getName();
	}
	
	public void setProductionPowerProfile(int jobID, int operationID, int processingTime, double power) {
		KeyJobOperation key = new KeyJobOperation(jobID, operationID);
		cycleProduction.put(key, processingTime);
		powerProduction.put(key, power);
	}
	
	@Override
	public String toString() {
		StringBuilder s = new StringBuilder();
		for (KeyJobOperation key : cycleProduction.keySet()) {
			s.append(key + " ProcessingTime: " + cycleProduction.get(key) + "\n");
		}
		return "MachineID: " + (ID+1) + " Name: " + name + "\n" + s.toString();
	}
	
	/**
	 * Get a copy of {@code Machine} with {@code ID, powerProduction and cycleProduction}.
	 * @return
	 */
	public Machine getInitializedCopy() {
		Machine mach = new Machine(ID);

		mach.setPowerProduction(powerProduction);
		mach.setCycleProduction(cycleProduction);
		
		return mach;

	}
	
	/**
	 * Used for Off state
	 */
	public void powerOn() {
		System.out.println("[" + getCurrentTime() + "][" + name + "] is powered on.");
		state.pressPowerButton(1); // 1 means on
	}
	
	public void powerOff() {
		System.out.println("[" + getCurrentTime() + "][" + name + "] is powered off.");
		state.pressPowerButton(0); // 0 means off
	}
	
	/**
	 * Used for Off state, indicating how long the machine stay at off state
	 * @param periodOff
	 */
	public void stayOff(long periodOff) {
		if (state == OffState) {
			state.doSelfTransition(periodOff);
		}
		else {
			throw new IllegalArgumentException("[" + getCurrentTime() + "][Mach] Wrong state " + 
					state.getName() + " when performing stayOff().");
		}
	}
	
	public static long calculateDay(long second) {
		long i = second;
		return i / 86400;	//3600s*24=86400s=1 day
	}
	
	public static long calculateHour(long second) {
		long i = second % 86400;
		return i / 3600;
	}
	
	public static long calculateMin(long second) {
		long i = second % 86400;
		i = i % 3600;
		return i / 60;		
	}
	
	public static long calculateSec(long second) {
		long i = second % 86400;
		i = i % 3600;
		return i % 60;
	}		
	
	public void performAnOperation(Operation op) {
		// TODO Consider job attributes, currentMachine, currentOperation, Duration etc
		currentJob = op.getJob();
		currentJob.setCurrentMachine(this);
		currentJob.setCurrentOperation(op);
		currentJob.setDuration();
	
		currentOperation = op;
		
		// Job processing
		if (currentOperation.getStartTime().size() == 1) {
			giveProdScheduling();
		} else {
			// TODO Consider subjobs
		}
		
		// Updates after job processing
		listExedJobs.add(currentJob);
		listExedOperations.add(op);
	}
	
	public void giveProdScheduling() {
		
	}
	
	/**
	 * Forward the production time
	 * @param timeElapse 
	 */
	public void updateCurrentTime(long timeElapse) {
		timeCurrent = timeCurrent.plusSeconds(timeElapse);
	}
	
	/**
	 * Accumulate the working period for each state.
	 * @param state
	 * @param duration
	 */
	public void updateStateDuration(String state, long duration) {
		if (state.equalsIgnoreCase("Off")) {
			durationOff += duration;
		}
		// TODO Consider other states
		else {
			throw new IllegalArgumentException("[" + getCurrentTime() + "][Machine] Error!! Can not update state duration with incorrect state name: " + state
					+ ".");
		}
	}
	
	/**
	 * Get the processing time for one operation.
	 * @param jobID
	 * @param operationID
	 * @return
	 */
	public int getCycleProduction(int jobID, int operationID) {
		return cycleProduction.get(new KeyJobOperation(jobID, operationID));
	}
}
