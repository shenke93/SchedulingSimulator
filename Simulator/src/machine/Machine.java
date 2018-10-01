package machine;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Hashtable;
import java.util.LinkedList;
import java.util.Map;

import platform.Config;
import platform.KeyJobOperation;
import shopfloor.Job;

public class Machine {
	// Equipment information (init with constructor)
	private int ID; // EquipmentID
	private String name; // Name
//	private State OffState;
//	private State ProductionState;
	
	// Log of simulation
//	private Logger logSimu;	

	// Time-related variables
	private LocalDateTime startTime; // zero time of machine
	private LocalDateTime currentTime; // current time of machine
	
	// Workload related variables
	private Job currentJob; // current job of machine
//	private Operation currentOperation;
	private String currentState; // current state of machine
//	private LinkedList<String> listState;
//	private LinkedList<Operation> listExedOperations = new LinkedList<Operation>();
//	private LinkedList<Job> executedJobs = new LinkedList<Job>();	// list of executed jobs

	// Production plan related attributes
//	private Map<KeyJobOperation, Integer> cycleProduction = new Hashtable<KeyJobOperation, Integer>();//processing time dependent on job, operation, and machine
//	private Map<KeyJobOperation, Double> powerProduction = new Hashtable<KeyJobOperation, Double>();//operation-dependent production power
	
	// Machine characteristics
	private int power; // power of machine (may differ in different states), unit: kw 
	
	// Assistance variables
	private long durationOff;
	
	// Decision variables
//	private LinkedList<Operation> listOperations = new LinkedList<Operation>();	//operations assigned to this machine
	private LinkedList<Job> waitingJobs = new LinkedList<Job>(); // jobs assigned to machine

	public Machine(int id) {
		ID = id;
		name = "Machine" + (ID+1);
		
//		startTime = Config.startTimeSchedule; // Should be the first time when the machine is started
		
//		OffState = new OffState(this);
//		ProductionState = new ProductionState(this);
		
//		listState = new LinkedList<String>();
		currentState = "Off"; // initial state of machine is "Off"
		
		// TODO remember to set machine start time (attribute startTime)
		// TODO remember to set machine current time (attribute currentTime)
		
//		if (Config.history) {
//			String filePath = Config.homeFolder + "\\simulationLogMachine" + (ID+1) + ".txt";
////			System.out.println(filePath);
//			logSimu = new Logger(filePath);
//		}
	}
	
	public LinkedList<Job> getWaitingJobs() {
		return waitingJobs;
	}
	
	public void setWaitingJobs(LinkedList<Job> jobs) {
		this.waitingJobs = jobs;
	}
	
	// Setters and Getters
	public String getCurrentState() {
		return currentState;
	}
	
	public void setCurrentState(String state) {
		this.currentState = state;
	
		// TODO: consider actions corresponding to current state
		setPower();
	}
	
//	public State getState(String state) {
//		if (state.equalsIgnoreCase("Off")) {
//			return OffState;
//		}
//		else if (state.equalsIgnoreCase("Production")) { 
//			return ProductionState;
//		}
//		else {
//			throw new IllegalArgumentException("[Machine] Error in input state name: " + state);
//		}
//	}
	
	/**
	 * @return machine ID
	 */
	public int getID() {
		return ID;
	}
	
	/**
	 * 
	 * @return machine name
	 */
	public String getName() {
		return name;
	}
	
//	private void setPowerProduction(Map<KeyJobOperation, Double> powerProduction) {
//		this.powerProduction = powerProduction;
//	}
	
	private void setPower() {
		if (this.currentState.equals("Off")) {
			this.power = 0;
		} else {
			this.power = 10;
		}
	}

//	private void setCycleProduction(Map<KeyJobOperation, Integer> cycleProduction) {
//		this.cycleProduction = cycleProduction;
//	}
	
//	public LinkedList<Operation> getListOperations() {
//		return listOperations;
//	}
	
	// TODO (Remove)
//	public void setListOperations(LinkedList<Operation> listOperations) {
//		for (Operation op : listOperations)	{
//			if (op.getEligibleMachineIDs().contains(this.ID)) {
//				this.listOperations.add(op);
//			}
//		}
//	}
	
//	public LinkedList<Operation> getExecutedOperations() {
//		return listExedOperations;
//	}

	public Job getCurrentJob() {
		return currentJob;
	}
	
//	public Operation getCurrentOperation() {
//		return currentOperation;
//	}
	
//	public double getPowerProduction(Job job, Operation operation) {
//		return powerProduction.get(new KeyJobOperation(job.getID(), operation.getID()));
//	}
	
//	public void addStateToList(LocalDateTime currentTime, String currentState, double power) {
//		listState.add(ChronoUnit.SECONDS.between(startTimeOfTheFirstDay, currentTime)
//				+ ", " + currentState + ", " + power);
//	}
	/**
	 * 
	 * @return current simulation time
	 */
	public LocalDateTime getCurrentTime() {
		return currentTime;
	}
	
	public void setCurrentTime(LocalDateTime time) {
		currentTime = time;
	}
	
	public LocalDateTime getStartTime() {
		return startTime;
	}
	
	public void setStartTime(LocalDateTime time) {
		startTime = time;
	}
	
