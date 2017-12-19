package platform;

public class KeyJobOperationJobOperation {
	private	final KeyJobOperation previousJobOperation;
	private final KeyJobOperation currentJobOperation;
	
	public KeyJobOperationJobOperation(KeyJobOperation previousKey, KeyJobOperation currentKey) {
		previousJobOperation = previousKey;
		currentJobOperation = currentKey;
	}
	
	@Override
	public boolean equals(Object o) {
		if (this == o) return true;
		if (!(o instanceof KeyJobOperationJobOperation))
			return false;
		KeyJobOperationJobOperation key = (KeyJobOperationJobOperation) o;
		return previousJobOperation.getJobID()	== key.previousJobOperation.getJobID() &&
				previousJobOperation.getOperationID() == key.previousJobOperation.getOperationID() &&
				currentJobOperation.getJobID() == key.currentJobOperation.getJobID() &&
				currentJobOperation.getOperationID() == key.currentJobOperation.getOperationID();
	}
	
	@Override
	public int hashCode() {
		int result = previousJobOperation.hashCode();
		result = 31 * result + currentJobOperation.hashCode();
		return result;
	}
}
