import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

from etas.inversion import parameter_dict2array, expected_aftershocks


def temporal_decay_plot(
    Pmat: pd.DataFrame, 
    tau: float, 
    c: float, 
    omega: float, 
    label: str=None, 
    comparison_params: dict={},
    file_name: str="time_kernel_fit.pdf"
):
    """
    Given the Pij matrix as a pandas dataframe, and the ETAS parameters
    describing the time kernel, creates the visualisation of the fit
    of the inverted time kernel to the 'observed' branching structure.
    Optionally, given additional sets of parameters, adds lines to the 
    plot that represent other kernels.
    
    Args:
        Pmat: dataframe containing pairs of events, columns: 
            'time_distance' - the difference in time between events
            'Pij' - probability that event i triggered j
            'zeta_plus_1' - scaling factor adjusting for incompleteness
        tau: ETAS parameter
        c: ETAS parameter
        omega: ETAS parameter
        label: string labeling the data represented by Pmat and tau, c, omega
        comparison_params: a dictionary with additional parameter sets,
            key should be the label of the additional set
        file_name: path and name of the pdf file where plot is stored
            
    Returns:
        None: stores the plot as a pdf
    """
    
    time_bins = np.logspace(-4,4)
    time_bins_sizes = time_bins[1:] - time_bins[:-1]
    tmid = (time_bins[:-1] + time_bins[1:]) / 2
    time_decay = np.exp(-tmid/tau) / (tmid+c)**(1+omega)
    
    counts, _ = np.histogram(
        Pmat["time_distance"],
        bins=time_bins,
        weights=Pmat["Pij"]*Pmat["zeta_plus_1"]
    )
    
    time_decay_scaled = (time_decay/np.sum(time_decay))

    counts_scaled = counts / time_bins_sizes
    counts_scaled = counts_scaled / sum(counts_scaled)
    
    plt.figure()
    plt.plot(tmid, time_decay_scaled, label=label, zorder=10)
    plt.scatter(tmid, counts_scaled, marker=".")
    plt.axvline(tau, color="black", linestyle='dashed')
    plt.axvline(c, color="black", linestyle='dashed')
    plt.text(
        tau+1e3,
        1e-4,
        f'log10(tau)={np.round(np.log10(tau),2)}',
        rotation=90
    )
    plt.text(
        c+1e-3,
        1e-5,
        f'log10(c)={np.round(np.log10(c),2)}',
        rotation=90
    )
    
    for area_label in comparison_params:
        tau = comparison_params[area_label]["tau"]
        c = comparison_params[area_label]["c"]
        omega = comparison_params[area_label]["omega"]
    
        time_decay = np.exp(-tmid/tau) / (tmid+c)**(1+omega)
        time_decay_scaled = time_decay / np.sum(time_decay)
    
        plt.plot(tmid, time_decay_scaled, label=area_label)

    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel("\u0394 t (days)")
    plt.ylabel("PDF (time kernel)")
    plt.legend()
    plt.savefig(file_name)
    plt.close()
    
    
def productivity_plot(
    Pmat: pd.DataFrame, 
    catalog: pd.DataFrame, 
    params: dict, 
    mc: float, 
    delta_m: float, 
    label: str=None, 
    comparison_params: dict={},
    file_name: str="productivity_fit.pdf"
):
    """
    Given the Pij matrix as a pandas dataframe, and the inverted 
    ETAS parameters, creates the visualisation of the fit
    of the inverted productivity law to the 'observed' branching structure.
    Optionally, given additional sets of parameters, adds lines to the 
    plot that represent other productivities.
    
    Args:
        Pmat: dataframe containing pairs of events, columns: 
            'source_magnitude' - the magnitude of the triggering event
            'Pij' - probability that event i triggered j
            'zeta_plus_1' - scaling factor adjusting for incompleteness
        catalog: dataframe used for inversion
        params: dict with ETAS parameters
        label: string labeling the data represented by Pmat and params
        comparison_params: a dictionary with additional parameter sets,
            key should be the label of the additional set
        file_name: path and name of the pdf file where plot is stored
            
    Returns:
        None: stores the plot in 'fits' directory
    """
    
    min_mag = np.min(catalog["magnitude"])
    max_mag = np.max(catalog["magnitude"])
    magnitude_bins = np.arange(min_mag-delta_m/2, max_mag+delta_m/2, delta_m)
    magnitudes = (magnitude_bins[1:] + magnitude_bins[:-1]) / 2

    params_array = (parameter_dict2array(params)[1:], mc)
    n_expected = expected_aftershocks(magnitudes, params_array, True, True)
    
    counts, _ = np.histogram(
        Pmat["source_magnitude"],
        bins=magnitude_bins, 
        weights=Pmat["Pij"]*Pmat["zeta_plus_1"], #multiply by the time factor
    )

    # average counts wrt the number of events in each bin
    how_many, _ = np.histogram(catalog["magnitude"], magnitude_bins)
    counts_scaled = np.array(counts) / how_many
    
    plt.figure()
    plt.plot(magnitudes, n_expected, label=label, zorder=10)
    plt.scatter(magnitudes, counts_scaled, marker='.')
    
    for area_label in comparison_params:
        params = comparison_params[area_label]
        params_array = (parameter_dict2array(params)[1:], mc)
        n_expected = expected_aftershocks(magnitudes, params_array, True, True)
        plt.plot(magnitudes, n_expected, label=area_label)
    
    plt.yscale("log")
    plt.xlabel("magnitude")
    plt.ylabel("number of aftershocks")
    plt.legend()
    plt.savefig(file_name)
    plt.close()
    

