package platform;

public class Utility {
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
}
