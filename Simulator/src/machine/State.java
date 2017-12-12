package machine;

import java.util.HashSet;
import java.util.Set;

public class State {
	private String name;
	private Set<String> successor = new HashSet<String>();
	
	public State(String name) {
		this.name = name;
	}
	
	public String getName() {
		return name;
	}
	
	public void setSuccessors(String[] name) {
		for(String s : name) {
			successor.add(s);
		}
	}

	public Set<String> getSuccessor() {
		return successor;
	}
	
}