def spatial_kernel(
    dist: float,
    d: float,
    gamma: float,
    rho: float,
    m: float,
    mc: float
):
    return 1 / (dist + d*np.exp(gamma*(m-mc)))**(1+rho)   

def spatial_decay_plot(
    Pmat: pd.DataFrame,
    magnitudes: list,
    d: float,
    gamma: float,
    rho: float,
    mc: float,
    label: str=None,
    comparison_params: dict={},
    file_name: str="space_kernel_fit"
):
    """
    Given the Pij matrix as a pandas dataframe, and the ETAS parameters
    describing the space kernel, creates the visualisation of the fit
    of the inverted space kernel to the 'observed' branching structure.
    Optionally, given additional sets of parameters, adds lines to the 
    plot that represent other kernels.
    
    Args:
        Pmat: dataframe containing pairs of events, columns: 
            'spatial_distance_squared' - the distance between events
            'source_magnitude' - the magnitude of the triggering event
            'Pij' - probability that event i triggered j
            'zeta_plus_1' - scaling factor adjusting for incompleteness
        magnitudes: the list of magnitudes of triggering events for which 
            plots should be generated
        d: ETAS parameter
        gamma: ETAS parameter
        rho: ETAS parameter
        mc: completeness magnitude
        label: string labeling the data represented by Pmat and d, gamma, rho
        comparison_params: a dictionary with additional parameter sets,
            key should be the label of the additional set
        file_name: path and name of the pdf file where plot is stored
            NOTE: function will add the observed magnitudes to the name
            
    Returns:
        None: stores the plot in 'fits' directory
    """

    for moi in magnitudes:
        
        Psubmat = Pmat[np.round(Pmat["source_magnitude"],1)==np.round(moi,1)]
        
        max_dist = np.sqrt(np.max(Psubmat["spatial_distance_squared"]))
        #TODO: change minimum distance?
        distance_bins = np.logspace(-1,np.log(max_dist))
        distances = (distance_bins[1:]+distance_bins[:-1])/2
        distance_bins_sizes = distance_bins[1:] - distance_bins[:-1]
        
        spatial_decay = spatial_kernel(distances, d, gamma, rho, moi, mc)
        spatial_decay_scaled = spatial_decay / np.nansum(spatial_decay)
        
        dist_emp, y = np.histogram(
            Psubmat["spatial_distance_squared"], 
            bins=distance_bins,
            weights=Psubmat["Pij"]*Psubmat["zeta_plus_1"]
        )
        dist_emp = dist_emp / distance_bins_sizes
        dist_emp_scaled = dist_emp / np.nansum(dist_emp)

        plt.plot(np.sqrt(distances), spatial_decay_scaled, label=label, zorder=10 )
        plt.scatter(np.sqrt(distances), dist_emp_scaled, marker=".")
        
        for area_label in comparison_params:
            d_area = comparison_params[area_label]["d"]
            gamma_area = comparison_params[area_label]["gamma"]
            rho_area = comparison_params[area_label]["rho"]
            
            spatial_decay = spatial_kernel(distances, d_area, gamma_area, rho_area, moi, mc)
            spatial_decay_scaled = spatial_decay / np.nansum(spatial_decay)
            plt.plot(np.sqrt(distances), spatial_decay_scaled, label=area_label)
        
        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel("distance (km)")
        plt.ylabel("PDF (space kernel)")
        plt.legend()
        plt.savefig(f"{file_name}_mag_{np.round(moi,2)}.pdf")

        plt.close()
        
        
