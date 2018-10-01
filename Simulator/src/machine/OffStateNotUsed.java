package machine;

public class OffStateNotUsed implements State {
	
	private Machine machine;
	private String name = "Off";
	private String finalDestState = name;
	
	public OffStateNotUsed(Machine machine) {
		this.machine = machine;
	}
	
	@Override
	public String getName() {
		return name;
	}

	@Override
	public void pressPowerButton(int buttonState) {
		switch(buttonState) {
			case 1: 
				doInterStateTransition();
				break;
			case 0: 
				System.out.println("[" + machine.getCurrentTime() + "][Off] Warning: Machine already stays off."+System.lineSeparator());
				break;
			default:
				System.out.println("[Off] Wrong button State value: It should be either 0 or 1.");
				System.exit(1);
		}
	}

	@Override
	public void doSelfTransition(long duration) {
		if (duration < 0) {
			System.out.println("[" + machine.getCurrentTime() + "][Off] Error in duration = " + duration + "!");
			System.exit(-1);
		}
		else {
			// TODO Consider stochastic events (machine failure)
			setTimeEnergyCost(duration);
		}
	}

	@Override
	public void doInterStateTransition() {
		machine.setState(machine.getState("Production"));
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
		machine.updateCurrentTime(stateDuration);
		machine.updateStateDuration(name, stateDuration);
	}

}
