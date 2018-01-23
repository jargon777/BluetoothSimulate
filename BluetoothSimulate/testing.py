'''
Created on Jan 16, 2018

@author: Matthew Muresan
'''


def main():
    try:
        S = 1950
        te = 15
        g = 40
        c = 90
        d = float(input("Give d? "))
        print(golden_section_flowrate(S, te, g, c, d))
    except:
        raise
    finally:
        pass

def golden_section_flowrate(S, te, g, c, d):
    tol = 0.05 # delay inaccuracy tolerance, seconds
    X = 0 #we vary X to find a matching d value
    p_a = flowrate_estimate(S, te, g, c, d, X)
    #short turn if demand is lower than the zero value
    if d <= p_a["dt"]: return {"X": 0.1, "Y":(0.1*p_a["Cap"])/S}
    X = 2
    p_b = flowrate_estimate(S, te, g, c, d, X)
    if d >= p_b["dt"]: return {"X": 2.0, "Y":(2.0*p_b["Cap"])/S}
    
    gr = (5**0.5 + 1) / 2
    
    X = p_b["X"] - (p_b["X"] - p_a["X"]) / gr
    p_c = flowrate_estimate(S, te, g, c, d, X)
    
    X = p_a["X"] + (p_b["X"] - p_a["X"]) / gr
    p_d = flowrate_estimate(S, te, g, c, d, X)
    while abs(p_d["Dev"]) > tol:
        if abs(p_c["Dev"]) < abs(p_d["Dev"]):
            p_b = p_d
        else:
            p_a = p_c
        
        X = p_b["X"] - (p_b["X"] - p_a["X"]) / gr
        p_c = flowrate_estimate(S, te, g, c, d, X)
    
        X = p_a["X"] + (p_b["X"] - p_a["X"]) / gr
        p_d = flowrate_estimate(S, te, g, c, d, X)
    
    return p_d #return the overestimated value of the tolerance bound.
        
    
def flowrate_estimate(S, te, g, c, d, X):
    #determine the saturation flow rate given some values
    ge = g+1
    X1 = X if X <= 1 else 1
    Cap = S * ge/c
    d1 = c*((1-ge/c)**2)/((2*(1-X1*ge/c)))
    d2 = ((X-1)+(((X-1)**2)+(240*X)/(Cap*te))**0.5)*15*te
    dt = d1+d2
    dem =  Cap * X
    return {"X": X, "Y":dem/S, "dt": dt, "Cap": Cap, "Dev": dt-d, "Dem": dem}
    
if __name__ == "__main__":
    main()