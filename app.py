#!/usr/bin/env python3
"""
Aramco Petro-C → SiC Digital Twin
Streamlit Web Application

A comprehensive digital twin for the petroleum coke to silicon carbide transformation process.
Covers 10 process stages from feedstock selection to device performance and economics.
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import os
from typing import Dict, List, Optional, Any

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))
sys.path.insert(0, os.path.dirname(__file__))

# Import configuration and modules
try:
    import config
    from modules import (
        m01_feedstock, m02_acid_leach, m03_halogen_purify, m04_thermal,
        m05_acheson, m06_sublimation, m07_pvt_growth, m08_wafering,
        m09_device, m10_lca_econ
    )
except ImportError as e:
    st.error(f"Failed to import modules: {e}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="Petro-C → SiC Digital Twin",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean styling
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Application header
st.title("🏭 Aramco Petro-C → SiC Digital Twin")
st.markdown("*Digital transformation of petroleum coke to silicon carbide for AIDC power electronics*")
st.markdown("---")

# Initialize session state
if 'impurity_tracking' not in st.session_state:
    st.session_state.impurity_tracking = {}
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = {}

def run_complete_simulation(grade: str, region: str, electrification: bool) -> Dict:
    """Run end-to-end simulation through all 10 modules."""
    results = {}
    
    try:
        # M01: Feedstock selection
        feedstock_props = m01_feedstock.select_feedstock(grade)
        results['feedstock'] = feedstock_props
        
        # M02: Acid leaching
        leach_results = m02_acid_leach.multi_acid_leach(
            feedstock_props['impurities_ppm'],
            'HCl',
            80.0,
            3600.0
        )
        results['acid_leach'] = leach_results
        
        # M03: Halogen purification
        halogen_results = m03_halogen_purify.purify_halogen(
            leach_results.get('final_impurities', feedstock_props['impurities_ppm']),
            1800
        )
        results['halogen'] = halogen_results
        
        # M04: Thermal treatment
        thermal_results = m04_thermal.thermal_treatment(mass_kg=10.0, T_max_C=1200)
        results['thermal'] = thermal_results
        
        # M05: Acheson synthesis
        acheson_results = m05_acheson.acheson_full_cycle(charge_mass_kg=500.0)
        results['acheson'] = acheson_results
        
        # M06: Sublimation
        sublim_results = m06_sublimation.sublimation_purify(
            leach_results.get('final_impurities', feedstock_props['impurities_ppm']),
            T_C=2400, duration_h=10.0
        )
        results['sublimation'] = sublim_results
        
        # M07: PVT growth
        pvt_results = m07_pvt_growth.pvt_simulation(2200, 2000, 800.0, 10.0)
        results['pvt_growth'] = pvt_results
        
        # M08: Wafering
        wafering_results = m08_wafering.cmp_process()
        results['wafering'] = wafering_results
        
        # M09: Device performance
        device_results = m09_device.baliga_fom()
        results['device'] = device_results
        
        # M10: LCA & Economics
        lca_results = m10_lca_econ.regional_comparison()
        results['lca_economics'] = lca_results
        
        return results
        
    except Exception as e:
        st.error(f"Error in simulation: {e}")
        return {}

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Region Selection
    region = st.selectbox(
        "🌍 Region",
        options=['Saudi', 'USA', 'EU', 'China'],
        index=0,
        help="Geographic region for cost and energy analysis"
    )
    
    # Electrification Option
    electrification = st.toggle(
        "⚡ Electrification",
        value=True,
        help="Enable renewable energy sources"
    )
    
    # Feedstock Grade Selection
    feedstock_grade = st.selectbox(
        "🛢️ Feedstock Grade",
        options=['green_coke', 'calcined_coke', 'needle_coke'],
        index=1,
        help="Initial petroleum coke grade"
    )
    
    st.markdown("---")
    
    # End-to-end simulation button
    if st.button("🚀 Run End-to-End Simulation", type="primary"):
        with st.spinner("Running complete simulation..."):
            try:
                # Run all modules in sequence
                results = run_complete_simulation(feedstock_grade, region, electrification)
                st.session_state.simulation_results = results
                st.success("✅ Simulation completed!")
            except Exception as e:
                st.error(f"❌ Simulation failed: {e}")

# Main content tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "1️⃣ Feedstock",
    "2️⃣ Acid Leaching", 
    "3️⃣ Halogen Purif.",
    "4️⃣ Thermal Treat.",
    "5️⃣ Acheson Synth.",
    "6️⃣ Sublimation",
    "7️⃣ PVT Growth",
    "8️⃣ Wafering",
    "9️⃣ Device Bench.",
    "🔟 LCA & Economics"
])

# Tab 1: Feedstock
with tab1:
    st.header("🛢️ Petroleum Coke Feedstock Characterization")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Grade Selection")
        selected_grade = st.radio(
            "Choose feedstock grade:",
            options=['green_coke', 'calcined_coke', 'needle_coke'],
            index=['green_coke', 'calcined_coke', 'needle_coke'].index(feedstock_grade),
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Get feedstock properties
        try:
            props = m01_feedstock.select_feedstock(selected_grade)
            
            st.metric("Carbon Content", f"{props['carbon_pct']:.1%}")
            st.metric("Sulfur Content", f"{props['sulfur_ppm']:,} ppm")
            st.metric("Total Impurities", f"{m01_feedstock.total_impurity_ppm(props['impurities_ppm']):,.0f} ppm")
            st.metric("Price", f"${props['price_usd_per_ton']:.0f}/ton")
            
        except Exception as e:
            st.error(f"Error loading feedstock data: {e}")
    
    with col2:
        st.subheader("Impurity Profile")
        
        if 'props' in locals():
            # Create impurity bar chart
            impurities = props['impurities_ppm']
            elements = list(impurities.keys())
            concentrations = list(impurities.values())
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(elements, concentrations, color='steelblue', alpha=0.7)
            ax.set_ylabel('Concentration (ppm)')
            ax.set_title('Impurity Profile by Element')
            ax.set_yscale('log')
            
            # Add value labels on bars
            for bar, val in zip(bars, concentrations):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.0f}', ha='center', va='bottom')
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
    
    # Purification path analysis
    st.subheader("Purification Path Analysis")
    
    target_grade = st.selectbox(
        "Target purity grade:",
        options=['metallurgical', 'chemical', 'electronic', 'semiconductor', 'ultra_semiconductor'],
        index=2
    )
    
    if st.button("Calculate Purification Path"):
        try:
            path = m01_feedstock.calculate_purification_path(props['impurities_ppm'], target_grade)
            stages = m01_feedstock.estimate_purification_stages(props['impurities_ppm'], target_grade)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Required Stages", f"{stages['n_stages']}")
                st.metric("Current Total", f"{stages['current_total_ppm']:,.0f} ppm")
                st.metric("Target Total", f"{stages['target_total_ppm']:,.0f} ppm")
            
            with col2:
                # Create purification path table
                path_df = pd.DataFrame([
                    {
                        'Element': el,
                        'Current (ppm)': data['current_ppm'],
                        'Target (ppm)': data['max_allowed_ppm'],
                        'Removal Required': f"{data['required_removal_frac']:.1%}"
                    }
                    for el, data in path.items()
                ])
                st.dataframe(path_df, hide_index=True)
                
        except Exception as e:
            st.error(f"Error calculating purification path: {e}")

# Tab 2: Acid Leaching
with tab2:
    st.header("⚗️ Acid Leaching Process")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Process Parameters")
        
        # Temperature control
        temp_c = st.slider(
            "Temperature (°C)",
            min_value=40,
            max_value=100,
            value=80,
            step=5
        )
        
        # Acid selection
        acid_type = st.selectbox(
            "Acid Type",
            options=['HCl', 'HF', 'HNO3', 'HCl_HF_mix'],
            help="Select acid for leaching process"
        )
        
        # Particle size
        particle_size = st.slider(
            "Particle Radius (μm)",
            min_value=1.0,
            max_value=100.0,
            value=50.0,
            step=1.0
        )
        
        # Time range for kinetics
        max_time = st.slider(
            "Simulation Time (hours)",
            min_value=1,
            max_value=24,
            value=8,
            step=1
        )
    
    with col2:
        st.subheader("Leaching Kinetics")
        
        try:
            # Calculate leaching kinetics
            particle_r_m = particle_size * 1e-6  # Convert μm to m
            
            # Get leaching rate
            rate_result = m02_acid_leach.shrinking_core_model(temp_c, acid_type, particle_r_m)
            tau = rate_result['tau_complete_s']
            
            # Generate time series for conversion
            time_hours = np.linspace(0, max_time, 100)
            time_seconds = time_hours * 3600
            conversions = [m02_acid_leach.shrinking_core_conversion(tau, t) for t in time_seconds]
            
            # Plot conversion vs time
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(time_hours, [c*100 for c in conversions], 'b-', linewidth=2)
            ax.set_xlabel('Time (hours)')
            ax.set_ylabel('Conversion (%)')
            ax.set_title(f'Leaching Kinetics - {acid_type} at {temp_c}°C')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Display metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Complete Conv. Time", f"{tau/3600:.1f} hours")
            with col_b:
                st.metric("Rate Constant", f"{rate_result.get('k_eff', 0):.2e}")
            with col_c:
                final_conversion = conversions[-1] if conversions else 0
                st.metric(f"Conversion @ {max_time}h", f"{final_conversion*100:.1f}%")
            
        except Exception as e:
            st.error(f"Error in leaching calculation: {e}")
    
    # Multi-acid sequence
    st.subheader("Multi-Acid Sequential Treatment")
    
    if st.button("Run Multi-Acid Sequence"):
        try:
            # Use current feedstock impurities
            if 'props' in locals():
                initial_impurities = props['impurities_ppm']
            else:
                # Fallback to selected feedstock
                initial_props = m01_feedstock.select_feedstock(feedstock_grade)
                initial_impurities = initial_props['impurities_ppm']
            
            sequence_results = m02_acid_leach.multi_acid_leach(
                initial_impurities,
                'HCl',
                temp_c,
                3600.0
            )
            
            # Display results table
            results_df = pd.DataFrame([
                {
                    'Stage': f"After {acid}",
                    **{el: f"{conc:.1f}" for el, conc in imp.items()}
                }
                for acid, imp in zip(['Initial'] + ['HCl', 'HF', 'HNO3'], 
                                   [initial_impurities] + sequence_results['stage_impurities'])
            ])
            
            st.dataframe(results_df, hide_index=True)
            
            # Update impurity tracking
            st.session_state.impurity_tracking['acid_leach'] = sequence_results['final_impurities']
            
        except Exception as e:
            st.error(f"Error in multi-acid sequence: {e}")

# Tab 3: Halogen Purification
with tab3:
    st.header("🌪️ Halogen Purification Process")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Process Parameters")
        
        # Temperature
        temp_halogen = st.slider(
            "Temperature (°C)",
            min_value=1400,
            max_value=2200,
            value=1800,
            step=50
        )
        
        # Cl2 flow rate
        cl2_flow = st.slider(
            "Cl₂ Flow Rate (L/min)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.1
        )
        
        # Process time
        process_time = st.slider(
            "Process Time (minutes)",
            min_value=10,
            max_value=120,
            value=30,
            step=5
        )
    
    with col2:
        st.subheader("Gibbs Free Energy vs Temperature")
        
        try:
            # Plot Gibbs energy for key metals
            temps_K = np.linspace(1400 + 273.15, 2200 + 273.15, 50)
            temps_C = temps_K - 273.15
            
            metals = ['Fe', 'Al', 'Ti', 'Ca']
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for metal in metals:
                try:
                    gibbs_values = [m03_halogen_purify.gibbs_free_energy(metal, T) for T in temps_K]
                    ax.plot(temps_C, gibbs_values, label=metal, linewidth=2)
                except:
                    pass
            
            ax.set_xlabel('Temperature (°C)')
            ax.set_ylabel('Gibbs Free Energy (kJ/mol)')
            ax.set_title('Gibbs Free Energy vs Temperature')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
        except Exception as e:
            st.error(f"Error plotting Gibbs energy: {e}")
    
    # Multi-element purification
    st.subheader("Multi-Element Purification Results")
    
    if st.button("Run Halogen Purification"):
        try:
            # Use impurities from previous stage or feedstock
            if 'acid_leach' in st.session_state.impurity_tracking:
                input_impurities = st.session_state.impurity_tracking['acid_leach']
            elif 'props' in locals():
                input_impurities = props['impurities_ppm']
            else:
                initial_props = m01_feedstock.select_feedstock(feedstock_grade)
                input_impurities = initial_props['impurities_ppm']
            
            # Run full halogen purification
            halogen_results = m03_halogen_purify.purify_halogen(
                input_impurities, temp_halogen, cl2_flow, process_time
            )
            
            # Display removal efficiency
            removal_eff = halogen_results['removal_efficiency']
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Removal Efficiency")
                eff_df = pd.DataFrame([
                    {'Element': el, 'Removal %': f"{eff*100:.1f}%"}
                    for el, eff in removal_eff.items()
                ])
                st.dataframe(eff_df, hide_index=True)
            
            with col_b:
                st.subheader("Final Concentrations")
                final_conc = halogen_results['final_concentrations']
                conc_df = pd.DataFrame([
                    {'Element': el, 'Final (ppm)': f"{conc:.2f}"}
                    for el, conc in final_conc.items()
                ])
                st.dataframe(conc_df, hide_index=True)
            
            # Update impurity tracking
            st.session_state.impurity_tracking['halogen'] = final_conc
            
            # Energy consumption
            total_energy = halogen_results.get('total_energy_kWh', 0)
            st.metric("Energy Consumption", f"{total_energy:.1f} kWh")
            
        except Exception as e:
            st.error(f"Error in halogen purification: {e}")

# Tab 4: Thermal Treatment
with tab4:
    st.header("🔥 Thermal Treatment Process")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Process Parameters")
        
        # Temperature
        temp_thermal = st.slider(
            "Temperature (°C)",
            min_value=800,
            max_value=1600,
            value=1200,
            step=50
        )
        
        # Time
        time_thermal = st.slider(
            "Treatment Time (hours)",
            min_value=0.5,
            max_value=8.0,
            value=2.0,
            step=0.5
        )
        
        # Sample thickness
        thickness = st.slider(
            "Sample Thickness (mm)",
            min_value=1.0,
            max_value=50.0,
            value=10.0,
            step=1.0
        )
    
    with col2:
        st.subheader("Avrami Crystallinity Evolution")
        
        try:
            # Generate time series for Avrami model
            time_range = np.linspace(0, time_thermal, 100) * 3600  # Convert to seconds
            T_K = temp_thermal + 273.15
            
            crystallinities = [m04_thermal.crystallinity_evolution(T_K, t) for t in time_range]
            time_hours_plot = time_range / 3600
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(time_hours_plot, [c*100 for c in crystallinities], 'r-', linewidth=2)
            ax.set_xlabel('Time (hours)')
            ax.set_ylabel('Crystallinity (%)')
            ax.set_title(f'Avrami Crystallinity Evolution at {temp_thermal}°C')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Show final crystallinity
            final_crystallinity = crystallinities[-1] if crystallinities else 0
            st.metric("Final Crystallinity", f"{final_crystallinity*100:.1f}%")
            
        except Exception as e:
            st.error(f"Error in crystallinity calculation: {e}")
    
    # 1D Thermal Profile
    st.subheader("1D Temperature Profile")
    
    if st.button("Calculate Thermal Profile"):
        try:
            profile_results = m04_thermal.heat_conduction_1d(
                temp_thermal, time_thermal, thickness/1000  # Convert mm to m
            )
            
            positions = profile_results['positions_m']
            temperatures = profile_results['final_temps_C']
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot([p*1000 for p in positions], temperatures, 'b-', linewidth=2)
            ax.set_xlabel('Position (mm)')
            ax.set_ylabel('Temperature (°C)')
            ax.set_title(f'Temperature Profile after {time_thermal} hours')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Show temperature gradient
            temp_gradient = (max(temperatures) - min(temperatures))
            st.metric("Temperature Gradient", f"{temp_gradient:.1f}°C")
            
        except Exception as e:
            st.error(f"Error calculating thermal profile: {e}")

# Tab 5: Acheson Synthesis
with tab5:
    st.header("⚡ Acheson Furnace Synthesis")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Furnace Parameters")
        
        # Power
        power_kW = st.slider(
            "Power (kW)",
            min_value=100,
            max_value=1000,
            value=500,
            step=50
        )
        
        # Process time
        time_acheson = st.slider(
            "Process Time (hours)",
            min_value=2,
            max_value=12,
            value=4,
            step=1
        )
        
        # Furnace length
        length = st.slider(
            "Furnace Length (m)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5
        )
    
    with col2:
        st.subheader("Temperature & Conversion Profile")
        
        try:
            # Run Acheson simulation
            acheson_results = m05_acheson.acheson_full_cycle(power_kW, time_acheson, length)
            
            positions = acheson_results['positions_m']
            final_temps = acheson_results['final_temps_C']
            conversions = acheson_results['conversions']
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
            
            # Temperature profile
            ax1.plot(positions, final_temps, 'r-', linewidth=2)
            ax1.set_ylabel('Temperature (°C)')
            ax1.set_title('Acheson Furnace - Temperature Profile')
            ax1.grid(True, alpha=0.3)
            
            # Conversion profile
            ax2.plot(positions, [c*100 for c in conversions], 'b-', linewidth=2)
            ax2.set_xlabel('Position (m)')
            ax2.set_ylabel('Conversion (%)')
            ax2.set_title('SiC Conversion Profile')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Show metrics
            max_temp = max(final_temps)
            avg_conversion = np.mean(conversions) * 100
            total_energy = acheson_results.get('total_energy_kWh', power_kW * time_acheson)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Max Temperature", f"{max_temp:.0f}°C")
            with col_b:
                st.metric("Avg Conversion", f"{avg_conversion:.1f}%")
            with col_c:
                st.metric("Energy Used", f"{total_energy:.0f} kWh")
            
        except Exception as e:
            st.error(f"Error in Acheson simulation: {e}")
    
    # Gibbs energy vs temperature
    st.subheader("Thermodynamic Analysis")
    
    if st.button("Show Gibbs Energy Analysis"):
        try:
            temps_range = np.linspace(1000, 2500, 100)
            temps_K = temps_range + 273.15
            
            gibbs_values = [m05_acheson.sic_formation_rate(T) for T in temps_K]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(temps_range, gibbs_values, 'g-', linewidth=2)
            ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
            ax.set_xlabel('Temperature (°C)')
            ax.set_ylabel('Gibbs Free Energy (kJ/mol)')
            ax.set_title('SiC Formation - Gibbs Free Energy vs Temperature')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
        except Exception as e:
            st.error(f"Error in thermodynamic analysis: {e}")

# Tab 6: Sublimation
with tab6:
    st.header("💨 Sublimation Purification")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Process Parameters")
        
        # Temperature
        temp_sublim = st.slider(
            "Temperature (°C)",
            min_value=2000,
            max_value=2800,
            value=2400,
            step=50
        )
        
        # Pressure
        pressure_mbar = st.slider(
            "Pressure (mbar)",
            min_value=1.0,
            max_value=50.0,
            value=10.0,
            step=1.0
        )
        
        # Process time
        time_sublim = st.slider(
            "Process Time (hours)",
            min_value=0.5,
            max_value=4.0,
            value=1.0,
            step=0.1
        )
    
    with col2:
        st.subheader("Vapor Pressure Analysis")
        
        try:
            # Plot vapor pressure for different species
            temps_range = np.linspace(2000, 2800, 100)
            temps_K = temps_range + 273.15
            
            species = ['SiC', 'Si', 'C']
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for spec in species:
                try:
                    vapor_pressures = [m06_sublimation.sic_vapor_species(spec, T) for T in temps_K]
                    ax.semilogy(temps_range, vapor_pressures, label=spec, linewidth=2)
                except:
                    pass
            
            ax.set_xlabel('Temperature (°C)')
            ax.set_ylabel('Vapor Pressure (Pa)')
            ax.set_title('Vapor Pressure vs Temperature')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
        except Exception as e:
            st.error(f"Error plotting vapor pressure: {e}")
    
    # BPS Segregation Analysis
    st.subheader("Boiling Point Separation (BPS)")
    
    if st.button("Run Sublimation Purification"):
        try:
            # Run sublimation purification
            sublim_results = m06_sublimation.sublimation_purify(
                temp_sublim, pressure_mbar, time_sublim
            )
            
            # Display results
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Separation Efficiency")
                efficiency = sublim_results.get('separation_efficiency', {})
                if efficiency:
                    eff_df = pd.DataFrame([
                        {'Component': comp, 'Separation %': f"{eff*100:.1f}%"}
                        for comp, eff in efficiency.items()
                    ])
                    st.dataframe(eff_df, hide_index=True)
            
            with col_b:
                st.subheader("Process Metrics")
                purity_gain = sublim_results.get('purity_increase', 0)
                energy_consumption = sublim_results.get('energy_kWh', 0)
                
                st.metric("Purity Gain", f"{purity_gain*100:.2f}%")
                st.metric("Energy Used", f"{energy_consumption:.1f} kWh")
            
            # BPS segregation details
            if 'bps_results' in sublim_results:
                st.subheader("BPS Segregation Results")
                bps_data = sublim_results['bps_results']
                
                fig, ax = plt.subplots(figsize=(10, 6))
                components = list(bps_data.keys())
                separations = [bps_data[c].get('separation_factor', 0) for c in components]
                
                ax.bar(components, separations, color='skyblue', alpha=0.7)
                ax.set_ylabel('Separation Factor')
                ax.set_title('BPS Separation Factors')
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            
        except Exception as e:
            st.error(f"Error in sublimation process: {e}")

# Tab 7: PVT Crystal Growth
with tab7:
    st.header("💎 PVT Crystal Growth")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Growth Parameters")
        
        # Source temperature
        T_source = st.slider(
            "Source Temperature (°C)",
            min_value=1800,
            max_value=2400,
            value=2200,
            step=25
        )
        
        # Seed temperature
        T_seed = st.slider(
            "Seed Temperature (°C)",
            min_value=1600,
            max_value=2200,
            value=2000,
            step=25
        )
        
        # Argon pressure
        P_Ar = st.slider(
            "Argon Pressure (mbar)",
            min_value=100,
            max_value=1500,
            value=800,
            step=50
        )
        
        # Growth time
        growth_time = st.slider(
            "Growth Time (hours)",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
    
    with col2:
        st.subheader("Growth Rate vs Temperature Gradient")
        
        try:
            # Calculate growth rate
            growth_rate = m07_pvt_growth.growth_rate(T_source, T_seed, P_Ar)
            
            # Plot growth rate vs temperature gradient
            temp_gradients = np.linspace(50, 400, 50)
            growth_rates = []
            
            for dT in temp_gradients:
                T_src_temp = T_seed + dT
                try:
                    rate = m07_pvt_growth.growth_rate(T_src_temp, T_seed, P_Ar)
                    growth_rates.append(rate)
                except:
                    growth_rates.append(0)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(temp_gradients, growth_rates, 'purple', linewidth=2)
            ax.axvline(x=T_source-T_seed, color='r', linestyle='--', 
                      label=f'Current ΔT = {T_source-T_seed}°C')
            ax.set_xlabel('Temperature Gradient (°C)')
            ax.set_ylabel('Growth Rate (mm/h)')
            ax.set_title('PVT Growth Rate vs Temperature Gradient')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Display current growth rate
            st.metric("Current Growth Rate", f"{growth_rate:.2f} mm/h")
            
        except Exception as e:
            st.error(f"Error calculating growth rate: {e}")
    
    # Defect density analysis
    st.subheader("Growth Quality Analysis")
    
    if st.button("Run PVT Growth Simulation"):
        try:
            # Run full PVT simulation
            pvt_results = m07_pvt_growth.pvt_simulation(
                T_source, T_seed, P_Ar, growth_time
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Growth Results")
                
                crystal_thickness = pvt_results.get('final_thickness_mm', 0)
                growth_rate_actual = pvt_results.get('average_growth_rate_mm_h', 0)
                
                st.metric("Crystal Thickness", f"{crystal_thickness:.1f} mm")
                st.metric("Average Growth Rate", f"{growth_rate_actual:.2f} mm/h")
            
            with col_b:
                st.subheader("Defect Analysis")
                
                defect_density = pvt_results.get('defect_density_cm2', 0)
                crystal_quality = pvt_results.get('quality_grade', 'Unknown')
                
                st.metric("Defect Density", f"{defect_density:.0f} cm⁻²")
                st.metric("Quality Grade", crystal_quality)
            
            # Growth profile over time
            if 'time_profile' in pvt_results:
                st.subheader("Growth Profile")
                
                time_data = pvt_results['time_profile']['time_h']
                thickness_data = pvt_results['time_profile']['thickness_mm']
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(time_data, thickness_data, 'b-', linewidth=2)
                ax.set_xlabel('Time (hours)')
                ax.set_ylabel('Crystal Thickness (mm)')
                ax.set_title('PVT Crystal Growth Profile')
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            
        except Exception as e:
            st.error(f"Error in PVT simulation: {e}")

# Tab 8: Wafering & CMP
with tab8:
    st.header("🪚 Wafering & CMP Process")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("CMP Parameters")
        
        # Slurry selection
        slurry_type = st.selectbox(
            "CMP Slurry",
            options=['colloidal_silica', 'alumina', 'diamond', 'cmp_SiC'],
            help="Choose CMP slurry type"
        )
        
        # Pressure (kPa)
        pressure_kPa = st.slider(
            "Pressure (kPa)",
            min_value=5.0,
            max_value=60.0,
            value=30.0,
            step=5.0
        )
        
        # Velocity
        velocity_m_s = st.slider(
            "Velocity (m/s)",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1
        )
        
        # Polish time
        polish_time = st.slider(
            "Polish Time (minutes)",
            min_value=5,
            max_value=60,
            value=30,
            step=5
        )
        
        # Wafer diameter
        wafer_diameter = st.slider(
            "Wafer Diameter (mm)",
            min_value=100,
            max_value=300,
            value=150,
            step=25
        )
    
    with col2:
        st.subheader("Material Removal Rate (MRR)")
        
        try:
            # Look up Preston coefficient for selected slurry
            from config import WAFERING as WAF_CFG
            k_p = WAF_CFG["preston_kp"].get(slurry_type, 3e-14)
            
            # Calculate MRR using Preston equation
            mrr = m08_wafering.preston_mrr(
                k_p, pressure_kPa, velocity_m_s
            )
            
            # Plot MRR vs pressure and velocity
            pressures = np.linspace(5, 60, 20)
            velocities = np.linspace(0.1, 2.0, 20)
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # MRR vs Pressure
            mrr_vs_p = [m08_wafering.preston_mrr(k_p, p, velocity_m_s) 
                       for p in pressures]
            ax1.plot(pressures, mrr_vs_p, 'b-', linewidth=2)
            ax1.axvline(x=pressure_kPa, color='r', linestyle='--', 
                       label=f'Current = {pressure_kPa} kPa')
            ax1.set_xlabel('Pressure (kPa)')
            ax1.set_ylabel('MRR (μm/min)')
            ax1.set_title('MRR vs Pressure')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # MRR vs Velocity
            mrr_vs_v = [m08_wafering.preston_mrr(k_p, pressure_kPa, v) 
                       for v in velocities]
            ax2.plot(velocities, mrr_vs_v, 'g-', linewidth=2)
            ax2.axvline(x=velocity_m_s, color='r', linestyle='--', 
                       label=f'Current = {velocity_m_s} m/s')
            ax2.set_xlabel('Velocity (m/s)')
            ax2.set_ylabel('MRR (μm/min)')
            ax2.set_title('MRR vs Velocity')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Display current MRR
            st.metric("Material Removal Rate", f"{mrr:.3f} μm/min")
            
        except Exception as e:
            st.error(f"Error calculating MRR: {e}")
    
    # Surface roughness evolution
    st.subheader("Surface Roughness Evolution")
    
    if st.button("Run CMP Simulation"):
        try:
            # Run full wafering process
            wafering_results = m08_wafering.cmp_process(
                wafer_diameter, polish_time/60, slurry_type  # Convert minutes to hours
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Process Results")
                
                final_roughness = wafering_results.get('final_roughness_nm', 0)
                total_removal = wafering_results.get('total_removal_um', 0)
                
                st.metric("Final Roughness", f"{final_roughness:.1f} nm")
                st.metric("Material Removed", f"{total_removal:.1f} μm")
            
            with col_b:
                st.subheader("Process Metrics")
                
                process_cost = wafering_results.get('process_cost_usd', 0)
                efficiency = wafering_results.get('process_efficiency', 0)
                
                st.metric("Process Cost", f"${process_cost:.2f}")
                st.metric("Efficiency", f"{efficiency:.1%}")
            
            # Roughness evolution plot
            if 'roughness_profile' in wafering_results:
                time_data = wafering_results['roughness_profile']['time_min']
                roughness_data = wafering_results['roughness_profile']['roughness_nm']
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(time_data, roughness_data, 'orange', linewidth=2)
                ax.set_xlabel('Time (minutes)')
                ax.set_ylabel('Surface Roughness (nm)')
                ax.set_title('CMP Surface Roughness Evolution')
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            
        except Exception as e:
            st.error(f"Error in CMP simulation: {e}")

# Tab 9: Device Benchmarking
with tab9:
    st.header("📱 Device Performance Benchmarking")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Device Parameters")
        
        # Material selection
        device_material = st.selectbox(
            "Semiconductor Material",
            options=['Si', '4H-SiC', '6H-SiC', 'GaN'],
            index=1,
            help="Select semiconductor material"
        )
        
        # Operating conditions
        operating_voltage = st.slider(
            "Operating Voltage (V)",
            min_value=100,
            max_value=10000,
            value=1200,
            step=100
        )
        
        operating_current = st.slider(
            "Operating Current (A)",
            min_value=1,
            max_value=100,
            value=20,
            step=1
        )
        
        switching_freq = st.slider(
            "Switching Frequency (kHz)",
            min_value=1,
            max_value=100,
            value=20,
            step=1
        )
    
    with col2:
        st.subheader("Baliga Figure of Merit Comparison")
        
        try:
            # Get BFOM for all materials
            bfom_results = m09_device.baliga_fom()
            
            materials = list(bfom_results.keys())
            fom_values = [bfom_results[mat]['FOM_normalized'] for mat in materials]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(materials, fom_values, color=['blue', 'red', 'green', 'orange'])
            
            # Highlight selected material
            if device_material in materials:
                idx = materials.index(device_material)
                bars[idx].set_color('darkred')
                bars[idx].set_alpha(0.8)
            
            ax.set_ylabel('Normalized Baliga FOM')
            ax.set_title('Baliga Figure of Merit Comparison')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, val in zip(bars, fom_values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.1f}', ha='center', va='bottom')
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
        except Exception as e:
            st.error(f"Error in BFOM calculation: {e}")
    
    # Material comparison table
    st.subheader("Detailed Material Comparison")
    
    if st.button("Generate Material Comparison"):
        try:
            # Get detailed properties for each material
            comparison_data = []
            materials = ['Si', '4H-SiC', '6H-SiC', 'GaN']
            
            for mat in materials:
                try:
                    bfom_data = m09_device.baliga_fom(mat)
                    ron_data = m09_device.mosfet_losses(mat, operating_voltage)
                    
                    comparison_data.append({
                        'Material': mat,
                        'Bandgap (eV)': bfom_data[mat].get('bandgap_eV', 0),
                        'Mobility (cm²/V·s)': bfom_data[mat].get('mobility_cm2_V_s', 0),
                        'Critical Field (MV/cm)': bfom_data[mat].get('critical_field_MV_cm', 0),
                        'BFOM (normalized)': bfom_data[mat].get('FOM_normalized', 0),
                        'R_on (mΩ·cm²)': ron_data.get('R_on_specific_mohm_cm2', 0)
                    })
                except:
                    pass
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, hide_index=True)
            
        except Exception as e:
            st.error(f"Error generating comparison: {e}")
    
    # AIDC Energy Savings
    st.subheader("AIDC Data Center Energy Savings")
    
    if st.button("Calculate AIDC Savings"):
        try:
            # Calculate energy savings for AIDC application
            aidc_savings = m09_device.aidc_power_savings(
                device_material, 
                operating_voltage, 
                operating_current,
                switching_freq * 1000  # Convert to Hz
            )
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Power Savings", f"{aidc_savings.get('power_savings_W', 0):.1f} W")
            
            with col_b:
                annual_savings = aidc_savings.get('annual_energy_savings_kWh', 0)
                st.metric("Annual Energy Savings", f"{annual_savings:.0f} kWh")
            
            with col_c:
                cost_savings = aidc_savings.get('cost_savings_usd', 0)
                st.metric("Annual Cost Savings", f"${cost_savings:.0f}")
            
            # Efficiency comparison
            if 'efficiency_comparison' in aidc_savings:
                eff_data = aidc_savings['efficiency_comparison']
                
                fig, ax = plt.subplots(figsize=(10, 6))
                
                scenarios = list(eff_data.keys())
                efficiencies = [eff_data[s]*100 for s in scenarios]
                
                ax.bar(scenarios, efficiencies, color='lightgreen', alpha=0.7)
                ax.set_ylabel('Efficiency (%)')
                ax.set_title('Power Conversion Efficiency Comparison')
                ax.grid(True, alpha=0.3, axis='y')
                ax.set_ylim(90, 100)
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            
        except Exception as e:
            st.error(f"Error calculating AIDC savings: {e}")

# Tab 10: LCA & Economics
with tab10:
    st.header("💰 Life Cycle Assessment & Economics")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Analysis Parameters")
        
        # Use region from sidebar
        st.write(f"**Selected Region:** {region}")
        st.write(f"**Electrification:** {'Enabled' if electrification else 'Disabled'}")
        
        # Production scale
        production_scale = st.selectbox(
            "Production Scale",
            options=['pilot', 'commercial', 'industrial'],
            index=1,
            help="Production scale for economic analysis"
        )
        
        # Analysis period
        analysis_years = st.slider(
            "Analysis Period (years)",
            min_value=5,
            max_value=25,
            value=10,
            step=5
        )
        
        # Carbon price
        carbon_price = st.slider(
            "Carbon Price ($/tonne CO₂)",
            min_value=0,
            max_value=200,
            value=50,
            step=10
        )
    
    with col2:
        st.subheader("Regional Cost Comparison")
        
        try:
            # Get regional comparison
            regional_results = m10_lca_econ.regional_comparison(region, electrification)
            
            # Plot COGS breakdown
            if 'cogs_breakdown' in regional_results:
                cogs_data = regional_results['cogs_breakdown']
                
                categories = list(cogs_data.keys())
                costs = list(cogs_data.values())
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.pie(costs, labels=categories, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'COGS Breakdown - {region}')
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            
        except Exception as e:
            st.error(f"Error in regional analysis: {e}")
    
    # Energy waterfall
    st.subheader("Energy Consumption Waterfall")
    
    if st.button("Generate Energy Analysis"):
        try:
            # Define typical energy consumption by stage
            stage_energies = {
                'Feedstock Prep': 5.0,
                'Acid Leaching': 15.0,
                'Halogen Purification': 25.0,
                'Thermal Treatment': 20.0,
                'Acheson Synthesis': 150.0,
                'Sublimation': 45.0,
                'PVT Growth': 35.0,
                'Wafering': 8.0
            }
            
            # Adjust for electrification
            if electrification:
                stage_energies = {k: v * 0.8 for k, v in stage_energies.items()}  # 20% reduction
            
            # Create waterfall chart
            cumulative_energy = 0
            energy_data = []
            cumulative_data = []
            
            for stage, energy in stage_energies.items():
                energy_data.append(energy)
                cumulative_energy += energy
                cumulative_data.append(cumulative_energy)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            stages = list(stage_energies.keys())
            
            # Create waterfall bars
            bottom = 0
            colors = plt.cm.viridis(np.linspace(0, 1, len(stages)))
            
            for i, (stage, energy) in enumerate(stage_energies.items()):
                ax.bar(stage, energy, bottom=bottom, color=colors[i], alpha=0.7, 
                      edgecolor='black', linewidth=0.5)
                
                # Add value label
                ax.text(stage, bottom + energy/2, f'{energy:.0f}', 
                       ha='center', va='center', fontweight='bold')
                
                bottom += energy
            
            ax.set_ylabel('Energy Consumption (kWh/wafer)')
            ax.set_title('Process Energy Waterfall')
            ax.grid(True, alpha=0.3, axis='y')
            plt.xticks(rotation=45, ha='right')
            
            # Add total line
            ax.axhline(y=cumulative_energy, color='red', linestyle='--', 
                      label=f'Total: {cumulative_energy:.0f} kWh/wafer')
            ax.legend()
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Show totals
            st.metric("Total Energy per Wafer", f"{cumulative_energy:.0f} kWh")
            
        except Exception as e:
            st.error(f"Error generating energy analysis: {e}")
    
    # CO₂ emissions analysis
    st.subheader("Carbon Footprint Analysis")
    
    if st.button("Calculate CO₂ Emissions"):
        try:
            # Calculate CO₂ emissions
            co2_results = m10_lca_econ.co2_emissions(region, electrification, production_scale)
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Emissions by Source")
                
                total_co2 = co2_results.get('total_co2_kg_wafer', 0)
                energy_co2 = co2_results.get('energy_co2_kg_wafer', 0)
                transport_co2 = co2_results.get('transport_co2_kg_wafer', 0)
                
                st.metric("Total CO₂", f"{total_co2:.1f} kg/wafer")
                st.metric("Energy CO₂", f"{energy_co2:.1f} kg/wafer")
                st.metric("Transport CO₂", f"{transport_co2:.1f} kg/wafer")
            
            with col_b:
                st.subheader("Emissions Breakdown")
                
                # Create stacked bar chart
                categories = ['Energy', 'Transport', 'Other']
                values = [
                    energy_co2,
                    transport_co2,
                    total_co2 - energy_co2 - transport_co2
                ]
                
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(['Total'], [total_co2], color='lightcoral')
                
                # Stacked components
                bottom = 0
                colors = ['red', 'orange', 'gray']
                for i, (cat, val) in enumerate(zip(categories, values)):
                    if val > 0:
                        ax.bar(['Components'], [val], bottom=bottom, 
                              color=colors[i], alpha=0.7, label=cat)
                        bottom += val
                
                ax.set_ylabel('CO₂ Emissions (kg/wafer)')
                ax.set_title('Carbon Footprint Breakdown')
                ax.legend()
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            
        except Exception as e:
            st.error(f"Error calculating CO₂ emissions: {e}")
    
    # NPV Analysis
    st.subheader("Net Present Value Analysis")
    
    if st.button("Run NPV Analysis"):
        try:
            # Run NPV analysis
            npv_results = m10_lca_econ.npv_irr(
                region, electrification, analysis_years, production_scale
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Financial Metrics")
                
                npv = npv_results.get('npv_usd', 0)
                irr = npv_results.get('irr_percent', 0)
                payback = npv_results.get('payback_years', 0)
                
                st.metric("Net Present Value", f"${npv/1e6:.1f}M")
                st.metric("Internal Rate of Return", f"{irr:.1f}%")
                st.metric("Payback Period", f"{payback:.1f} years")
            
            with col_b:
                st.subheader("Cash Flow Profile")
                
                if 'cash_flows' in npv_results:
                    years = npv_results['cash_flows']['years']
                    flows = npv_results['cash_flows']['flows_usd']
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Color code positive/negative flows
                    colors = ['green' if f >= 0 else 'red' for f in flows]
                    ax.bar(years, [f/1e6 for f in flows], color=colors, alpha=0.7)
                    
                    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                    ax.set_xlabel('Year')
                    ax.set_ylabel('Cash Flow ($M)')
                    ax.set_title('Annual Cash Flow Profile')
                    ax.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
            
        except Exception as e:
            st.error(f"Error in NPV analysis: {e}")

# Impurity tracking across stages
if st.session_state.impurity_tracking:
    st.markdown("---")
    st.subheader("🔬 Impurity Tracking Across Process Stages")
    
    # Create impurity progression chart
    stages = list(st.session_state.impurity_tracking.keys())
    if len(stages) > 1:
        # Get all elements
        all_elements = set()
        for stage_impurities in st.session_state.impurity_tracking.values():
            all_elements.update(stage_impurities.keys())
        
        # Create DataFrame for plotting
        tracking_data = []
        for stage in stages:
            stage_impurities = st.session_state.impurity_tracking[stage]
            total_impurities = sum(stage_impurities.values())
            tracking_data.append({
                'Stage': stage.replace('_', ' ').title(),
                'Total Impurities (ppm)': total_impurities
            })
        
        if tracking_data:
            tracking_df = pd.DataFrame(tracking_data)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(tracking_df['Stage'], tracking_df['Total Impurities (ppm)'], 
                   'o-', linewidth=2, markersize=8, color='red')
            ax.set_yscale('log')
            ax.set_ylabel('Total Impurities (ppm)')
            ax.set_title('Impurity Reduction Through Process Stages')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

# Display simulation results summary
if st.session_state.simulation_results:
    st.markdown("---")
    st.subheader("📊 End-to-End Simulation Summary")
    
    results = st.session_state.simulation_results
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Calculate total energy (simplified)
        total_energy = 300  # Typical value, could be calculated from results
        st.metric("Total Energy", f"{total_energy:.0f} kWh/wafer")
    
    with col2:
        # Calculate total CO₂ (simplified)
        total_co2 = total_energy * 0.5  # Typical conversion factor
        if electrification:
            total_co2 *= 0.3  # Much lower with renewable energy
        st.metric("Total CO₂", f"{total_co2:.1f} kg/wafer")
    
    with col3:
        # Estimated COGS (simplified)
        base_cogs = 150
        region_multiplier = {'Saudi': 0.8, 'USA': 1.0, 'EU': 1.2, 'China': 0.9}
        estimated_cogs = base_cogs * region_multiplier.get(region, 1.0)
        st.metric("Est. COGS", f"${estimated_cogs:.0f}/wafer")
    
    with col4:
        # Simplified NPV indicator
        npv_indicator = "Positive" if region in ['Saudi', 'China'] else "Marginal"
        st.metric("NPV Outlook", npv_indicator)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🏭 Aramco Petro-C → SiC Digital Twin | Built with Streamlit</p>
    <p><em>Advanced process modeling for petroleum coke to silicon carbide transformation</em></p>
</div>
""", unsafe_allow_html=True)