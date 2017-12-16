package platform;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.time.LocalDateTime;

public class Logger {
	StringBuffer sb = new StringBuffer();
	String dir;
	
	public Logger(String dir) {
		this.dir = dir;
	}
	
	public void log(String s) {
//		System.out.println(s);
		sb.append(s + System.lineSeparator());
	}
	
	public void record(String s) {
		sb.append(s + System.lineSeparator());
	}
	
	public void logYear(int year) {
		sb.append(year + ", ");
		System.out.print(year + ", ");
	}
	
	public void logIteration(int iter) {
		sb.append(iter + ", ");
		System.out.print(iter + ", ");
	}
	
	public void logMonday(String mondayDate) {
		sb.append(mondayDate + ", ");
		System.out.print(mondayDate + ", ");
	}
	
	public void logNumJob(int numJob) {
		sb.append(numJob + ", ");
		System.out.print(numJob + ", ");
	}
	
	public void logNumBottle(int numBottle) {
		sb.append(numBottle + ", ");
		System.out.print(numBottle + ", ");
	}
	
	public void logPureJobDuration(int jobDuration) {
		sb.append(jobDuration + ", ");
		System.out.print(jobDuration + ", ");
	}
	
	public void logMinimalTotalProdDuration(long d) {
		sb.append(d + ", ");
		System.out.print(d + ", ");
	}
	
	public void logCosts(String costs) {
		sb.append(costs);
	}
	
	public void logElectricityPriceStatistics(String priceStatistics) {
		sb.append(priceStatistics + System.lineSeparator());
	}
	
	public void logState(String stateEndTime) {
		sb.append(stateEndTime + System.lineSeparator());
	}
	
	public void output() {
		try {
			writeFile(sb.toString(), new File(dir));
		} catch (Exception e) {
			e.printStackTrace();
		}
	}
	
	private void writeFile(String data, File target) throws Exception {
		if (target.exists() == false) {
			target.createNewFile();
		}
		BufferedWriter bw = new BufferedWriter(new FileWriter(target));
		bw.write(data);
		bw.close();
	}
	
	public static void printSimulationInfo(LocalDateTime simulationTime, String className, String simulationInfo) {
		if (Config.history) {
			System.out.println("[" + simulationTime + "][" + className + "] " + simulationInfo);
		}
	}
	
	public static void printSimulationInfo(String className, String simulationInfo) {
		if (Config.history) {
			System.out.println("[" + className + "] " + simulationInfo);
		}
	}
	
	// UDUT
//	public static void main(String[] args) {
//		Logger logger = new Logger(Config.homeFolder + "\\ok.txt");
//		logger.log("OK");
//		logger.output();
//	}
}
