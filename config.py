"""Petro-C → SiC DT Configuration"""

# === Petroleum Coke Properties ===
PETRO_COKE_GRADES = {
    "green_coke": {
        "carbon_pct": 0.88,
        "sulfur_ppm": 40000,
        "impurities_ppm": {
            "Fe": 500, "Al": 200, "Ti": 100, "Ca": 300,
            "V": 800, "Ni": 400, "Si": 500, "B": 5, "N": 8000
        },
        "ash_pct": 0.5,
        "volatile_pct": 10.0,
        "HHV_MJ_kg": 35.0,
        "price_usd_per_ton": 80.0,
    },
    "calcined_coke": {
        "carbon_pct": 0.985,
        "sulfur_ppm": 10000,
        "impurities_ppm": {
            "Fe": 200, "Al": 100, "Ti": 50, "Ca": 150,
            "V": 300, "Ni": 200, "Si": 300, "B": 3, "N": 3000
        },
        "ash_pct": 0.2,
        "volatile_pct": 0.5,
        "HHV_MJ_kg": 33.0,
        "price_usd_per_ton": 350.0,
    },
    "needle_coke": {
        "carbon_pct": 0.995,
        "sulfur_ppm": 3000,
        "impurities_ppm": {
            "Fe": 50, "Al": 30, "Ti": 20, "Ca": 40,
            "V": 50, "Ni": 30, "Si": 100, "B": 1, "N": 1000
        },
        "ash_pct": 0.05,
        "volatile_pct": 0.3,
        "HHV_MJ_kg": 33.5,
        "price_usd_per_ton": 1500.0,
    },
}

# === Target Purity ===
PURITY_GRADES = {
    "metallurgical": {"total_impurity_ppm": 10000, "label": "2N"},
    "chemical": {"total_impurity_ppm": 1000, "label": "3N"},
    "electronic": {"total_impurity_ppm": 100, "label": "4N"},
    "semiconductor": {"total_impurity_ppm": 10, "label": "5N"},
    "ultra_semiconductor": {"total_impurity_ppm": 1, "label": "6N"},
}

# === Acid Leaching Parameters ===
ACID_LEACH = {
    "HCl": {
        "conc_mol_L": 6.0,
        "T_range_C": (60, 90),
        "removal_eff": {"Fe": 0.85, "Ca": 0.90, "Al": 0.70, "Ni": 0.80},
        "D0_m2_s": 1e-9,
        "Ea_diffusion_kJ_mol": 20.0,
        "acid_order": 1.0,
    },
    "HF": {
        "conc_mol_L": 2.0,
        "T_range_C": (25, 60),
        "removal_eff": {"Si": 0.95, "Ti": 0.75, "Al": 0.85},
        "D0_m2_s": 1.5e-9,
        "Ea_diffusion_kJ_mol": 18.0,
        "acid_order": 0.8,
    },
    "HNO3": {
        "conc_mol_L": 4.0,
        "T_range_C": (60, 80),
        "removal_eff": {"V": 0.90, "Ni": 0.85, "Fe": 0.75},
        "D0_m2_s": 1.2e-9,
        "Ea_diffusion_kJ_mol": 22.0,
        "acid_order": 1.2,
    },
    "HCl_HF_mix": {
        "conc_mol_L": (4.0, 1.0),
        "T_range_C": (60, 80),
        "removal_eff": {
            "Fe": 0.92, "Al": 0.88, "Si": 0.90, "Ca": 0.88,
            "Ti": 0.80, "V": 0.85, "Ni": 0.82
        },
        "D0_m2_s": 1.3e-9,
        "Ea_diffusion_kJ_mol": 19.0,
        "acid_order": 1.0,
    },
}

# === Halogen Purification ===
HALOGEN_PURIFY = {
    "Cl2": {
        "T_range_C": (1500, 2000),
        "flow_rate_L_min": (0.5, 5.0),
        "removal_eff_at_1800C": {
            "Fe": 0.995, "Al": 0.99, "Ti": 0.98, "Ca": 0.99,
            "V": 0.97, "B": 0.90, "N": 0.60
        },
        "energy_kWh_per_kg": 15.0,
    },
    "HCl_gas": {
        "T_range_C": (1200, 1800),
        "flow_rate_L_min": (1.0, 10.0),
        "removal_eff_at_1500C": {
            "Fe": 0.98, "Al": 0.97, "Ti": 0.95, "Ca": 0.97,
            "V": 0.93, "B": 0.85, "N": 0.50
        },
        "energy_kWh_per_kg": 12.0,
    },
}

