"""Calibration data for the three-region, three-income-group model.

Every value carries its source. Values marked ASSUMPTION are not taken from a
published table; they are set within ranges reported by the cited source or,
where no source exists, chosen by the authors and varied in the Monte Carlo.
Regions: 0 = advanced economies (ADV), 1 = emerging and middle-income (EME),
2 = low-income developing countries (LIC).
Income groups within each region: 0 = bottom 50%, 1 = middle 40%, 2 = top 10%.
"""
import numpy as np

REGIONS = ["ADV", "EME", "LIC"]
GROUPS = ["Bottom 50%", "Middle 40%", "Top 10%"]
GROUP_POP = np.array([0.50, 0.40, 0.10])

START_YEAR, END_YEAR = 2026, 2046

CAL = {
    # Share of world GDP at market exchange rates. ASSUMPTION, approximate IMF WEO 2025 aggregates.
    "gdp_share": np.array([0.57, 0.40, 0.03]),
    # Share of world adult population. ASSUMPTION, approximate UN WPP 2024 by income group.
    "pop_share": np.array([0.14, 0.70, 0.16]),
    # Labour income share of GDP. ILO: high income 55.4% (2024), low income about 38.5%;
    # global 52.4-52.6%. EME value ASSUMPTION consistent with the global average.
    "labshare0": np.array([0.554, 0.50, 0.385]),
    # Baseline real GDP growth without the AI wave. ASSUMPTION, approximate IMF WEO
    # medium-term projections (world about 3.1% in 2026).
    "g_base": np.array([0.016, 0.040, 0.045]),
    # Labour supply growth (hours), start and end of horizon. Derived from UN WPP medium
    # variant changes in ages 20-64, 2020-2050 (high income -46m, middle +592m, low +440m).
    "ls_g_start": np.array([-0.002, 0.006, 0.026]),
    "ls_g_end": np.array([-0.004, 0.002, 0.023]),
    # Share of employment exposed to AI. IMF SDN/2024/001 (Cazzaniga et al.): 60%, 40%, 26%.
    "exposure": np.array([0.60, 0.40, 0.26]),
    # Pre-tax income shares by group. WIR 2022: Europe top 10% 36%, East Asia 43%, Latin
    # America 55%, MENA 58%; bottom 50% below 15% everywhere except Europe, below 10% in
    # Sub-Saharan Africa. Regional blends are ASSUMPTIONS within these ranges.
    "inc_share": np.array([[0.17, 0.43, 0.40],
                           [0.12, 0.40, 0.48],
                           [0.09, 0.36, 0.55]]),
    # Wealth shares by group. WIR 2022: top 10% hold 60-80% in every region, bottom 50%
    # under 5%; Europe 58/38/4. Regional values ASSUMPTIONS within these ranges.
    "wealth_share": np.array([[0.04, 0.34, 0.62],
                              [0.03, 0.27, 0.70],
                              [0.02, 0.23, 0.75]]),
    # Average propensity to consume out of disposable income. Fisher et al. (2020): US income
    # quintiles 0.974, 0.741, 0.629, 0.542, 0.475 (2013), mapped to groups; EME shifted down
    # (higher household saving), LIC up. Shifts are ASSUMPTIONS.
    "apc": np.array([[0.85, 0.58, 0.40],
                     [0.80, 0.53, 0.35],
                     [0.90, 0.63, 0.45]]),
    # Government revenue, % GDP. IMF DataMapper ADV 36.3% (2025); EME 26% and LIC 15% are
    # proxies (IMF Fiscal Monitor series for EMMIEs; Sub-Saharan Africa 19.6%, low-income Asia 13%).
    "rev_gdp": np.array([0.363, 0.26, 0.15]),
    # Composition of revenue: labour-linked, capital-linked, consumption. ADV from OECD
    # Revenue Statistics 2025 (SSC 25.5% + three quarters of PIT 23.7% = 43%; CIT 11.9% +
    # property 5.1% + capital part of PIT = 23%; consumption and other 34%). EME and LIC
    # ASSUMPTIONS reflecting heavier reliance on consumption taxes.
    "rev_mix": np.array([[0.43, 0.23, 0.34],
                         [0.25, 0.25, 0.50],
                         [0.15, 0.25, 0.60]]),
    # Gross public debt, % GDP, 2025. IMF Fiscal Monitor April 2026: 108.0, 75.3, 48.2.
    "debt0": np.array([1.080, 0.753, 0.482]),
    # Primary balance, % GDP. Overall balance 2025 (Fiscal Monitor Apr 2026): -4.4, -6.1, -2.8,
    # less an interest bill ASSUMED at about 2.8, 2.6, 2.0% of GDP.
    "primary0": np.array([-0.016, -0.035, -0.008]),
    # Real interest rate on public debt. ASSUMPTION; varied +/-1 pp in Monte Carlo.
    "r_real": np.array([0.006, 0.010, 0.015]),
    # Public pension spending, % GDP. OECD 8.1% (2024, Pensions at a Glance 2025); EME and LIC
    # ASSUMPTIONS. Annual drift from ageing ASSUMED (OECD projects 8.8-10% by 2050).
    "pension0": np.array([0.081, 0.040, 0.012]),
    "pension_drift": np.array([0.0007, 0.0008, 0.0002]),
    # Structural unemployment rate. ASSUMPTION.
    "u_star": np.array([0.05, 0.055, 0.06]),
    # Unemployment support: coverage and replacement rate. ASSUMPTION.
    "ub_cov": np.array([0.40, 0.15, 0.05]),
    "ub_rep": np.array([0.50, 0.40, 0.30]),
    # Retained share of after-tax profits. ASSUMPTION.
    "retained": np.array([0.40, 0.45, 0.40]),
    # Capital-output ratio for initial wealth. ASSUMPTION.
    "k_y": np.array([3.0, 3.0, 2.5]),
    # Distribution of transfers across groups: pensions, unemployment support. ASSUMPTION.
    "pension_dist": np.array([0.40, 0.45, 0.15]),
    "ub_dist": np.array([0.60, 0.40, 0.00]),
}

