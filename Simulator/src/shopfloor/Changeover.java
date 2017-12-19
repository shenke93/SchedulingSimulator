package shopfloor;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.LinkedList;

import platform.Utils;

public class Changeover {
	private LinkedList<LocalDateTime> startTime = new LinkedList<LocalDateTime>();
	private LinkedList<LocalDateTime> endTime = new LinkedList<LocalDateTime>();
	private int duration;
	
	public Changeover(int d) {
		duration = d;
	}
	
	public Changeover(LinkedList<LocalDateTime> st, LinkedList<LocalDateTime> et, int d) {
		for (LocalDateTime t : st) {
			startTime.add(t);
		}
		for (LocalDateTime t : et) {
			endTime.add(t);
		}
		duration = d;
	}
	
	public void setStartEndTimeBackward(LocalDateTime upperBound) {
		startTime.clear();
		endTime.clear();
		
		LocalDateTime st = upperBound.minusSeconds(duration);
		if (Utils.isSplitByWeekend(st, upperBound)) {
			LocalDateTime startOfCurrentWeek = Utils.getStartOfSameWeek(upperBound);
			long duration2ndHalf = ChronoUnit.SECONDS.between(startOfCurrentWeek, upperBound);
			long duration1stHalf = duration - duration2ndHalf;
			LocalDateTime endOfPreviousWeek = Utils.getEndOfPreviousWeek(upperBound);
			startTime.add(endOfPreviousWeek.minusSeconds(duration1stHalf));
			startTime.add(startOfCurrentWeek);
			endTime.add(endOfPreviousWeek);
			endTime.add(upperBound);
		}
		else {
			startTime.add(st);
			endTime.add(upperBound);
		}
	}
	
	public LocalDateTime getFirstStartTime() {
		return startTime.getFirst();
	}
	
	public int getDuration(){
		return duration;
	}
	
	public boolean isSplit() {
		if (startTime.size() == 1)
			return false;
		else if (startTime.size() > 1)
			return true;
		else {
			System.out.println("[Changeover] Error: startTime contins no element!");
			System.exit(-1);
			return false;
		}
	}
	
	public LocalDateTime getFirstEndTime() {
		return endTime.getFirst();
	}
	
	public LocalDateTime getLastStartTime() {
		return startTime.getLast();
	}
	
	public LocalDateTime getLastEndTime() {
		return endTime.getLast();
	}
	
	public Changeover deepCopy() {
		Changeover changeover = new Changeover(startTime, endTime, duration);
		return changeover;
	}
}