# === Thermodynamic data for metal chlorides ===
# ΔG(T) ≈ ΔH - T·ΔS  (linear approximation, kJ/mol)
METAL_CHLORIDE_THERMO = {
    "Fe": {"delta_H_kJ": -399.0, "delta_S_kJ_K": -0.130, "Ea_kJ_mol": 150.0, "A_s": 1e7, "n_Cl2": 1.5, "alpha": 1.0, "beta": 0.67},
    "Al": {"delta_H_kJ": -704.0, "delta_S_kJ_K": -0.180, "Ea_kJ_mol": 180.0, "A_s": 5e7, "n_Cl2": 1.5, "alpha": 1.0, "beta": 0.67},
    "Ti": {"delta_H_kJ": -804.0, "delta_S_kJ_K": -0.200, "Ea_kJ_mol": 200.0, "A_s": 2e7, "n_Cl2": 2.0, "alpha": 1.0, "beta": 0.67},
    "Ca": {"delta_H_kJ": -795.0, "delta_S_kJ_K": -0.150, "Ea_kJ_mol": 120.0, "A_s": 1e8, "n_Cl2": 1.0, "alpha": 1.0, "beta": 0.67},
    "V":  {"delta_H_kJ": -580.0, "delta_S_kJ_K": -0.170, "Ea_kJ_mol": 190.0, "A_s": 3e7, "n_Cl2": 2.0, "alpha": 1.0, "beta": 0.67},
    "Ni": {"delta_H_kJ": -305.0, "delta_S_kJ_K": -0.110, "Ea_kJ_mol": 160.0, "A_s": 8e6, "n_Cl2": 1.0, "alpha": 1.0, "beta": 0.67},
    "B":  {"delta_H_kJ": -427.0, "delta_S_kJ_K": -0.140, "Ea_kJ_mol": 220.0, "A_s": 1e6, "n_Cl2": 1.5, "alpha": 0.8, "beta": 0.67},
    "N":  {"delta_H_kJ": -100.0, "delta_S_kJ_K": -0.050, "Ea_kJ_mol": 280.0, "A_s": 5e5, "n_Cl2": 0.5, "alpha": 0.5, "beta": 0.50},
    "Si": {"delta_H_kJ": -687.0, "delta_S_kJ_K": -0.190, "Ea_kJ_mol": 210.0, "A_s": 1e7, "n_Cl2": 2.0, "alpha": 1.0, "beta": 0.67},
}

# === Thermal Treatment ===
THERMAL = {
    "pyrolysis_Ea_kJ_mol": 180.0,
    "pyrolysis_A_s": 1e12,
    "pyrolysis_n": 1.5,
    "carbon_density_kg_m3": 1600.0,
    "carbon_Cp_J_kgK": 1200.0,
    "carbon_k_W_mK": 5.0,
    "avrami_k0_s": 1e6,
    "avrami_Ea_kJ_mol": 300.0,
    "avrami_n": 2.5,
}

# === Acheson Process ===
ACHESON = {
    "reaction": "SiO2 + 3C -> SiC + 2CO",
    "delta_H_kJ_mol": 618.5,
    "T_core_C": 2700,
    "T_shell_C": 1800,
    "activation_energy_kJ_mol": 250,
    "pre_exponential_s": 1e8,
    "energy_kWh_per_kg_SiC": 8.5,
    "cycle_time_hours": 36,
    "yield_fraction": 0.35,
    "SiO2_to_C_molar_ratio": 1.0 / 3.0,
    "CO_generation_mol_per_mol_SiC": 2.0,
    # Molar masses (g/mol)
    "M_SiO2": 60.08,
    "M_C": 12.01,
    "M_SiC": 40.10,
    "M_CO": 28.01,
    # Furnace geometry defaults
    "default_length_m": 4.0,
    "default_radius_m": 0.8,
    "default_core_radius_m": 0.1,
    # Material properties of charge mix
    "charge_density_kg_m3": 1200.0,
    "charge_Cp_J_kgK": 1000.0,
    "charge_k_W_mK": 2.0,
    "charge_porosity": 0.40,
    # Graphite core resistivity
    "graphite_rho0_ohm_m": 1e-5,
    "graphite_alpha_K": 5e-4,
}

# === Physical Constants ===
R_GAS = 8.314  # J/(mol·K)
BOLTZMANN = 1.381e-23  # J/K

# === Energy Costs by Region ($/kWh) ===
ENERGY_COSTS = {
    "saudi_arabia": 0.048,
    "usa_average": 0.075,
    "usa_industrial": 0.068,
    "eu_average": 0.120,
    "china_industrial": 0.058,
    "japan_industrial": 0.095,
    "saudi_solar_ppa": 0.015,
}

