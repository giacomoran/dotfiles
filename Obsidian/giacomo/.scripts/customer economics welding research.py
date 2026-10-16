"""
Welding contractor and buyer economics by geography.
Computes all-in welder cost, contractor billable rate, implied margins,
and cobot break-even analysis for US, EU (Germany as benchmark), and Italy.

Data sources are cited inline. All figures are as of 2024-2025 unless noted.
"""

# ---------------------------------------------------------------------------
# Geography parameters
# ---------------------------------------------------------------------------

# US wage data from BLS OEWS May 2024 (SOC 51-4121)
# https://www.onetonline.org/link/summary/51-4121.00 citing BLS 2024
US_WELDER_MEDIAN_HOURLY = 24.52      # USD, median hourly wage
US_WELDER_MEAN_HOURLY   = 27.50      # USD, mean hourly (approximated from BLS 2024 range; OOH reports mean ~$27-28)
US_WELDER_P90_ANNUAL    = 75_850     # USD, 90th percentile annual
US_WELDER_P10_ANNUAL    = 38_130     # USD, 10th percentile annual

# US employer burden: BLS ECEC shows benefits avg ~43% on top of wages for private-sector
# production workers. A $25/hr welder costs ~$42.59 all-in (cited from search results).
# Using 42% burden rate as a round, well-sourced estimate.
US_EMPLOYER_BURDEN_RATE = 0.42       # fraction on top of gross wage

# Germany welder wages (Glassdoor/erieri 2024, confirmed by multiple salary sites)
# Range €35k-€58k/yr; mean ~€48k/yr; ~€23/hr gross
DE_WELDER_ANNUAL_EUR    = 48_714     # EUR/yr gross (erieri.com 2024)
DE_WELDER_HOURLY_EUR    = 23.0       # EUR/hr gross (derived: 48714 / 2118 standard annual hours)
# Germany employer social security: ~21% employer share of gross wage (pension 9.3%,
# health 7.3%, nursing 1.7%, unemployment 1.3%, accident ~1.14%)
# Source: Germany social security contribution data 2024, multiple payroll sources
DE_EMPLOYER_SS_RATE     = 0.21       # fraction on top of gross wage
# Germany also has no mandatory 13th/14th month, but works councils and CBAs
# often add ~5% in additional employer costs (vacation pay, holiday pay premiums).
DE_EMPLOYER_OTHER_RATE  = 0.05
DE_EMPLOYER_BURDEN_RATE = DE_EMPLOYER_SS_RATE + DE_EMPLOYER_OTHER_RATE

# Italy welder wages (CCNL Metalmeccanici Industria, June 2024 tables)
# A welder maps to level C1-C3. Level C3 (ex-5th level): ~€2,130/month.
# Level C1 (ex-3rd level S): ~€1,948/month.
# Using C2 (~€1,989/month) as mid-skill welder benchmark.
# Source: lexplain.it/tabelle-retributive-metalmeccanici-industria/ citing June 2024 CCNL tables
IT_WELDER_MONTHLY_EUR   = 1_989      # EUR/month gross, CCNL C2 level mid-skill welder
IT_ANNUAL_MONTHS        = 13.5       # CCNL mandates 13th month + partial 14th (varies by CBA; 13.5 is conservative)
IT_WELDER_ANNUAL_EUR    = IT_WELDER_MONTHLY_EUR * IT_ANNUAL_MONTHS
IT_WORKING_HOURS_YR     = 1_760      # standard Italian metalworking hours/year (contractual)
IT_WELDER_HOURLY_EUR    = IT_WELDER_ANNUAL_EUR / IT_WORKING_HOURS_YR
# Italy employer burden: social security 29-32% of gross + TFR ~7.5% + INAIL ~1-2%
# Total: ~38-42% on top of gross wage. Using 40% midpoint.
# Source: peoitaly.com employer costs Italy 2024
IT_EMPLOYER_BURDEN_RATE = 0.40

# EUR/USD exchange rate (approximate 2024 average)
EUR_USD = 1.08

# ---------------------------------------------------------------------------
# All-in employer cost calculation
# ---------------------------------------------------------------------------

