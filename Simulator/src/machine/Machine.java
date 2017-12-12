package machine;

public class Machine {
	// Constant attributes
	private int ID; // EquipmentID
	private String name; // Name
	
	// Variables
	private State state;
	private int speed;
	
	public Machine(int id, String name) {
		ID = id;
		this.name = name;
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
	public int getSpeed() {
		return speed;
	}
	public void setSpeed(int speed) {
		this.speed = speed;
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
	
	
	
	
}