# === Electrification Toggle ===
ELECTRIFICATION_OPTIONS = {
    "acid_leach_heating": {"conventional": "steam", "electric": "electric_heater", "energy_ratio": 0.85},
    "halogen_furnace": {"conventional": "resistance", "electric": "resistance", "energy_ratio": 1.0},
    "acheson_furnace": {"conventional": "resistance", "electric": "resistance", "energy_ratio": 1.0},
    "thermal_treatment": {"conventional": "gas_fired", "electric": "microwave", "energy_ratio": 0.70},
    "drying": {"conventional": "gas_fired", "electric": "infrared", "energy_ratio": 0.80},
    "sublimation": {"conventional": "resistance", "electric": "induction", "energy_ratio": 0.90},
    "pvt_growth": {"conventional": "resistance", "electric": "resistance", "energy_ratio": 1.0},
    "wafering": {"conventional": "mechanical", "electric": "mechanical", "energy_ratio": 1.0},
    "cmp": {"conventional": "mechanical", "electric": "mechanical", "energy_ratio": 1.0},
}

# === M06: Sublimation Purification ===
# Ref: Lilov (2003), Drowart et al., J. Mass Spectrom. (2005)
SUBLIMATION = {
    "alpha_evap": 0.5,                 # Evaporation coefficient (0.1-1, SiC ~0.5)
    "T_range_C": (2000, 2400),         # Sublimation temperature range
    "energy_kWh_per_kg_h": 25.0,       # Specific energy at ~2200°C
    # Vapor species thermodynamic data: ln(P/Pa) = A - B/T(K)
    # Ref: Lilov, Materials Science and Engineering B100 (2003) 16-22
    "vapor_species": {
        "Si":   {"A": 27.2, "B": 52800, "molar_mass": 28.09},
        "Si2C": {"A": 30.1, "B": 63400, "molar_mass": 68.18},
        "SiC2": {"A": 29.5, "B": 60100, "molar_mass": 64.13},
    },
    # Burton-Prim-Slichter impurity segregation
    # Ref: Burton, Prim, Slichter, J. Chem. Phys. 21 (1953) 1987
    "impurity_k0": {  # Equilibrium partition coefficients
        "Fe": 1e-5, "Al": 1e-4, "Ti": 2e-5, "Ca": 5e-5,
        "V": 1e-5, "Ni": 8e-6, "B": 0.8, "N": 0.5,
        "Si": 1.0,
    },
    "D_liquid_m2_s": 5e-9,   # Diffusivity in melt/vapor
    "delta_BPS_m": 1e-4,     # Boundary layer thickness
}

# === M07: PVT Crystal Growth ===
# Ref: Wellmann (2018) Cryst. Res. Technol., Kimoto & Cooper (2014) textbook
PVT_GROWTH = {
    "T_source_range_C": (2100, 2300),
    "T_seed_range_C": (2000, 2200),
    "T_gradient_typical_K_cm": 10.0,    # Typical axial gradient
    "P_Ar_range_mbar": (5, 50),
    "stefan_boltzmann": 5.67e-8,         # W/(m²·K⁴)
    "emissivity_SiC": 0.9,
    "emissivity_graphite": 0.85,
    # Binary diffusivities at 2200°C, 20 mbar [m²/s]
    # Ref: Wellmann (2018)
    "D_binary_m2_s": {
        "Si_Ar": 5e-4, "Si2C_Ar": 3e-4, "SiC2_Ar": 3.5e-4,
        "Si_Si2C": 2e-4, "Si_SiC2": 2.5e-4, "Si2C_SiC2": 1.5e-4,
    },
    # 4H-SiC material properties
    "E_Young_GPa": 448,                # Young's modulus
    "poisson_ratio": 0.21,
    "CTE_K": 4.3e-6,                   # Coefficient of thermal expansion
    "k_thermal_SiC_W_mK": 490,         # Thermal conductivity (RT)
    "density_SiC_kg_m3": 3210,
    "M_SiC_g_mol": 40.10,
    # Typical growth rate parameters
    "growth_rate_prefactor": 0.02,      # mm/h per K of ΔT (empirical)
    "growth_rate_P_factor": -0.005,     # mm/h per mbar Ar above 20 mbar
    # Defect correlation coefficients (empirical)
    # Ref: Kimoto & Cooper, "Fundamentals of SiC Technology" (2014)
    "BPD_base_cm2": 100,               # Base BPD at v=0.2 mm/h, σ=10 MPa
    "BPD_growth_rate_exp": 1.5,        # BPD ∝ v^1.5
    "BPD_stress_exp": 2.0,             # BPD ∝ σ^2
    "TSD_to_BPD_ratio": 0.1,           # TSD typically ~10% of BPD
    # Energy
    "energy_kWh_per_h_150mm": 50.0,    # Power consumption for 150mm furnace
    "energy_kWh_per_h_200mm": 80.0,    # Power consumption for 200mm furnace
}