	// Functional methods
	/**
	 * 
	 * @param state machine state to be initialized
	 */
//	public void initState(State state) {
//		if (this.state == null) {
//			this.state = state;
//		} else {
//			System.out.println("InitialState Wrong: State exist!");
//			System.exit(0);
//		}
//	}
	/**
	 * 
	 * @return name of machine current state
	 */
//	public String getMachineState() {
//		return state.getName();
//	}
	
//	public void setProductionPowerProfile(int jobID, int operationID, int processingTime, double power) {
//		KeyJobOperation key = new KeyJobOperation(jobID, operationID);
//		cycleProduction.put(key, processingTime);
//		powerProduction.put(key, power);
//	}
	
//	@Override
//	public String toString() {
//		StringBuilder s = new StringBuilder();
//		for (KeyJobOperation key : cycleProduction.keySet()) {
//			s.append(key + " ProcessingTime: " + cycleProduction.get(key) + "\n");
//		}
//		return "MachineID: " + (ID+1) + " Name: " + name + "\n" + s.toString();
//	}
	
	/**
	 * Get a copy of {@code Machine} with {@code ID, powerProduction and cycleProduction}.
	 * @return
	 */
//	public Machine getInitializedCopy() {
//		Machine m = new Machine(ID);
////		mach.setPowerProduction(powerProduction);
////		mach.setCycleProduction(cycleProduction);		
//		return m;
//
//	}
	
	/**
	 * Used for Off state
	 */
//	public void powerOn() {
//		System.out.println("[" + getCurrentTime() + "][" + name + "] is powered on.");
//		state.pressPowerButton(1); // 1 means on
//	}
	
//	public void powerOff() {
//		System.out.println("[" + getCurrentTime() + "][" + name + "] is powered off.");
//		state.pressPowerButton(0); // 0 means off
//	}
	
	/**
	 * Used for Off state, indicating how long the machine stay at off state
	 * @param periodOff
	 */
//	public void stayOff(long periodOff) {
//		if (state == OffState) {
//			state.doSelfTransition(periodOff);
//		}
//		else {
//			throw new IllegalArgumentException("[" + getCurrentTime() + "][Mach] Wrong state " + 
//					state.getName() + " when performing stayOff().");
//		}
//	}
	
//	public void performAnOperation(Operation op) {
//		// TODO Consider job attributes, currentMachine, currentOperation, Duration etc
//		currentJob = op.getJob();
//		currentJob.setCurrentMachine(this);
//		currentJob.setCurrentOperation(op);
//		currentJob.setDuration();
//	
//		currentOperation = op;
//		
//		// Job processing
//		Logger.printSimulationInfo(this.timeCurrent, this.name, "Quantity of current workpieces: " + "Job " +
//									(currentJob.getID()+1) + " Operation " + (op.getID()+1)+ ": " + currentJob.getQuantity());
//		
//		if (currentOperation.getStartTime().size() == 1) {
//			giveProdScheduling();
//		} else {
//			// TODO Consider subjobs
//		}
//		
//		// Updates after job processing
//		listExedJobs.add(currentJob);
//		listExedOperations.add(op);
//	}
	
	/**
	 * @param job to be performed on the machine
	 */
	public void performJob(Job job) {
		System.out.printf("Machine is performing job %d \n", job.getID());
		currentJob = job;
		currentTime.plusSeconds(job.getProcessingTime());
		System.out.printf("Job %d is finished. \n", job.getID());
	}
	
//	public void giveProdScheduling() {
////		System.out.println("giveProdScheduling");
//		if (currentJob.getQuantity() > 0) {
//			if (Config.history) {
////				System.out.println(currentJob.getQuantity());
////				System.out.println(currentJob.getID());
//				logSimu.log("[" + timeCurrent + "][Machine] New production scheduling of " + 
//							currentJob.getQuantity() + " workpieces (job" + currentJob.getID() + ") is given externally.");
//			}
//			Logger.printSimulationInfo(timeCurrent, name, "New Production scheduling of " + 
//							currentJob.getQuantity() + " workpieces (Job " + (currentJob.getID()+1) + " Operation " + (currentOperation.getID()+1) + ") is given externally.");	
//			state.setFinalDestState("Procduction");
//			state.doInterStateTransition();
//		}
//	}
	
	/**
	 * Forward the production time
	 * @param timeElapse 
	 */
	public void updateCurrentTime(long timeElapse) {
		currentTime = currentTime.plusSeconds(timeElapse);
	}
	
	/**
	 * Accumulate the working period for each state.
	 * @param state
	 * @param duration
	 */
//	public void updateStateDuration(String state, long duration) {
//		if (state.equalsIgnoreCase("Off")) {
//			durationOff += duration;
//		}
//		// TODO Consider other states
//		else {
//			throw new IllegalArgumentException("[" + getCurrentTime() + "][Machine] Error!! Can not update state duration with incorrect state name: " + state
//					+ ".");
//		}
//	}
	
	/**
	 * Get the processing time for one operation.
	 * @param jobID
	 * @param operationID
	 * @return
	 */
//	public int getCycleProduction(int jobID, int operationID) {
//		return cycleProduction.get(new KeyJobOperation(jobID, operationID));
//	}
	
	public void terminateSimulation() {
//		if (Config.history) {
//			logSimu.log("[" + getCurrentTime() + "][OFF] Simulation terminates.");
//			logSimu.output();
//			// printEnergyConsumption();
//		}
	}
	
}