ANNUAL_HOURS_WORKED = 2_000   # productive hours per welder per year (US standard)
EU_ANNUAL_HOURS     = 1_760   # EU/Italy standard contracted hours

def all_in_hourly(gross_hourly: float, burden_rate: float) -> float:
    """Return total employer cost per hour worked (gross wage * (1 + burden_rate))."""
    return gross_hourly * (1 + burden_rate)

us_gross_hr   = US_WELDER_MEDIAN_HOURLY
us_allin_hr   = all_in_hourly(us_gross_hr, US_EMPLOYER_BURDEN_RATE)
us_allin_ann  = us_allin_hr * ANNUAL_HOURS_WORKED

de_gross_hr   = DE_WELDER_HOURLY_EUR
de_allin_hr   = all_in_hourly(de_gross_hr, DE_EMPLOYER_BURDEN_RATE)
de_allin_ann  = de_allin_hr * EU_ANNUAL_HOURS

it_gross_hr   = IT_WELDER_HOURLY_EUR
it_allin_hr   = all_in_hourly(it_gross_hr, IT_EMPLOYER_BURDEN_RATE)
it_allin_ann  = it_allin_hr * IT_WORKING_HOURS_YR

# ---------------------------------------------------------------------------
# Contractor economics: billable rate vs. all-in cost
# ---------------------------------------------------------------------------
# Billable market rates:
# US: $65-$125/hr depending on process and region; blended shop rate ~$75-$90/hr for
#     MIG/structural, ~$100-$125 for TIG/pipe. Using $85/hr as a mid-market blended rate.
#     Source: latestcost.com, homeguide.com, thumbtack.com 2024 data.
# EU (Germany): European rates are less standardized. German Lohnfertigung
#     welding shops typically charge €60-€90/hr for contract welding.
#     Using €70/hr as mid-market.
# Italy: Italian terzisti (subcontract fab shops) charge €40-€65/hr.
#     Using €52/hr as mid-market.

US_BILLABLE_RATE_LOW  = 65.0   # USD/hr
US_BILLABLE_RATE_MID  = 85.0
US_BILLABLE_RATE_HIGH = 125.0

DE_BILLABLE_RATE_LOW  = 60.0   # EUR/hr
DE_BILLABLE_RATE_MID  = 70.0
DE_BILLABLE_RATE_HIGH = 90.0

IT_BILLABLE_RATE_LOW  = 40.0   # EUR/hr
IT_BILLABLE_RATE_MID  = 52.0
IT_BILLABLE_RATE_HIGH = 65.0

# Overhead per direct-labor hour (beyond direct labor itself):
# Consumables, shielding gas, equipment depreciation, facilities, admin.
# Trade press (thefabricator.com, canadianmetalworking.com) consistently cites
# $25-$50/hr overhead for welding departments. Using $35 mid for US.
US_OVERHEAD_PER_HR = 35.0   # USD/hr (consumables + gas + equip + facilities + admin)
DE_OVERHEAD_PER_HR = 28.0   # EUR/hr
IT_OVERHEAD_PER_HR = 18.0   # EUR/hr (lower equipment cost base, smaller shops)

def gross_margin(billable: float, labor_cost: float, overhead: float) -> float:
    """Gross margin = (billable - labor_cost - overhead) / billable."""
    return (billable - labor_cost - overhead) / billable

us_gm_mid = gross_margin(US_BILLABLE_RATE_MID, us_allin_hr, US_OVERHEAD_PER_HR)
de_gm_mid = gross_margin(DE_BILLABLE_RATE_MID, de_allin_hr, DE_OVERHEAD_PER_HR)
it_gm_mid = gross_margin(IT_BILLABLE_RATE_MID, it_allin_hr, IT_OVERHEAD_PER_HR)

# Net margin: industry references (The Fabricator, FMA survey EBITDA ~9.8%) suggest
# metal fab net margins of 4-10%. Specialty welding contractors are higher.
# Approximate net margin ~8-12% after SG&A on top of above gross.
US_NET_MARGIN_ESTIMATE = 0.10   # ~10% typical for specialty welding contractor
DE_NET_MARGIN_ESTIMATE = 0.08
IT_NET_MARGIN_ESTIMATE = 0.07

