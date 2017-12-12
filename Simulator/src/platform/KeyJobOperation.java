package platform;

public class KeyJobOperation {
	private final int jobID;
	private final int operationID;
	
	public KeyJobOperation(int jobID, int operationID) {
		this.jobID = jobID;
		this.operationID = operationID;
	}
	
	/**
	 * Methods for Map<Key2D, V>
	 */
	@Override
	public boolean equals(Object o) {
		if (this == o) return true;
		if (!(o instanceof KeyJobOperation))
			return false;
		KeyJobOperation key = (KeyJobOperation) o;
		return jobID == key.jobID && operationID == key.operationID;
	}
	
	@Override
	public int hashCode() {
		int result = jobID;
		result = 31 * result + operationID;
		return result;
	}

	public int getJobID() {
		return jobID;
	}

	public int getOperationID() {
		return operationID;
	}
	
	@Override
	public String toString() {
		return " JobID: " + (jobID+1) + " OperationID: " + (operationID+1);
	}
	
}