# Uncertain behavioural and technology parameters: (low, high, source / justification).
PRIORS = {
    "theta": (0.25, 0.70, "Share of substitutable exposed tasks automated by 2046. Eloundou et al. (Science 2024): 1.8% of jobs have >50% of tasks exposed with simple interfaces, up to 46% with complementary software; McKinsey Global Institute (2023): midpoint scenario automates about half of all work activities by 2045 (upper end). Lower bound raised from 0.15: a 20-year horizon with widening exposure makes very low adoption implausible."),
    "phi_s": (0.40, 0.70, "Substitution share of exposed employment. IMF SDN/2024/001: in advanced economies 33 of 60 points are high exposure with low complementarity (0.55)."),
    "mid_adv": (2030.0, 2040.0, "Year of fastest adoption in advanced economies. ASSUMPTION; diffusion literature (Comin and Hobijn 2010) shows faster adoption for newer technologies."),
    "k_slope": (0.25, 0.60, "Steepness of the adoption curve. ASSUMPTION."),
    "lag_eme": (1.0, 5.0, "Adoption lag of EME behind ADV, years. ASSUMPTION, Comin and Hobijn (2010)."),
    "lag_lic": (3.0, 10.0, "Adoption lag of LIC behind ADV, years. ASSUMPTION, Comin and Hobijn (2010)."),
    "psi": (0.25, 0.85, "Reinstatement: new human tasks per unit of AI displacement. Acemoglu and Restrepo (2019): 0.47/0.48 = 1.0 in 1947-87, 0.35/0.70 = 0.5 in 1987-2017. Centred on the most recent period (0.5); full offset (1.0) excluded because AI is closer to automation than to augmentation innovation (Acemoglu 2025; Autor et al. 2024)."),
    "lag_new": (4.0, 10.0, "Years before new tasks appear. ASSUMPTION; productivity J-curve (Brynjolfsson, Rock and Syverson 2021) and the slow emergence of new work titles (Autor et al. 2024). Lower bound raised from 2: near-immediate reinstatement has no historical support."),
    "d0": (0.0010, 0.0035, "Non-AI annual erosion of labour task content. ILO global labour share -0.15%/yr (2004-24); Acemoglu and Restrepo net -0.35%/yr (US 1987-2017)."),
    "pi_save": (0.15, 0.45, "Cost saving on automated tasks. Acemoglu (2025): 27% average labour cost saving."),
    "mu": (0.00, 0.30, "Productivity gain on augmented (complementary) tasks. Brynjolfsson, Li and Raymond: 14% average, 34% for novices."),
    "beta_w": (0.30, 1.00, "Pass-through of productivity growth to wage growth. ASSUMPTION."),
    "kappa": (0.05, 0.50, "Wage response to unemployment gap (wage Phillips slope, pp of wage growth per pp of unemployment gap). US: about 0.45 in 1991-2008, 0.14 (not significant) in 2009-2015 (Federal Reserve Bank of San Francisco, Economic Letter 2017-30); flattening after 2008 across ten advanced economies (Bank of Canada SDP 2019-8). Range widened to include rigid wages."),
    "eps": (0.15, 0.75, "Constant-output own-wage elasticity of labour demand. Hamermesh (1993, Labor Demand): best estimate about 0.30, range 0.15-0.75; Lichter, Peichl and Siegloch (2015, European Economic Review) meta-analysis: mean about 0.25."),
    "rent_share": (0.00, 0.30, "Share of AI-induced labour-share loss recouped by workers through bargaining or profit-sharing, status quo. ASSUMPTION."),
    "eta": (0.00, 1.00, "Elasticity of investment to the profit share. ASSUMPTION; profit-led vs wage-led demand literature."),
    "nu": (0.30, 1.00, "Net pass-through of an AI-induced demand shortfall to output, after monetary and fiscal offsets. ASSUMPTION."),
    "zeta": (0.20, 0.60, "Share of AI-induced capital income in EME/LIC booked in ADV. ASSUMPTION; concentration of frontier AI firms."),
    "exp_mult": (1.00, 1.60, "Growth of the exposed share of employment by 2046 as capabilities and robotics advance (1 = today's IMF exposure). ASSUMPTION; industrial robot stock +9%/yr (IFR 2025)."),
    "omega": (0.00, 0.05, "Unmeasured consumer welfare from AI services at full adoption, % of consumption. ASSUMPTION; used only in welfare-adjusted results."),
    "dr": (-0.01, 0.01, "Shift in real interest rates on public debt. ASSUMPTION."),
}
PARAM_NAMES = list(PRIORS.keys())

CENTRAL = {k: (v[0] + v[1]) / 2 for k, v in PRIORS.items()}