# ---------------------------------------------------------------------------
# Cobot break-even analysis
# ---------------------------------------------------------------------------
# Cobot welding cell all-in installed cost:
# Vectis Automation: $95k-$140k all-in (pricing page 2024)
# Hirebotics Cobot Welder core: $105k (published pricing)
# Lincoln Electric Cooper: $85k-$100k
# Codinter example CapEx: $70k + $7k hidden = $77k
# Using $110k as representative mid-market all-in installed cost.
# Source: vectisautomation.com/pricing, hirebotics.com, lincolnelectric.com (2024)

COBOT_INSTALLED_COST  = 110_000   # USD, all-in (robot arm, welder, fixtures, integration)
COBOT_ANNUAL_OPEX     = 13_250    # USD/yr (consumables $10k, power $950, maintenance $2.5k)
                                   # Source: codinter.com ROI analysis
COBOT_USEFUL_LIFE_YR  = 7         # years (industry standard, conservative)
COBOT_SALVAGE         = 0.10      # fraction of installed cost residual at end of life

# Cobot productivity relative to human: 3-4x on arc-on time due to no fatigue,
# higher duty cycle. Human arc-on rate is 15-45% of total time; cobot sustains ~85%.
# Net effective output: cobot produces ~2-3x a human when accounting for setup overhead.
# Using 2.5x as conservative mid-point.
# Source: Vectis 2024 ("3-4x productivity boost"), codinter.com, binzel-abicor.com
COBOT_PRODUCTIVITY_MULTIPLIER = 2.5

# Cobot operates in single shift (2,000 hr/yr), potentially double shift (4,000 hr/yr)
COBOT_HOURS_SINGLE_SHIFT = 2_000   # hr/yr
COBOT_HOURS_DOUBLE_SHIFT = 4_000

def cobot_annual_depreciation(cost: float, life_yr: int, salvage: float) -> float:
    """Straight-line depreciation."""
    return (cost * (1 - salvage)) / life_yr

def cobot_cost_per_hour(
    installed_cost: float,
    annual_opex: float,
    life_yr: int,
    salvage: float,
    hours_per_yr: float,
) -> float:
    """All-in cost per hour for the cobot cell."""
    annual_depreciation = cobot_annual_depreciation(installed_cost, life_yr, salvage)
    return (annual_depreciation + annual_opex) / hours_per_yr

# Human welder cost per hour (US, all-in employer cost)
human_cost_hr_us = us_allin_hr

cobot_cph_single = cobot_cost_per_hour(
    COBOT_INSTALLED_COST, COBOT_ANNUAL_OPEX, COBOT_USEFUL_LIFE_YR,
    COBOT_SALVAGE, COBOT_HOURS_SINGLE_SHIFT
)
cobot_cph_double = cobot_cost_per_hour(
    COBOT_INSTALLED_COST, COBOT_ANNUAL_OPEX, COBOT_USEFUL_LIFE_YR,
    COBOT_SALVAGE, COBOT_HOURS_DOUBLE_SHIFT
)

# Effective cost per human-equivalent hour of output:
cobot_effective_cph_single = cobot_cph_single / COBOT_PRODUCTIVITY_MULTIPLIER
cobot_effective_cph_double = cobot_cph_double / COBOT_PRODUCTIVITY_MULTIPLIER

# Simple payback period: how long until cobot capital is recovered via labor savings
# Assume one human welder replaced per cobot cell (conservative; some replace 1.5-2)
annual_labor_savings_single = (human_cost_hr_us * COBOT_HOURS_SINGLE_SHIFT) - (COBOT_ANNUAL_OPEX + cobot_annual_depreciation(COBOT_INSTALLED_COST, COBOT_USEFUL_LIFE_YR, COBOT_SALVAGE))
annual_labor_savings_double = (human_cost_hr_us * COBOT_HOURS_DOUBLE_SHIFT) - (COBOT_ANNUAL_OPEX + cobot_annual_depreciation(COBOT_INSTALLED_COST, COBOT_USEFUL_LIFE_YR, COBOT_SALVAGE))

