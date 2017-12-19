package machine;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Hashtable;
import java.util.LinkedList;
import java.util.Map;

import platform.Config;
import platform.KeyJobOperation;
import platform.KeyJobOperationJobOperation;
import platform.Logger;
import shopfloor.Changeover;
import shopfloor.Job;
import shopfloor.Operation;

public class Machine {
	// Equipment attributes
	private int ID; // EquipmentID
	private String name; // Name
	private State OffState;
	private State ProductionState;
	
	private Logger logSimu;	

	// Variables
	private LocalDateTime startTimeOfTheFirstDay;
	private Changeover changeover;
	private int changeoverTimes;
	private boolean flagChangeover = false;	//whether the machine stays at Ready for a changeover
	private LinkedList<Changeover> listChangeovers = new LinkedList<Changeover>();
	

	private LocalDateTime timeCurrent;
	private Job currentJob;
	private Operation currentOperation;

	
	private State state;
	private LinkedList<String> listState;

	private long durationOff;
	
	private LinkedList<Operation> listExedOperations = new LinkedList<Operation>();
	private LinkedList<Job> listExedJobs = new LinkedList<Job>();	//all the executed jobs

	// Production plan related attributes
	private Map<KeyJobOperationJobOperation, Integer> setupTimes = 
			new Hashtable<KeyJobOperationJobOperation, Integer>();	//sequence-dependent setup times
	private Map<KeyJobOperation, Integer> cycleProduction = new Hashtable<KeyJobOperation, Integer>();//processing time dependent on job, operation, and machine
	private Map<KeyJobOperation, Double> powerProduction = new Hashtable<KeyJobOperation, Double>();//operation-dependent production power
	
	// Decision variables
	private LinkedList<Operation> listOperations = new LinkedList<Operation>();	//operations assigned to this machine

