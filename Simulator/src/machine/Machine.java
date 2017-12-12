package machine;

import java.util.Hashtable;
import java.util.Map;

import platform.KeyJobOperation;

public class Machine {
	// Equipment attributes
	private int ID; // EquipmentID
	private String name; // Name
	
	// Variables
	private State state;

	// Production plan related attributes
	private Map<KeyJobOperation, Integer> cycleProduction = new Hashtable<KeyJobOperation, Integer>();//processing time dependent on job, operation, and machine
	private Map<KeyJobOperation, Double> powerProduction = new Hashtable<KeyJobOperation, Double>();//operation-dependent production power

	
	public Machine(int id, String name) {
		ID = id;
		this.name = name;
	}
	
	public Machine(int id) {
		ID = id;
		name = "Mach" + ID;
	}
	
	// Setters and Getters
	public State getState() {
		return state;
	}
	public void setState(State state) {
		State currentState = this.state;
		if (state.getSuccessor().contains(currentState.getName())) {
			this.state = state;
		} else {
			System.out.println("SetState Wrong: State not availble from current state!");
			System.exit(0);
		}
	}
	
	public int getID() {
		return ID;
	}
	public String getName() {
		return name;
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
	
}
