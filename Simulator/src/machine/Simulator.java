package machine;

import platform.Config;
import shopfloor.ShopFloor;

public class Simulator {

	public static void main(String[] args) {
//		State on = new State("On");
//		String[] successor1 = {"On", "Off"};
//		on.setSuccessors(successor1);
//		
//		State off = new State("Off");
//		off.setSuccessors(successor1);
//		
//		Machine m1 = new Machine(1, "titi");
//		m1.initState(on);
//		// m1.initState(on);
//		m1.setState(off);
//		// m1.setState(on);
//		
//		System.out.println("EquipmentID: " + m1.getID() + "\n" + "EquipmentName: "+m1.getName());
//		System.out.println("MachineState: " + m1.getMachineState());;
		Config config = new Config("single machine");
		config.getInstance();
		
		ShopFloor shopFloor = new ShopFloor("single machine");
		shopFloor.performJobs();
		
		// Onjective
		System.out.println("Summary:");
		System.out.println("Start Schedule: " + Config.startTimeSchedule);
		System.out.println("Due Schedule: " + Config.dueTime);
		System.out.println("Current EndTime: " + shopFloor.getCurrentTime());

		long makeSpan = shopFloor.getMakespan();
		System.out.println("Makespan: " + Machine.calculateDay(makeSpan) + " d " 
							+ Machine.calculateHour(makeSpan) + " h "
							+ Machine.calculateMin(makeSpan) + " m "
							+ Machine.calculateSec(makeSpan) + " s."
		);
		System.out.println("Late jobs:");
		shopFloor.getLateJobs();
		System.out.println("\nTotalWeightedTardiness(sum(Quantity * Duration) for each late job):");
		long tw = shopFloor.getWeightedTardiness();
		System.out.println(Machine.calculateDay(tw) + " d " 
				+ Machine.calculateHour(tw) + " h "
				+ Machine.calculateMin(tw) + " m "
				+ Machine.calculateSec(tw) + " s."
);
	}

}