	public Machine(int id) {
		ID = id;
		name = "Machine" + (ID+1);
		
		startTimeOfTheFirstDay = Config.startTimeSchedule;
		
		OffState = new OffState(this);
		ProductionState = new ProductionState(this);
		
		listState = new LinkedList<String>();
		state = OffState;
		
		timeCurrent = Config.startTimeSchedule;
		
		// TODO stochastic
		// TODO subsystems
		
		if (Config.history) {
			String filePath = Config.homeFolder + "\\simulationLogMachine" + (ID+1) + ".txt";
//			System.out.println(filePath);
			logSimu = new Logger(filePath);
		}
		
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
	
	public LinkedList<Operation> getListOperations() {
		return listOperations;
	}
	
	// TODO (Remove)
	public void setListOperations(LinkedList<Operation> listOperations) {
		for (Operation op : listOperations)	{
			if (op.getEligibleMachineIDs().contains(this.ID)) {
				this.listOperations.add(op);
			}
		}
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
		mach.setSetupTimes(setupTimes);
		mach.setPowerProduction(powerProduction);
		mach.setCycleProduction(cycleProduction);
		
		return mach;

	}
	
	private void setSetupTimes(Map<KeyJobOperationJobOperation, Integer> setupTimes) {
		this.setupTimes = setupTimes;
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
		Logger.printSimulationInfo(this.timeCurrent, this.name, "Quantity of current workpieces: " + "Job " +
									(currentJob.getID()+1) + " Operation " + (op.getID()+1)+ ": " + currentJob.getQuantity());
		
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
//		System.out.println("giveProdScheduling");
		if (currentJob.getQuantity() > 0) {
			if (Config.history) {
//				System.out.println(currentJob.getQuantity());
//				System.out.println(currentJob.getID());
				logSimu.log("[" + timeCurrent + "][Machine] New production scheduling of " + 
							currentJob.getQuantity() + " workpieces (job" + currentJob.getID() + ") is given externally.");
			}
			Logger.printSimulationInfo(timeCurrent, name, "New Production scheduling of " + 
							currentJob.getQuantity() + " workpieces (Job " + (currentJob.getID()+1) + " Operation " + (currentOperation.getID()+1) + ") is given externally.");	
			state.setFinalDestState("Procduction");
			state.doInterStateTransition();
		}
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
	
	public void terminateSimulation() {
		if (Config.history) {
			logSimu.log("[" + getCurrentTime() + "][OFF] Simulation terminates.");
			logSimu.output();
			// printEnergyConsumption();
		}
	}
	
	public int getSetupTime(KeyJobOperation previousJobOperation, KeyJobOperation currentJobOperation) {
		Logger.printSimulationInfo(timeCurrent, name, "previousJob ID = " + (previousJobOperation.getJobID()+1) + 
				", previousOperation ID = " + (previousJobOperation.getOperationID()+1) + 
				", currentJob ID = " + (currentJobOperation.getJobID()+1) + 
				", currentOperation ID = " + (currentJobOperation.getOperationID()+1));
		// UDUT
		System.out.println(setupTimes.get(new KeyJobOperationJobOperation(previousJobOperation, currentJobOperation)));
		return setupTimes.get(new KeyJobOperationJobOperation(previousJobOperation, currentJobOperation));
	}
	
	public void setSetupTime(KeyJobOperation previousJobOperation, KeyJobOperation currentJobOperation, int setupTime) {
		setupTimes.put(new KeyJobOperationJobOperation(previousJobOperation, currentJobOperation), setupTime);
	}
	
	public void setChangeover(Changeover c) {
		changeover = c;
	}
	
	public void stayIdle(long periodIdle) {
		state.doSelfTransition(periodIdle);
	}
	
	public Changeover getChangeover() {
		return changeover;
	}
	
	public void doSplitChangeovers() {
		Logger.printSimulationInfo(timeCurrent, name, "Machine performs two split changeovers before and after a weekend, respectively");
//		System.out.println("First start time of changeover = " + changeover.getFirstStartTime());
//		System.out.println("First end time of changeover = " + changeover.getFirstEndTime());
		long durationPartialChangeover = ChronoUnit.SECONDS.between(
							changeover.getFirstStartTime(), changeover.getFirstEndTime());
		Logger.printSimulationInfo(name, "The duration of 1st changeover = " + durationPartialChangeover + " sec");
		doAPartialChangeover(durationPartialChangeover);
		powerOff();
		long weekendDuration = ChronoUnit.SECONDS.between(timeCurrent,
				 changeover.getLastStartTime().minusSeconds(Config.durationPowerOn));
//		System.out.println("Time after powering off: " + timeCurrent);
//		System.out.println("durationPartialChangeover1 = " + durationPartialChangeover);
//		System.out.println("weekendDuration = " + weekendDuration);
		stayOff(weekendDuration);
		powerOn();
//		System.out.println("Time after powering on: " + timeCurrent);
		durationPartialChangeover = ChronoUnit.SECONDS.between(
				changeover.getLastStartTime(), changeover.getLastEndTime());
		Logger.printSimulationInfo(timeCurrent, name, "The duration of 2nd changeover: " + durationPartialChangeover + " sec");
		doAPartialChangeover(durationPartialChangeover);
//		System.out.println("durationPartialChangeover2 = " + durationPartialChangeover);
		++changeoverTimes;
	}
	
	private void doAPartialChangeover(long durationPartialChangeover) {
		if (Config.history) {
			logSimu.log("[" + getCurrentTime() + "][Mach] Machine starts to do a partial changeover.");
		}
		flagChangeover = true;
		state.setTimeEnergyCost(durationPartialChangeover);
		flagChangeover = false;	//flagChangeover is usually turned off
		if (Config.history) {
			logSimu.log("[" + getCurrentTime() + "][Mach] The partial changeover is done.");
		}
	}
	
	public void doACompleteChangeover() {
		if (Config.history) {
			logSimu.log("[" + getCurrentTime() + "][Mach] Machine starts to do a complete changeover.");
		}
		flagChangeover = true;
		Logger.printSimulationInfo(timeCurrent, name, "Machine performs a complete changeover of " + changeover.getDuration() + " sec");
		state.setTimeEnergyCost(changeover.getDuration());
		flagChangeover = false;	//flagChangeover is usually turned off
		if (Config.history) {
			logSimu.log("[" + getCurrentTime() + "][Mach] The complete changeover is done.");
		}
		++changeoverTimes;
	}
	
	public void addAChangeover(Changeover c) {
		listChangeovers.add(c.deepCopy());
	}
}
