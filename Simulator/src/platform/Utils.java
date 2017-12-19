package platform;

import java.time.DayOfWeek;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;

import machine.Machine;
import platform.Config;

/**
 * This class contains frequently-used utilities to handle timing issues in 
 * placing jobs and changeovers on the time horizon
 * @author Xu GONG
 * 
 */
public class Utils {	
	/**
	 * Machine powering on/off duration is considered as part of weekends
	 * @param inputTime
	 * @return
	 */
	public static boolean isOnWeekendIncludingPowerOnOff(LocalDateTime inputTime) {
		if (Config.workOnWeekend)
			return false;
	
		if (inputTime.getDayOfWeek() == DayOfWeek.SATURDAY) {
			LocalDateTime endOfSameWeek = getEndOfSameWeek(inputTime);
			if (inputTime.isAfter(endOfSameWeek)) {
				return true;
			}
			return false;
		}
		
		if (inputTime.getDayOfWeek() == DayOfWeek.SUNDAY) {
			return true;
		}
		
		if (inputTime.getDayOfWeek() == DayOfWeek.MONDAY) {
			LocalDateTime startOfSameWeek = getStartOfSameWeek(inputTime);
			if (inputTime.isBefore(startOfSameWeek)) {
				return true;
			}
			return false;
		}
	
		return false;
	}
	
	public static boolean isOnNaturalWeekend(LocalDateTime inputTime) {
		if (Config.workOnWeekend) {
			return false;
		}
	
		if (inputTime.getDayOfWeek() == DayOfWeek.SATURDAY) {
			LocalDateTime endOfSameWeek = inputTime.with(TemporalAdjusters
					.nextOrSame(DayOfWeek.SATURDAY))
					.truncatedTo(ChronoUnit.DAYS)
					.plusHours(Config.startHourOfWeek);
			if (inputTime.isAfter(endOfSameWeek)) {
				return true;
			}
			return false;
		}
		
		if (inputTime.getDayOfWeek() == DayOfWeek.SUNDAY) {
			return true;
		}
		
		if (inputTime.getDayOfWeek() == DayOfWeek.MONDAY) {
			LocalDateTime startOfSameWeek = inputTime.truncatedTo(ChronoUnit.DAYS)
					.plusHours(Config.startHourOfWeek);
			if (inputTime.isBefore(startOfSameWeek)) {
				return true;
			}
			return false;
		}
	
		return false;
	}
	
	public static boolean isSplitByWeekend(LocalDateTime lowerBound, LocalDateTime upperBound) {
		boolean isSplit = true;
		if (Config.workOnWeekend) {
			isSplit = false;
		}
		else if (lowerBound.get(Config.weekOfYear) == upperBound.get(Config.weekOfYear)) {
			LocalDateTime startOfCurrentWeek = getStartOfSameWeek(lowerBound);
			LocalDateTime endOfCurrentWeek = getEndOfSameWeek(startOfCurrentWeek);
			if (!lowerBound.isBefore(startOfCurrentWeek) && !lowerBound.isAfter(endOfCurrentWeek) &&
				!upperBound.isBefore(startOfCurrentWeek) && !upperBound.isAfter(endOfCurrentWeek)) {
				isSplit = false;
			}
		}
		return isSplit;
	}
	
	public static LocalDateTime min(LocalDateTime time0, LocalDateTime time1) {
		if (time0 == null) {
			return time1;
		}
		else if (time1 == null) {
			return time0;
		}
		else {
			if (time0.isAfter(time1)) {
				return time1;
			}
			return time0;
		}		
	}
	
	public static LocalDateTime max(LocalDateTime time0, LocalDateTime time1) {
		if (time0 == null) {
			return time1;
		}
		else if (time1 == null) {
			return time0;
		}
		else {
			if (time0.isAfter(time1)) {
				return time0;
			}
			return time1;
		}		
	}
	
	public static LocalDateTime getEndOfPreviousWeek(LocalDateTime time) {
		if (time.getDayOfWeek() == DayOfWeek.SUNDAY) {
			time = time.with(TemporalAdjusters.previous(DayOfWeek.SATURDAY));
		}
		return time.with(TemporalAdjusters.previous(DayOfWeek.SATURDAY))
				.truncatedTo(ChronoUnit.DAYS)
				.plusHours(Config.startHourOfWeek)
				.minusSeconds(Config.defaultShutdownDuration);
	}
	
