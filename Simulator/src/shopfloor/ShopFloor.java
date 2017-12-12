package shopfloor;

import java.time.LocalDateTime;
import java.util.LinkedList;
import java.util.List;

import machine.Machine;
import platform.Config;

public class ShopFloor {
	
	private final String name = "ShopFloor";
	
	// Input info
	private List<Machine> listMachines = new LinkedList<Machine>();
	private List<Job> listJobs = new LinkedList<Job>();
	
	// Variables used in simulation
	private LocalDateTime currentTime = Config.startTimeSchedule;	//it keeps up with the latest time of all machines
	private LinkedList<Job> listExeJobs = new LinkedList<Job>();	//a job is considered executed once its last operation is completed
	private int[] productQuantity = new int[Config.numProdType];	//accumulated amount of produced products (whose last operation is completed)
	private int TotalProductQuantity; 	//the sum of all types of products


}
