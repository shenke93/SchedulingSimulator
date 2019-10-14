''' 
@Joachim David, joachim.david@ugent.be, January 2019
Probability distribution library, can generate a probability distribution from data
-----------------------------------------------------------------------------------
Definitions of the functions can be found in the book
Reliability and Safety Engineering (2016), Springer Series of Reliability Engineering
'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import lognorm
import scipy


def sturges_rule(length):
    ''' Applies sturges rule to an integer number 
    ---
    * length: int
    * returns int'''
    assert isinstance(length, int), 'Only integers permitted'
    return int(np.round(1 + 3.322 * np.log10(length)))

def make_hist_frame(duration, observed=None, numbins=None, range=None, return_bins=False):
    duration = np.array(duration)
    if observed is not None:
        observed = np.array(observed)
    if numbins is None:
        # Book Reliability and Safety Engineering, suggested number of bins, page 61
        # Sturges' rule for grouping data
        numbins = sturges_rule(len(duration))
        numbins
    if range is None:
        # Determine histogram range
        mint = 0
        maxt = np.max(duration)
        range = (mint, maxt)
    if observed is not None:
        duration_failures = duration[observed==True]
        duration_dropout = duration[observed==False]
        hist, bin_edges = np.histogram(duration_failures, bins=numbins, range=range)
        hist_do, bin_edges = np.histogram(duration_dropout, bins=numbins, range=range)
    else:
        hist, bin_edges = np.histogram(duration, bins=numbins, range=range)
    timestep = bin_edges[1] - bin_edges[0]

    df_temp = pd.DataFrame([])
    new_index = []
    for start, end in zip(bin_edges[:-1], bin_edges[1:]):
        #print(str(start) + ':' + str(end))
        string = '{:.2f}-{:.2f}'.format(start, end)
        new_index.append(string)

    if observed is None:
        start_amount = np.sum(hist)
    else:
        start_amount = np.sum(hist) + np.sum(hist_do)
    
    failures = hist
    if observed is not None:
        censored = hist_do
    else:
        censored = np.zeros(failures.shape)
    remaining = start_amount - np.delete(np.insert(np.cumsum(failures) + np.cumsum(censored), 0, 0), -1)
    remaining_adj = remaining - 0.5 * censored

    prob_survive = 1 - failures/remaining_adj

    reliability = np.cumprod(prob_survive)
    #print(reliability)
    failure_func = 1 - reliability

    inst_fail = failures / np.sum(failures) / timestep

    hazard = failures / remaining / timestep

    #import pdb; pdb.set_trace()
    #print(np.array(np.power(reliability, 2)))
    #print(np.power(reliability, 2))
    #print(np.array((np.cumsum(1-prob_survive) / (remaining_adj * prob_survive))))

    #variance = reliability ** 2 * np.cumsum((1-prob_survive) / (remaining_adj * prob_survive))
    #std = variance ** (1/2)

    df_temp = pd.DataFrame({'Remaining': remaining, 'Failures': failures,
                            'Reliability': reliability, 'FailCDF': failure_func,
                            'FailPDF': inst_fail, 'Hazard': hazard, #'Std': std
                            }, index=new_index)
    df_temp = df_temp[['Remaining', 'Failures', 'Reliability', 'FailCDF', 'FailPDF', 'Hazard']]#, 'Std']]
    if not return_bins:
        return df_temp
    return df_temp, bin_edges

def duration_run_down(duration, up, down, continue_obs, stop_obs, observation=True):
    ''' This function brings the two functions hereunder together.
    The functions keep existing for backward compatibility.
    Read the comments there to get more insight in this function'''
    # This checks if all values have been assigned and all lists have same length
    try:
        assert (len(up) == len(down) == len(duration) == len(continue_obs) == len(stop_obs))
        assert (sum(up) + sum(down) + sum(stop_obs) + sum(continue_obs) == len(duration))
    except:
        print(sum(up), sum(down), sum(stop_obs), sum(continue_obs), len(duration))
        raise
    l = len(up)
    uptime = []     # Empty list of runtime
    sum_uptime = 0  # Runtime counter

    downtime = [] # Empty list of downtime
    sum_downtime = 0 # Downtime counter

    if observation:
        observed_up = []
        observed_down = []

    for i in np.arange(l):
        d = down[i]
        r = up[i]
        s = stop_obs[i]
        c = continue_obs[i]
        t = duration[i]
        if d: # New downtime
            # Save the uptime and reset the counter
            if sum_uptime > 0:
                uptime.append(sum_uptime)
                sum_uptime = 0 
                if observation:
                    observed_up.append(True)
            # Count the downtime
            sum_downtime += t
        elif r: # New runtime
            # Save the downtime and reset the counter
            if sum_downtime > 0:
                downtime.append(sum_downtime)
                sum_downtime = 0
                if observation:
                    observed_down.append(True)
            sum_uptime += t
        elif c: # Continue after this
            pass
        elif s: # New censoring
            if observation:
                if sum_uptime > 0:
                    uptime.append(sum_uptime)
                    observed_up.append(False)
                    sum_uptime = 0
                if sum_downtime > 0:
                    downtime.append(sum_downtime)
                    observed_down.append(False)
                    sum_downtime = 0
        else:
            print('Something went wrong')
    uptime = pd.Series(uptime); downtime = pd.Series(downtime)
    return_tuple = (uptime, downtime)
    if observation:
        observed_up = pd.Series(observed_up); observed_down = pd.Series(observed_down)
        return_tuple += (observed_up, observed_down)
    return return_tuple

def duration_of_downtime(duration, up, down):
    ''' From three arrays, generate the duration of downtime as a Series
    duration: the length of the action
    up: uptime which needs to be counted
        if True, this counts as Uptime
        if False, this is not Uptime nor downtime (e.g. pause) and the time is not counted
    down: downtime which is valid
        if True, this is valid Downtime with the right reason
        if False, this is not Downtime with the right reason (Uptime or failure not counted)
    
    The function could be rewritten with one array with three states
    -1: failure
    0: failure but not counted as failure time(e.g. pause)
    1: runtime
    But this works too:
    '''
    assert (len(up) == len(down) == len(duration))
    l = len(up)

    downtime = [] # Empty list of downtime
    sum_downtime = 0 # Downtime counter

    for i in np.arange(l):
        d = down[i]
        r = up[i]
        t = duration[i]
        if d: # New downtime
            # Count the downtime
            sum_downtime += t
        elif r: # New runtime
            # Save the downtime and reset the counter
            if sum_downtime > 0:
                downtime.append(sum_downtime)
                sum_downtime = 0
        else: # New invalid time
            # TODO: add censoring option (will possibly need a fourth list)
            pass
    downtime = pd.Series(downtime)
    return downtime

def duration_between_downtime(duration, up, down):
    ''' This function brings the two functions hereunder together.
    The functions keep existing for backward compatibility.
    Read the comments there to get more insight in this function'''
    assert (len(up) == len(down) == len(duration))
    l = len(up)
    uptime = []     # Empty list of runtime
    sum_uptime = 0  # Runtime counter

    for i in np.arange(l):
        d = down[i]
        r = up[i]
        t = duration[i]
        if d: # New downtime
            # Save the uptime and reset the counter
            if sum_uptime > 0:
                uptime.append(sum_uptime)
                sum_uptime = 0 
        elif r: # New runtime
            sum_uptime += t
        else: # New invalid time
            pass
    uptime = pd.Series(uptime)
    return uptime

def _determine_exp(values, reliability):
    '''
    Determine the Exponential distribution
    :param values:
    :param reliability:
    :return:
    '''
    from scipy.stats import linregress
    lambdas = -np.log(reliability)
    slope, intercept, _, _, _ = linregress(values[1:-1], lambdas[1:-1])
    lamb = slope
    return lamb

def _determine_weibull(values, reliability):
    '''
    Determine the Weibull distribution using the reliability measure and their values
    '''
    from scipy.stats import linregress
    lambdas = -np.log(reliability)
    # Determine the distribution
    slope, intercept, _, _, _, = linregress(np.log(values[1:-1]), np.log(lambdas[1:-1]))
    beta = slope
    alpha = np.exp(-(intercept/beta))
    return alpha, beta

def durations_to_hist(durations):
    hist, bin_edges = np.histogram(np.array(durations),
                                       bins=sturges_rule(len(durations)))
    normhist = hist / sum(hist)
    c_fail = np.cumsum(normhist)
    return bin_edges[1:], 1-c_fail

def _determine_exp_or_weibull(values, reliability):
    ## Determine if distribution is Weibull distribution
    # Input: timestamps, their inferred reliaiblity
    # If Weibull: return alpha and beta of the Weibull distribution
    # If exponential: return lambda and offset
    from scipy.stats import linregress
    lambdas = -np.log(reliability)

    # Determine the distribution
    slope, intercept, _, _, _, = linregress(np.log(values[1:-1]), np.log(lambdas[1:-1]))

    beta = slope
    alpha = np.exp(-(intercept/beta))

    dist_string = ''

    if 0.9 < beta < 1.1:
        dist_string = 'exp'
        print('This is an exponential distribution with lambda {:.3}'.format(1/alpha))
        plt.plot(values[1:-1], lambdas[:-1], 'o', label='real data') # = lambda * y + c
        slope, intercept, _, _, _, = linregress(values[1:-1], lambdas[:-1])
        lamb = slope
        offset = intercept
        plt.title('Linear plot with slope {:.3} and intercept {:.3}'.format(slope, intercept))
        plt.xlabel('t')
        plt.ylabel('ln(1/R(t))')
        plt.plot(values[1:-1], slope * values[1:-1] + intercept, label='y = {:.3}x + {:.3}'.format(slope, intercept))
        plt.legend()
    else:
        dist_string = 'weibull'
        print('This is a Weibull distribution with alpha {:.3} and beta {:.3}'.format(alpha, beta))
        if beta < 1:
            print('This results in a decreasing failure rate')
        else:
            print('This results in an increasing failure rate')
        plt.plot(np.log(values[1:-1]), np.log(lambdas[1:-1]), 'o', label='real data') # = lambda * y + c
        slope, intercept, _, _, _, = linregress(np.log(values[1:-1]), np.log(lambdas[1:-1]))
        plt.title('Linear plot with slope {:.3} and intercept {:.3}'.format(slope, intercept))
        plt.xlabel('ln t')
        plt.ylabel('ln (ln (1/R(t))')
        plt.plot(np.log(values[1:-1]), slope * np.log(values[1:-1]) + intercept, label='y = {:.3}x {:+.3}'.format(slope, intercept))
        plt.legend()
    
    if dist_string=='weibull':
        return alpha, beta, dist_string
    elif dist_string=='exp': # if exp
        return lamb, offset, dist_string
    else:
        return None


def total_cost_maintenance(timearray, model, cp=100, cu=250, return_separate=False):
    '''
    If you have a model of the failure rate, calculate the ideal total maintenance cost versus time
    return_separate (boolean): If True, return all the values for the costs split up as planned and unplanned maintenance cost
    get_min (boolean): If True, return the minimum value (the best value for Preventive Maintenance)
    model: a class from the classes below
    '''
    Cp = cp
    Cu = cu
    # calculate expected time if there is unexpected breakdown
    
    # summate the expectation of preventive maintenance * time of maintenance +
    # the expectation of unexpected maintenance * expected value of unexpected breakdown
    
    #expectedvalue = np.array([scipy.integrate.quad(model.reliability_cdf, 0, t)[0] for t in timearray])
    #denum = expectedvalue * (1 - model.reliability_cdf(timearray)) + model.reliability_cdf(timearray) * timearray
    
    expectedvalue = np.array([scipy.integrate.quad(model.reliability_cdf, 0, t)[0] for t in timearray])
    denum = expectedvalue
    
    cput = (Cp * model.reliability_cdf(timearray) + 
            Cu * (1 - model.reliability_cdf(timearray))) / denum
    if return_separate:
        preventive = Cp * model.reliability_cdf(timearray) / denum
        unexpected = Cu * (1 - model.reliability_cdf(timearray)) / denum
        return cput, preventive, unexpected
    # don't return separate
    return cput

def pm_recommend(model, cp=100, cu=250):
    minimum = scipy.optimize.fmin(total_cost_maintenance, 0.5, args=(model, cp, cu))
    return minimum

class Exponential:
    ''' 
    Exponential distribution as standard defined
    the PDF of this function is defined as:
    f(t) = lamb * exp(-lamb * t)
    '''
    def __init__(self, lamb, durations=[]):
        self.lamb = lamb
        self.durations = durations

    @classmethod
    def from_durations(cls, durations):
        hist, bin_edges = np.histogram(np.array(durations),
                                       bins=sturges_rule(len(durations)))
        normhist = hist / sum(hist)
        c_fail = np.cumsum(normhist)
        lamb = _determine_exp(bin_edges[1:], 1 - c_fail)
        return cls(lamb)


    @classmethod
    def from_durations2(cls, durations):
        from scipy.stats import expon
        param = expon.fit(durations, floc=0)
        loc, scale = param
        lamb = 1/scale
        return cls(lamb, durations)


    def __repr__(self):
        return 'Exponential: lambda {}'.format(self.lamb)

    def reliability_cdf(self, t):
        return np.exp(-self.lamb * t)

    def failure_cdf(self, t):
        return 1 - self.reliability_cdf(t)

    def failure_pdf(self, t):
        return self.lamb * np.exp(-self.lamb * t)

    def hazard_pdf(self, t):
        return self.lamb * np.ones(t.shape)

    def generate_failure_time(self):
        rn = np.random.rand()
        return 1/self.lamb * np.log(1/(1-rn))

    def return_params(self):
        return self.lamb

    def mean_time(self):
        return 1/self.lamb

    def confidence_limits(self):
        from scipy.stats import chi2
        chi2.pdf(self.durations)

class Weibull:
    '''
    Exponential distribution as standard defined
    the PDF of this function is defined as:
    f(t) = (beta/alpha) * (t/alpha)**(beta-1) * exp(-t / alpha)**beta
    '''
    def __init__(self, alpha, beta):
        self.alpha = alpha
        self.beta = beta

    def __repr__(self):
        return 'Weibull: alpha {:.2f},  beta {:.2f}'.format(self.alpha, self.beta)

    @classmethod
    def from_durations(cls, durations):
        hist, bin_edges = np.histogram(np.array(durations), 
                                       bins=sturges_rule(len(durations)))
        normhist = hist / sum(hist)
        c_fail = np.cumsum(normhist)
        alpha, beta = _determine_weibull(bin_edges[1:], 1-c_fail)
        return cls(alpha, beta)

    @classmethod
    def from_durations2(cls, durations):
        from scipy.stats import weibull_min
        param = weibull_min.fit(durations, floc=0)
        alpha = param[0]
        beta = param[2]
        return cls(alpha, beta)

    def get_t_from_reliability(self, reliability):
        return (-np.log(reliability))**(1/self.beta)*self.alpha


    def reliability_cdf(self, t):
        ''' 
        The reliability function is 
        R(t) = exp(-(t/alpha)**beta), alpha > 0, beta > 0, 
        '''
        return np.exp(-(t/self.alpha)**self.beta)

    def failure_cdf(self, t):
        return 1 - self.reliability_cdf(t)

    def failure_pdf(self, t):
        return (self.beta/self.alpha) * (t/self.alpha)**(self.beta-1) * np.exp(-(t/self.alpha)**self.beta)

    def hazard_pdf(self, t):
        t[t==0] = 0.01
        return self.beta * t**(self.beta-1) / (self.alpha**self.beta)  

    def generate_failure_time(self):
        rn = np.random.rand() # pick number from uniform distribution
        return self.alpha * np.log(1/(1-rn))**(1/self.beta)

    def return_params(self):
        return self.alpha, self.beta

    def mean_time(self):
        from scipy.special import gamma
        MTBF = self.alpha * gamma(1/self.beta + 1)
        return MTBF

    def median(self):
        mean = self.alpha * np.log(2)**(1/self.beta)
        return mean


class Lognormal:
    ''' 
    Lognormal distribution as defined
    the PDF of this function is defined as:
    f(t) = 1/(sigma * t * sqrt(2 pi) * exp(-1/2 * (ln t - mu)/ sigma)^2); t>0
    '''
    def __init__(self, sigma, mu):
        self.sigma = sigma
        self.mu = mu

    def __repr__(self):
        return 'Lognormal: sigma {:.2f}, mu {:.2f}'.format(self.sigma, self.mu)

    @classmethod
    def from_durations(cls, durations):
        param = lognorm.fit(durations, floc=0)
        sigma = param[0]
        mu = np.log(param[2])
        return cls(sigma, mu)

    from_durations2 = from_durations

    def failure_cdf(self, t):
        return lognorm.cdf(t, self.sigma, 0, np.exp(self.mu))
    
    def reliability_cdf(self, t):
        return 1 - self.failure_cdf(t)

    def failure_pdf(self, t):
        return lognorm.pdf(t, self.sigma, 0, np.exp(self.mu))

    def hazard_pdf(self, t):
        return lognorm.pdf(t, self.sigma, 0, np.exp(self.mu)) / lognorm.sf(t, self.sigma, 0, np.exp(self.mu))

    def generate_failure_time(self):
        return lognorm.rvs(self.sigma, 0, np.exp(self.mu))

    def return_params(self):
        return self.sigma, self.mu

    def mean_time(self):
        return np.exp(self.mu + 1/2 * self.sigma**2)

if __name__ == "__main__":
    print(__doc__)