payback_single = COBOT_INSTALLED_COST / max(annual_labor_savings_single, 1)
payback_double = COBOT_INSTALLED_COST / max(annual_labor_savings_double, 1)

# Minimum annual hours for cobot to break even against human welder (cost parity)
# cobot_cost_per_hour(H) = human_cost_hr_us
# (depreciation + opex) / H = human_cost_hr_us  ->  H = (depreciation + opex) / human_cost_hr_us
annual_fixed_cobot = cobot_annual_depreciation(COBOT_INSTALLED_COST, COBOT_USEFUL_LIFE_YR, COBOT_SALVAGE) + COBOT_ANNUAL_OPEX
breakeven_hours = annual_fixed_cobot / human_cost_hr_us

# ---------------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------------

def pct(x: float) -> str:
    return f"{x * 100:.1f}%"

print("=" * 65)
print("WELDING ECONOMICS BY GEOGRAPHY (2024-2025 data)")
print("=" * 65)

print("\n--- WELDER WAGES ---")
print(f"{'':35s} {'US (USD)':>12s} {'Germany (EUR)':>14s} {'Italy (EUR)':>12s}")
print(f"{'Gross hourly wage':35s} {'$'+f'{us_gross_hr:.2f}':>12s} {'€'+f'{de_gross_hr:.2f}':>14s} {'€'+f'{it_gross_hr:.2f}':>12s}")
print(f"{'Employer burden rate':35s} {pct(US_EMPLOYER_BURDEN_RATE):>12s} {pct(DE_EMPLOYER_BURDEN_RATE):>14s} {pct(IT_EMPLOYER_BURDEN_RATE):>12s}")
print(f"{'All-in employer cost/hr':35s} {'$'+f'{us_allin_hr:.2f}':>12s} {'€'+f'{de_allin_hr:.2f}':>14s} {'€'+f'{it_allin_hr:.2f}':>12s}")
print(f"{'All-in employer cost/yr':35s} {'$'+f'{us_allin_ann:,.0f}':>12s} {'€'+f'{de_allin_ann:,.0f}':>14s} {'€'+f'{it_allin_ann:,.0f}':>12s}")
print(f"{'Annual hours worked':35s} {ANNUAL_HOURS_WORKED:>12d} {EU_ANNUAL_HOURS:>14d} {IT_WORKING_HOURS_YR:>12d}")

print("\n--- CONTRACTOR BILLABLE RATES (MID-MARKET BLENDED) ---")
print(f"{'Market billable rate (low)':35s} {'$'+f'{US_BILLABLE_RATE_LOW:.0f}/hr':>12s} {'€'+f'{DE_BILLABLE_RATE_LOW:.0f}/hr':>14s} {'€'+f'{IT_BILLABLE_RATE_LOW:.0f}/hr':>12s}")
print(f"{'Market billable rate (mid)':35s} {'$'+f'{US_BILLABLE_RATE_MID:.0f}/hr':>12s} {'€'+f'{DE_BILLABLE_RATE_MID:.0f}/hr':>14s} {'€'+f'{IT_BILLABLE_RATE_MID:.0f}/hr':>12s}")
print(f"{'Market billable rate (high)':35s} {'$'+f'{US_BILLABLE_RATE_HIGH:.0f}/hr':>12s} {'€'+f'{DE_BILLABLE_RATE_HIGH:.0f}/hr':>14s} {'€'+f'{IT_BILLABLE_RATE_HIGH:.0f}/hr':>12s}")
print(f"{'Overhead per hr (non-labor)':35s} {'$'+f'{US_OVERHEAD_PER_HR:.0f}/hr':>12s} {'€'+f'{DE_OVERHEAD_PER_HR:.0f}/hr':>14s} {'€'+f'{IT_OVERHEAD_PER_HR:.0f}/hr':>12s}")
print(f"{'Gross margin (mid rate)':35s} {pct(us_gm_mid):>12s} {pct(de_gm_mid):>14s} {pct(it_gm_mid):>12s}")
print(f"{'Implied net margin (est)':35s} {pct(US_NET_MARGIN_ESTIMATE):>12s} {pct(DE_NET_MARGIN_ESTIMATE):>14s} {pct(IT_NET_MARGIN_ESTIMATE):>12s}")