	public static LocalDateTime getEndOfSameWeek(LocalDateTime time) {
		if (time.getDayOfWeek() == DayOfWeek.SUNDAY) {
			return time.with(TemporalAdjusters.previousOrSame(DayOfWeek.SATURDAY))
					.truncatedTo(ChronoUnit.DAYS)
					.plusHours(Config.startHourOfWeek)
					.minusSeconds(Config.defaultShutdownDuration);
		}
		return time.with(TemporalAdjusters.nextOrSame(DayOfWeek.SATURDAY))
					.truncatedTo(ChronoUnit.DAYS)
					.plusHours(Config.startHourOfWeek)
					.minusSeconds(Config.defaultShutdownDuration);
	}
	
	public static LocalDateTime getStartOfSameWeek(LocalDateTime time) {			
		return time.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY))
					.truncatedTo(ChronoUnit.DAYS)
					.plusHours(Config.startHourOfWeek)
					.plusSeconds(Config.durationPowerOn);
	}
	
	public static LocalDateTime getStartOfNextWeek(LocalDateTime time) {
		return time.with(TemporalAdjusters.next(DayOfWeek.MONDAY))
				.truncatedTo(ChronoUnit.DAYS)
				.plusHours(Config.startHourOfWeek)
				.plusSeconds(Config.durationPowerOn);
	}
	
	/**
	 * Weekend is excluded if no weekend production: the start of a week is the end of machine 
	 * powering on, and the end of a week is the start of machine powering off
	 * @param lowerBound
	 * @param upperBound
	 * @return Effective duration between lowerBound and upperBound that can be used for production
	 */
	public static long getDuration(LocalDateTime lowerBound, LocalDateTime upperBound) {
		if (lowerBound.isAfter(upperBound)) {
			return -1;
		}
		else if (Utils.isSplitByWeekend(lowerBound, upperBound)) {
			//Ensure lowerBound and upperBound are out of weekends
			if (Utils.isOnWeekendIncludingPowerOnOff(lowerBound)) {
				if (lowerBound.getDayOfWeek() == DayOfWeek.MONDAY) {
					lowerBound = Utils.getStartOfSameWeek(lowerBound);
				}
				else {
					lowerBound = Utils.getStartOfNextWeek(lowerBound);
				}
			}
				
			if (Utils.isOnWeekendIncludingPowerOnOff(upperBound)) {
				if (upperBound.getDayOfWeek() == DayOfWeek.MONDAY &&
					upperBound.isBefore(Utils.getStartOfSameWeek(upperBound))) {
					upperBound = Utils.getEndOfPreviousWeek(upperBound);
				}
				else {
					upperBound = Utils.getEndOfSameWeek(upperBound);
				}
			}
			
			//Accumulate duration 
			long duration = ChronoUnit.SECONDS.between(lowerBound, Utils.getEndOfSameWeek(lowerBound));
			int numWeek = upperBound.get(Config.weekOfYear) - lowerBound.get(Config.weekOfYear);
			if (numWeek > 1) {
				duration += Config.freeDurationOfNormalWeek * (numWeek - 1);
			}
			duration += ChronoUnit.SECONDS.between(
					Utils.getStartOfNextWeek(lowerBound).plusWeeks(numWeek - 1), upperBound);
			return duration;
		}
		else {
			return ChronoUnit.SECONDS.between(lowerBound, upperBound);
		}
	}
	
	public static LocalDateTime shiftToNextWorkingWeek(LocalDateTime time) {
		if (time.getDayOfWeek() == DayOfWeek.MONDAY && time.isBefore(Utils.getStartOfSameWeek(time))) {
			return Utils.getStartOfSameWeek(time);
		}				
		return Utils.getStartOfNextWeek(time);
	}
	
	public static LocalDateTime shiftToPreviousWorkingWeek(LocalDateTime time) {
		if (time.getDayOfWeek() == DayOfWeek.MONDAY) {
			return Utils.getEndOfPreviousWeek(time);
		}
		return Utils.getEndOfSameWeek(time);
	}
	
	public static String getDayHourMinSec(long duration) {
		StringBuilder time = new StringBuilder("");
		time.append(Machine.calculateDay(duration) + "d");
		time.append(Machine.calculateHour(duration) + "h");
		time.append(Machine.calculateMin(duration) + "m");
		time.append(Machine.calculateSec(duration) + "s");
		return time.toString();
	}
	
}