class ETASFitVisualisation:
    def __init__(self, metadata: dict):
        self.catalog = pd.read_csv(metadata.get("fn_catalog", None))
        self.Pij = pd.read_csv(metadata.get("fn_pij", None))
        self.mc = metadata.get("mc", None)
        self.delta_m = metadata.get("delta_m", None)
        self.parameters = metadata.get("parameters", None)
        self.label = metadata.get("label", None)
        self.comparison_parameters = metadata.get("comparison_parameters", {})
        self.magnitude_list = metadata.get("magnitude_list", None)
        self.store_path = metadata.get("store_path", None)
        
        self.a, self.gamma, self.c, self.d, self.k, self.mu, self.tau, self.omega, self.rho = \
            self.parameters["a"], \
            self.parameters["gamma"], \
            np.power(10, self.parameters["log10_c"]), \
            np.power(10, self.parameters["log10_d"]), \
            np.power(10, self.parameters["log10_k0"]), \
            np.power(10, self.parameters["log10_mu"]), \
            np.power(10, self.parameters["log10_tau"]), \
            self.parameters["omega"], \
            self.parameters["rho"]
        
        comparison_params = {}
        for area_label in self.comparison_parameters:
            params = self.comparison_parameters[area_label]
            mu = np.power(10, params["log10_mu"])
            d = np.power(10, params["log10_d"])
            k = np.power(10, params["log10_k0"])
            gamma = params["gamma"]
            rho = params["rho"]
            beta = params["beta"]
            
            del_m = params["mc"] - params["delta_m"]/2 - (self.mc - self.delta_m/2)
            d = d * np.exp(del_m*gamma)
            k = k * np.exp(del_m*gamma*rho)
            mu = mu*np.exp(-del_m*beta)
            
            params["log10_mu"] = np.log10(mu)
            params["log10_d"] = np.log10(d)
            params["log10_k0"] = np.log10(k)
            
            comparison_params[area_label] = params
        self.comparison_parameters = comparison_params
        
    def time_kernel_plot(self, fn_store: str="time_kernel_fit.pdf"):
        
        comparison_params = {}
        if self.comparison_parameters is not None:
            for area_label in self.comparison_parameters:
                params = self.comparison_parameters[area_label]
                comparison_params[area_label] = {
                    "tau" : np.power(10, params["log10_tau"]),
                    "omega": params["omega"],
                    "c": np.power(10, params["log10_c"])
                }

        temporal_decay_plot(
            Pmat=self.Pij,
            tau=self.tau, 
            c=self.c, 
            omega=self.omega, 
            label=self.label,
            file_name=os.path.join(self.store_path, fn_store),
            comparison_params=comparison_params
        )
        
    def productivity_law_plot(self, fn_store: str="productivity_law_fit.pdf"):
        
        productivity_plot(
            Pmat = self.Pij,
            catalog = self.catalog, 
            params=self.parameters, 
            mc=self.mc, 
            delta_m=self.delta_m, 
            label=self.label,
            file_name=os.path.join(self.store_path, fn_store),
            comparison_params=self.comparison_parameters
        )
        
    def space_kernel_plot(self, fn_store: str="space_kernel_fit.pdf"):
        
        comparison_params = {}
        if self.comparison_parameters is not None:
            for area_label in self.comparison_parameters:
                params = self.comparison_parameters[area_label]
                comparison_params[area_label] = {
                    "d" : np.power(10, params["log10_d"]),
                    "rho": params["rho"],
                    "gamma": params["gamma"]
                }
                
        spatial_decay_plot(
            Pmat = self.Pij,
            magnitudes = self.magnitude_list, 
            d=self.d, 
            gamma=self.gamma, 
            rho=self.rho, 
            mc=self.mc,
            label=self.label,
            file_name=os.path.join(self.store_path, fn_store),
            comparison_params=comparison_params
        )
        
    def all_plots(self):
        self.time_kernel_plot()
        self.productivity_law_plot()
        self.space_kernel_plot()