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
	}

}