# === M08: Wafering & CMP ===
# Ref: Ciszek (2004), Zhu et al., Precision Engineering (2005)
WAFERING = {
    # Diamond wire saw parameters
    "wire_diameter_mm": 0.12,          # Standard diamond wire
    "abrasive_size_mm": 0.015,         # Diamond grit size
    "wafer_thickness_mm": 0.35,        # Standard 4H-SiC wafer
    "TTV_um": 5.0,                     # Total thickness variation
    # CMP parameters
    # Ref: Zhu et al., Precision Engineering (2005)
    "preston_kp": {                    # Preston coefficient [m²/N] by slurry
        "alumina": 1e-13,
        "colloidal_silica": 3e-14,
        "diamond": 5e-13,
        "cmp_SiC": 2e-14,             # SiC-specific CMP slurry
    },
    "cmp_pressure_kPa": 30.0,
    "cmp_velocity_m_s": 1.5,
    "initial_Ra_nm": 200.0,            # After grinding
    "target_Ra_nm": 0.5,               # Epi-ready
    # Roughness evolution: Ra(t) = Ra_0·exp(-k·t) + Ra_final
    "roughness_k_per_min": {
        "alumina": 0.02,
        "colloidal_silica": 0.05,
        "diamond": 0.01,
        "cmp_SiC": 0.03,
    },
    # Costs ($/wafer for processing steps)
    "wire_saw_cost_per_wafer": 5.0,
    "grinding_cost_per_wafer": 3.0,
    "cmp_cost_per_min": 0.50,
    "slurry_cost_per_L": {"alumina": 20, "colloidal_silica": 50, "diamond": 200, "cmp_SiC": 80},
    "slurry_consumption_L_per_min": 0.01,
}

# === M09: SiC Power Device ===
# Ref: Baliga, "Fundamentals of Power Semiconductor Devices" (2008)
SIC_DEVICE = {
    # Material properties for Baliga FOM
    "materials": {
        "Si": {
            "bandgap_eV": 1.12, "E_c_MV_cm": 0.3, "mu_cm2_Vs": 1400,
            "epsilon_r": 11.7, "k_thermal_W_mK": 150, "label": "Si",
        },
        "4H-SiC": {
            "bandgap_eV": 3.26, "E_c_MV_cm": 2.0, "mu_cm2_Vs": 900,
            "epsilon_r": 9.7, "k_thermal_W_mK": 490, "label": "4H-SiC",
        },
        "GaN": {
            "bandgap_eV": 3.4, "E_c_MV_cm": 3.3, "mu_cm2_Vs": 1250,
            "epsilon_r": 9.0, "k_thermal_W_mK": 130, "label": "GaN",
        },
    },
    "epsilon_0_F_m": 8.854e-12,
    # Typical 1200V SiC MOSFET
    "V_BR_V": 1200,
    "R_ch_mohm_cm2": 2.0,              # Channel resistance
    "R_sub_mohm_cm2": 0.5,             # Substrate resistance
    # Switching times (ns)
    "t_on_ns": 20, "t_off_ns": 30,
    # AIDC rack parameters
    "aidc_rack_power_kW": 40.0,        # AI training rack ~40kW
    "aidc_n_racks": 1000,
    "hours_per_year": 8760,
    # Device cost learning curve
    # Ref: Yole Développement (2023)
    "die_yield_150mm": 0.65,
    "die_yield_200mm": 0.55,
    "die_area_mm2": 25.0,
    "device_packaging_cost": 2.0,      # $/device
}

# === M10: LCA & Economics ===
# Ref: IRENA (2022), IEA (2023), Saudi Vision 2030
LCA_ECON = {
    # Grid emission factors (kg CO₂/kWh)
    # Ref: IEA Emission Factors (2023)
    "emission_factors": {
        "saudi_arabia": 0.58,
        "usa_average": 0.39,
        "eu_average": 0.23,
        "china_industrial": 0.55,
    },
    # Electrification scenario multipliers on emission factor
    "electrification_scenarios": {
        "current": 1.0,                 # Current grid
        "grid_electric": 0.7,          # Grid decarbonization (~2030)
        "solar_electric": 0.05,        # Direct solar PV + storage
    },
    # COGS categories ($/wafer default)
    "cogs_default": {
        "raw_materials": 15.0,
        "energy": 80.0,
        "equipment_depreciation": 120.0,
        "labor": 30.0,
        "consumables": 25.0,
        "overhead": 20.0,
    },
    # Regional cost multipliers (relative to Saudi)
    "regional_multipliers": {
        "saudi_arabia": {"energy": 1.0, "labor": 1.0, "capex": 1.1},
        "usa": {"energy": 1.56, "labor": 2.5, "capex": 1.3},
        "eu": {"energy": 2.50, "labor": 3.0, "capex": 1.4},
        "china": {"energy": 1.21, "labor": 0.4, "capex": 0.8},
    },
    # Default NPV parameters
    "discount_rate": 0.10,
    "project_years": 15,
    "capex_M_usd": 500,                # $500M fab
    "wafers_per_year": 100000,          # 100k 150mm wafer/year
}
