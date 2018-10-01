package machine;

public interface StateNotUsed {
	/**
	 * 
	 * @return name of the state
	 */
	public String getName();
	
	/**
	 * 
	 * @param buttonState: ON: buttonState=1; OFF: buttonState=0
	 */
	public void pressPowerButton(int buttonState);
	
	/**
	 * delay: to indicate the duration for staying at the current state
	 * @param duration
	 * The time will advance in this method
	 */
	public void doSelfTransition(long duration);	
	
	/**
	 * Make the current state transition to the next neighbouring state 
	 * The next state is implicately indicated by the variable finalDestState in each state
	 * The time will NOT advance in this method
	 */
	public void doInterStateTransition();
	
	/**
	 * Set the final destination state of the current state
	 * @param destState
	 */
	public void setFinalDestState(String destState);
	
	public String getFinalDestState();
	
	public void setTimeEnergyCost(long stateDuration);
}