print("\n--- COST COMPONENT BREAKDOWN (US, per billable hour at $85) ---")
us_labor_frac    = us_allin_hr / US_BILLABLE_RATE_MID
us_overhead_frac = US_OVERHEAD_PER_HR / US_BILLABLE_RATE_MID
us_margin_frac   = us_gm_mid
print(f"  Direct labor (all-in):  {pct(us_labor_frac):>8s}  (${us_allin_hr:.2f}/hr)")
print(f"  Non-labor overhead:     {pct(us_overhead_frac):>8s}  (${US_OVERHEAD_PER_HR:.0f}/hr: consumables, gas, equip, facilities)")
print(f"  Gross margin:           {pct(us_margin_frac):>8s}")
print(f"  Less SG&A/interest:          ~5-7pp")
print(f"  Net margin (est):            ~8-12%")

print("\n--- COBOT BREAK-EVEN ANALYSIS (US) ---")
annual_dep = cobot_annual_depreciation(COBOT_INSTALLED_COST, COBOT_USEFUL_LIFE_YR, COBOT_SALVAGE)
print(f"  Installed cost:              ${COBOT_INSTALLED_COST:,.0f}")
print(f"  Useful life:                 {COBOT_USEFUL_LIFE_YR} years")
print(f"  Annual depreciation (SL):    ${annual_dep:,.0f}/yr")
print(f"  Annual OPEX (consumables,")
print(f"    power, maintenance):       ${COBOT_ANNUAL_OPEX:,.0f}/yr")
print(f"  Total annual fixed cost:     ${annual_fixed_cobot:,.0f}/yr")
print(f"")
print(f"  Human welder all-in cost:    ${human_cost_hr_us:.2f}/hr")
print(f"  Productivity multiplier:     {COBOT_PRODUCTIVITY_MULTIPLIER}x")
print(f"")
print(f"  Single shift (2,000 hr/yr):")
print(f"    Cobot raw cost/hr:         ${cobot_cph_single:.2f}")
print(f"    Cobot effective cost/hr    ${cobot_effective_cph_single:.2f}  (per human-equiv output-hr)")
print(f"    vs human all-in:           ${human_cost_hr_us:.2f}")
print(f"    Annual labor savings:      ${annual_labor_savings_single:,.0f}")
print(f"    Simple payback:            {payback_single:.1f} yrs")
print(f"")
print(f"  Double shift (4,000 hr/yr):")
print(f"    Cobot raw cost/hr:         ${cobot_cph_double:.2f}")
print(f"    Cobot effective cost/hr    ${cobot_effective_cph_double:.2f}  (per human-equiv output-hr)")
print(f"    Annual labor savings:      ${annual_labor_savings_double:,.0f}")
print(f"    Simple payback:            {payback_double:.1f} yrs")
print(f"")
print(f"  Break-even hours/yr (cost parity, single worker displaced):")
print(f"    {breakeven_hours:.0f} hr/yr  (~{breakeven_hours/ANNUAL_HOURS_WORKED:.1f} shifts)")
print(f"")
print(f"  Minimum economic batch: cobot requires ~{breakeven_hours:.0f} arc-on hours/yr")
print(f"  to justify capital at single-shift labor rates. At ~15 min avg weld time")
print(f"  per part, that is ~{breakeven_hours * 4:.0f} parts/yr minimum; at 5 min avg,")
print(f"  ~{breakeven_hours * 12:.0f} parts/yr.")

print("\n--- SUMMARY: UNSERVED SEGMENT ---")
print(f"  Cobot cells break even at >{breakeven_hours:.0f} arc-on hr/yr (single shift).")
print(f"  Shops below this threshold (~high-mix, <500 parts per batch) are underserved")
print(f"  by automation. This is the target segment for a training-data contractor:")
print(f"  human welders who are economically irreplaceable until data volume makes")
print(f"  a custom model viable.")
