package machine;

import java.time.LocalDateTime;

public class ProductionStateNotUsed implements State {
	
	private Machine machine;
	private LocalDateTime startTime, endTime; // Time points for produciton state
	private String name = "Production";
	private String finalDestState;
	
	public ProductionStateNotUsed(Machine machine) {
		this.machine = machine;
	}
	@Override
	public String getName() {
		return name;
	}

	@Override
	public void pressPowerButton(int buttonState) {
	}

	@Override
	public void doSelfTransition(long duration) {

	}

	@Override
	public void doInterStateTransition() {
//		machine.addStateToList(machine.getCurrentTime(), name, 
//				machine.getPowerProduction(machine.getCurrentJob(), machine.getCurrentOperation()));
//		machine.setState(machine.getState("Off"));
	}

	@Override
	public void setFinalDestState(String destState) {
		finalDestState = destState;
	}

	@Override
	public String getFinalDestState() {
		return finalDestState;
	}

	@Override
	public void setTimeEnergyCost(long stateDuration) {
		// TODO Auto-generated method stub

	}

}
