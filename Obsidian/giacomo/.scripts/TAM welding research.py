"""
TAM analysis for welding automation startup.

Research goal: estimate the total addressable market for a welding contractor
that collects training data via instrumented guns to eventually train welding robots,
targeting SME job-shop welding (short-run, variable-geometry) not served by classical automation.

Three angles:
  1. Labor stock (top-down): welder headcount × wages → total labor bill → SME fraction
  2. Fabricated metal establishments (bottom-up): SME shop count × revenue → implied welding spend
  3. Robot sanity check: welding robot installed base vs. total welding labor → unserved gap

Data sources and years are documented inline.
"""

# ---------------------------------------------------------------------------
# Sources summary
# BLS OES May 2024 (SOC 51-4121): 457,300 jobs, median $51,000/yr
#   https://www.onetonline.org/link/summary/51-4121.00 (O*NET citing BLS 2024)
# AWS Welding Workforce Data 2025: 771,000 total welding professionals, avg $26.76/hr
#   https://weldingworkforcedata.com/
# IFR World Robotics 2025 (2024 data): 542,000 total robots installed in 2024,
#   4,664,000 global installed base; 14.67% of applications = welding; Italy 8,783 units
#   https://ifr.org/ifr-press-releases/news/global-robot-demand-in-factories-doubles-over-10-years
# IFR World Robotics 2024 (2023 data): 541,302 total; EU 92,393; Italy 10,412
#   https://ifr.org/ifr-press-releases/news/record-of-4-million-robots-working-in-factories-worldwide
# Grand View Research / market reports: global welding equipment ~$19.7B in 2023,
#   consumables ~$18B; automated segment ~55.8% of equipment units
# Eurostat / CEDEFOP: ~7.4 million metal workers in EU (2022), 22% in ISCO-721
#   (sheet/structural metal workers, moulders, welders)
# NACE C25 EU (2022): ~3.7 million employed in fabricated metal products Div 25
# Federmeccanica: Italy metalworking sector ~1.7 million workers, ~150B EUR value added
# IFR Europe 2023: Italy 10,412 robots installed; 2024: 8,783 installed
# Job-shop share of sheet metal fabrication equipment market: 31.4% revenue share (Grand View 2023)
# ---------------------------------------------------------------------------

print("=" * 70)
print("WELDING AUTOMATION TAM ANALYSIS")
print("=" * 70)

# ---------------------------------------------------------------------------
# SECTION 1 — UNITED STATES
# ---------------------------------------------------------------------------
print("\n--- UNITED STATES ---\n")

# Labor stock
# BLS OES May 2024 (SOC 51-4121) gives 457,300 jobs (O*NET/BLS Occupational Outlook Handbook 2024)
# AWS Welding Workforce Data site (2025) says 771,000 total welding professionals across 6 categories;
# SOC 51-4121 is ~61% of that = 470,310 — consistent with BLS figure. Use BLS primary count.
us_welders_bls = 457_300          # SOC 51-4121: welders, cutters, solderers, brazers (BLS OES May 2024)
us_welding_professionals_aws = 771_000  # all 6 AWS categories incl. boilermakers, sheet metal, structural (AWS 2025)

# Median wage (BLS OES May 2024): $51,000/yr; mean slightly higher (~$55k is typical spread)
# AWS reports avg hourly $26.76 → $55,660/yr; use as mean estimate
us_median_wage = 51_000           # USD/yr, BLS OES May 2024
us_mean_wage_aws = 26.76 * 2080   # $55,660/yr from AWS hourly avg (AWS 2025)

# Total labor bill for SOC 51-4121 only
us_labor_bill_bls = us_welders_bls * us_mean_wage_aws
print(f"BLS SOC 51-4121 welder count (May 2024):         {us_welders_bls:>12,}")
print(f"AWS total welding professionals (2025):          {us_welding_professionals_aws:>12,}")
print(f"Median annual wage (BLS 2024):                   ${us_median_wage:>11,}")
print(f"Mean annual wage estimate (AWS avg hourly×2080): ${us_mean_wage_aws:>11,.0f}")
print(f"Total welder labor bill (SOC 51-4121 only):      ${us_labor_bill_bls/1e9:>9.2f}B")

# SME job-shop fraction
# Job shops hold 31.4% revenue share of sheet metal fabrication equipment market (Grand View 2023).
# Classical automation (automotive OEMs, aerospace primes, heavy industry) is concentrated in
# large manufacturers. BLS NAICS 332 has ~53,700 establishments; the vast majority are SMEs.
# Conservative estimate: ~40% of welding labor is in SME job shops not amenable to classical robots
# (short runs, variable geometry, fixture-intensive). This aligns with:
#   - ~80% of NAICS 332 employment is in SMEs (Eurostat 2010 figure for analogous EU sector)
#   - But large-batch SMEs (auto suppliers, HVAC OEMs) can use traditional robots
#   - So we estimate 35–45% as unserved SME job-shop fraction; use 40% central, 35% low, 50% high.
us_sme_fraction_low = 0.35
us_sme_fraction_mid = 0.40
us_sme_fraction_high = 0.50

us_addressable_labor_low = us_labor_bill_bls * us_sme_fraction_low
us_addressable_labor_mid = us_labor_bill_bls * us_sme_fraction_mid
us_addressable_labor_high = us_labor_bill_bls * us_sme_fraction_high

print(f"\nSME job-shop fraction assumption: {us_sme_fraction_low:.0%}–{us_sme_fraction_high:.0%} (central {us_sme_fraction_mid:.0%})")
print(f"SME-addressable labor bill (low):  ${us_addressable_labor_low/1e9:.2f}B")
print(f"SME-addressable labor bill (mid):  ${us_addressable_labor_mid/1e9:.2f}B")
print(f"SME-addressable labor bill (high): ${us_addressable_labor_high/1e9:.2f}B")

# Bottom-up: NAICS 332 establishments
# 2020 Census: 49,442 firms / 53,743 establishments, 1,359,954 employees, $82.8B payroll
# Note: NAICS 332 includes ALL fabricated metal, not just welding; welding is ~30–40% of ops
naics332_establishments = 53_743   # US Census 2020 (most recent available)
naics332_employment = 1_359_954    # US Census 2020
naics332_payroll = 82_824_260_000  # USD, US Census 2020
naics332_avg_wage = naics332_payroll / naics332_employment

# Fraction of NAICS 332 work that is welding (arc/MIG/TIG): ~35% of labor time is a common
# industry rule of thumb; Lincoln Electric uses similar framing in investor materials
welding_labor_fraction_of_332 = 0.35

us_naics332_welding_labor = naics332_payroll * welding_labor_fraction_of_332
us_naics332_sme_welding_labor = us_naics332_welding_labor * us_sme_fraction_mid

print(f"\n--- Bottom-up (NAICS 332) ---")
print(f"NAICS 332 establishments (Census 2020):          {naics332_establishments:>12,}")
print(f"NAICS 332 employment (Census 2020):              {naics332_employment:>12,}")
print(f"NAICS 332 annual payroll (Census 2020):          ${naics332_payroll/1e9:>9.1f}B")
print(f"NAICS 332 avg wage:                              ${naics332_avg_wage:>11,.0f}")
print(f"Welding labor fraction of NAICS 332 ({welding_labor_fraction_of_332:.0%}):    ${us_naics332_welding_labor/1e9:>9.2f}B")
print(f"SME job-shop welding labor (40% of above):       ${us_naics332_sme_welding_labor/1e9:>9.2f}B")

# Robot sanity check
# IFR 2025 (2024 data): US installed 34,200 robots in 2024; ~14.67% = welding
# Cumulative stock: US total stock estimated ~450,000–500,000 (not directly stated by IFR for US)
# Global installed base: 4,664,000; Americas ~9% → ~420,000; US ~85% of Americas → ~357,000
# Welding robots in US stock: 14.67% × 357,000 = ~52,370
us_installed_base_est = 4_664_000 * 0.09 * 0.85
us_welding_robot_stock = us_installed_base_est * 0.1467
# Each welding robot replaces roughly 1.5–2.0 FTE welders (higher duty cycle, multi-shift)
robot_to_welder_replacement = 1.75
us_welders_served_by_robots = us_welding_robot_stock * robot_to_welder_replacement
us_welder_automation_gap = us_welders_bls - us_welders_served_by_robots
us_automation_penetration = us_welders_served_by_robots / us_welders_bls

print(f"\n--- Robot sanity check ---")
print(f"US robot installed base estimate:                {us_installed_base_est:>12,.0f}")
print(f"US welding robot stock estimate (14.67%):        {us_welding_robot_stock:>12,.0f}")
print(f"Welders effectively served by robots (~1.75×):   {us_welders_served_by_robots:>12,.0f}")
print(f"Unserved welder gap (BLS count - robot-served):  {us_welder_automation_gap:>12,.0f}")
print(f"Implied robot automation penetration:            {us_automation_penetration:>12.1%}")

# ---------------------------------------------------------------------------
# SECTION 2 — EUROPEAN UNION
# ---------------------------------------------------------------------------
print("\n\n--- EUROPEAN UNION ---\n")

# Eurostat / CEDEFOP: 7.4 million metal workers (ISCO 7, metal & machinery trades) in EU-27 (2022)
# ISCO 721 (sheet/structural metal workers, moulders, welders) = 22% of that group
# This gives the primary welders/related subgroup
eu_metal_workers_total = 7_400_000        # CEDEFOP 2023 update citing Eurostat 2022
eu_isco721_fraction = 0.22                # CEDEFOP 2023 (22% of metal workers in this sub-group)
eu_welders_isco721 = eu_metal_workers_total * eu_isco721_fraction

# NACE C25 (fabricated metal products) EU: ~3.7M employed (Eurostat 2022 per search results)
eu_nace_c25_employment = 3_700_000        # Eurostat structural business stats 2022

# Wages: EU average manufacturing wage is approximately €35,000–€40,000/yr gross
# Germany higher (~€50k), Italy/Spain lower (~€30–35k). Use €36,000 as EU avg for metal trades.
eu_avg_welder_wage = 36_000               # EUR/yr (estimated; Eurostat SES data range)
eu_total_welder_labor_bill = eu_welders_isco721 * eu_avg_welder_wage

# Europe welding equipment market: €4.23B in 2023 (Grand View Research)
# Europe welding consumables: €3.1B in 2024 (IMARC Group)
eu_welding_equipment_market = 4_234_000_000   # EUR, 2023, Grand View Research
eu_welding_consumables_market = 3_100_000_000  # EUR, 2024, IMARC Group

# SME fraction: EU NACE C25 data (Eurostat 2010 historical): SMEs = 82.5% of employment
# Modern figure likely similar; use 80% for employment share, 40% for job-shop unserved
eu_sme_employment_fraction = 0.80   # SME share of NACE C25 employment
eu_sme_unserved_fraction = 0.40     # of those, fraction in truly short-run job shops

eu_addressable_labor_mid = eu_total_welder_labor_bill * eu_sme_unserved_fraction

# Robot check: IFR 2024 (2023 data): EU installed 92,393 robots; Italy 10,412
# IFR 2025 (2024 data): EU installed 73,534 (note: EU subset reported was 73,534 in 2023 from earlier fetch)
# For 2024: Europe total 542k × 16% = ~86,700; EU subset ~80% of Europe → ~69,400
eu_robot_installations_2024 = 542_000 * 0.16
eu_welding_robot_installations = eu_robot_installations_2024 * 0.1467
# EU stock: global 4,664,000 × 16% = 746,240; welding share: ×14.67% = 109,473
eu_robot_stock = 4_664_000 * 0.16
eu_welding_robot_stock = eu_robot_stock * 0.1467
eu_welders_served = eu_welding_robot_stock * robot_to_welder_replacement
eu_automation_penetration = eu_welders_served / eu_welders_isco721

print(f"EU metal workers total (Eurostat/CEDEFOP 2022):  {eu_metal_workers_total:>12,}")
print(f"ISCO 721 share (sheet metal, moulders, welders): {eu_isco721_fraction:>12.0%}")
print(f"EU estimated welders/related (ISCO 721):         {eu_welders_isco721:>12,.0f}")
print(f"NACE C25 employment EU (Eurostat 2022):          {eu_nace_c25_employment:>12,}")
print(f"EU avg welder wage estimate:                     €{eu_avg_welder_wage:>11,}")
print(f"EU total welder labor bill (ISCO 721):           €{eu_total_welder_labor_bill/1e9:>9.2f}B")
print(f"SME-addressable labor (40% unserved):            €{eu_addressable_labor_mid/1e9:>9.2f}B")
print(f"\nEU welding equipment market (2023):              €{eu_welding_equipment_market/1e9:>9.2f}B")
print(f"EU welding consumables market (2024):            €{eu_welding_consumables_market/1e9:>9.2f}B")
print(f"\nEU robot installations 2024 (est.):              {eu_robot_installations_2024:>12,.0f}")
print(f"EU welding robot installations 2024 (14.67%):    {eu_welding_robot_installations:>12,.0f}")
print(f"EU welding robot stock est.:                     {eu_welding_robot_stock:>12,.0f}")
print(f"Welders served by EU robots (~1.75×):            {eu_welders_served:>12,.0f}")
print(f"Implied robot automation penetration:            {eu_automation_penetration:>12.1%}")

# ---------------------------------------------------------------------------
# SECTION 3 — ITALY
# ---------------------------------------------------------------------------
print("\n\n--- ITALY ---\n")

# Federmeccanica: Italian metalworking sector ~1.7M workers, ~€150B value added (c.2022)
# Italy is 2nd largest EU robot market; fabricated metal (NACE C25) is a core sector.
# Italy's NACE C25 share of EU: Italy contributes ~12–13% of EU manufacturing value added.
# Applying 12% to EU NACE C25 employment of 3.7M → ~444,000 in NACE C25 Italy
italy_nace_c25_employment_est = int(eu_nace_c25_employment * 0.12)  # ~444,000

# Federmeccanica total metalworking: ~1.7M. NACE C25 is a subset (~26% of metalworking total).
italy_metalworking_total = 1_700_000      # Federmeccanica (year ~2022)
italy_metalworking_value_added = 150e9   # EUR, Federmeccanica

# Italy welders (ISCO 721): applying EU ratio of ISCO-721 to NACE-C25 employment:
# EU: 1,628,000 (ISCO721) / 3,700,000 (NACE-C25) = 44% ratio
eu_isco721_to_nace_c25_ratio = eu_welders_isco721 / eu_nace_c25_employment
italy_welders_est = int(italy_nace_c25_employment_est * eu_isco721_to_nace_c25_ratio)

# Italian wages: average manufacturing wage ~€28,000–€32,000/yr (ISTAT SES 2022)
# Metalworking CCNL (collective contract) base: avg ~€29,000–€33,000 depending on level
italy_avg_welder_wage = 30_000             # EUR/yr (ISTAT SES 2022 range)
italy_total_welder_labor_bill = italy_welders_est * italy_avg_welder_wage

# IFR robot data:
# 2022: 11,475 installed (IFR 2023 report)
# 2023: ~12,000 installed (IFR press release)
# 2024: 8,783 installed (IFR 2025 report, -16% YoY)
italy_robot_installed_2024 = 8_783        # IFR 2025
italy_robot_installed_2023 = 10_412       # IFR 2024

# Italy robot stock: proportional to global. Italy ~2% of global stock as approximation.
# (Italy 2024 installations: 8,783 / 542,000 global = 1.6%; stock likely ~2%)
italy_robot_stock = 4_664_000 * 0.02
italy_welding_robot_stock = italy_robot_stock * 0.1467
italy_welders_served = italy_welding_robot_stock * robot_to_welder_replacement
italy_automation_penetration = italy_welders_served / italy_welders_est

# SME fraction: Italy metalworking is famously fragmented. ~95% of enterprises are SMEs < 50 employees.
# Federmeccanica notes average enterprise size is small. Use 50% unserved fraction (higher than EU avg)
italy_sme_unserved_fraction = 0.50
italy_addressable_labor = italy_total_welder_labor_bill * italy_sme_unserved_fraction

print(f"Italy metalworking total workers (Federmeccanica ~2022): {italy_metalworking_total:>9,}")
print(f"Italy NACE C25 employment estimate (12% of EU):          {italy_nace_c25_employment_est:>9,}")
print(f"Italy welders estimate (ISCO 721 ratio from EU):         {italy_welders_est:>9,}")
print(f"Italy avg welder wage estimate (ISTAT SES 2022):        €{italy_avg_welder_wage:>9,}")
print(f"Italy total welder labor bill:                          €{italy_total_welder_labor_bill/1e9:>8.2f}B")
print(f"SME unserved fraction (50%):                            €{italy_addressable_labor/1e9:>8.2f}B")
print(f"\nItaly robot installations 2023 (IFR 2024):               {italy_robot_installed_2023:>9,}")
print(f"Italy robot installations 2024 (IFR 2025):               {italy_robot_installed_2024:>9,}")
print(f"Italy robot stock estimate (~2% of global):              {italy_robot_stock:>9,.0f}")
print(f"Italy welding robot stock (14.67%):                      {italy_welding_robot_stock:>9,.0f}")
print(f"Welders served by robots (~1.75×):                       {italy_welders_served:>9,.0f}")
print(f"Implied robot automation penetration:                    {italy_automation_penetration:>9.1%}")

# ---------------------------------------------------------------------------
# SECTION 4 — GLOBAL
# ---------------------------------------------------------------------------
print("\n\n--- GLOBAL ---\n")

# Global welding equipment market: ~$19.7B in 2023 (Grand View Research)
# Global welding consumables: ~$18B in 2023 (multiple sources)
# Robot welding market: ~$7–$11B depending on definition (Abagy: >$7B in 2024)
global_welding_equipment = 19_715_800_000   # USD, 2023, Grand View Research
global_welding_consumables = 18_020_000_000  # USD, 2023, multiple sources
global_welding_robot_market = 7_000_000_000  # USD, 2024, conservative (Abagy)

# Global welder count: extrapolate from US + EU + proxy for rest of world
# ILO estimates ~3–4M welders globally; World Robotics context and industry commentary
# suggests ~3M manual welders globally as reasonable order-of-magnitude
# (US: 457k, EU: 1.63M, rest of world incl. China/India/Asia: ~2–3× EU = ~3.3–5M)
# Use 4M as central global estimate.
global_welders_est = 4_000_000

# Total global welder labor bill: avg wage ~$25,000/yr globally (mix of low/high wage economies)
global_avg_welder_wage_usd = 25_000
global_total_labor_bill = global_welders_est * global_avg_welder_wage_usd

# Global welding robot stock: IFR 2025: 4,664,000 total; 14.67% welding = 684,000
global_welding_robot_stock = 4_664_000 * 0.1467
global_welders_served = global_welding_robot_stock * robot_to_welder_replacement
global_automation_penetration = global_welders_served / global_welders_est

# SME addressable: ~40% globally (lower in Asia where factory scale is larger)
global_sme_fraction = 0.40
global_addressable_labor = global_total_labor_bill * global_sme_fraction

print(f"Global welding equipment market (2023):          ${global_welding_equipment/1e9:>9.1f}B")
print(f"Global welding consumables market (2023):        ${global_welding_consumables/1e9:>9.1f}B")
print(f"Global welding robot market (2024):              ${global_welding_robot_market/1e9:>9.1f}B")
print(f"\nGlobal welder count estimate:                    {global_welders_est:>12,}")
print(f"Global avg welder wage estimate:                 ${global_avg_welder_wage_usd:>11,}")
print(f"Global total welder labor bill:                  ${global_total_labor_bill/1e9:>9.1f}B")
print(f"\nGlobal welding robot stock (4.664M × 14.67%):   {global_welding_robot_stock:>12,.0f}")
print(f"Welders served by robots (×1.75):                {global_welders_served:>12,.0f}")
print(f"Implied global robot automation penetration:     {global_automation_penetration:>12.1%}")
print(f"\nSME-addressable labor bill (40% unserved):       ${global_addressable_labor/1e9:>9.1f}B")

# ---------------------------------------------------------------------------
# SUMMARY TABLE
# ---------------------------------------------------------------------------
print("\n\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print(f"{'Geography':<10} {'Welders':>10} {'Avg Wage':>12} {'Labor Bill':>12} {'SME-TAM':>12} {'Bot. Pen.':>10}")
print("-" * 70)
print(f"{'US':<10} {us_welders_bls:>10,} {'$55,660':>12} ${us_labor_bill_bls/1e9:>10.1f}B ${us_addressable_labor_mid/1e9:>10.1f}B {us_automation_penetration:>9.1%}")
print(f"{'EU':<10} {eu_welders_isco721:>10,.0f} {'€36,000':>12} €{eu_total_welder_labor_bill/1e9:>10.1f}B €{eu_addressable_labor_mid/1e9:>10.1f}B {eu_automation_penetration:>9.1%}")
print(f"{'Italy':<10} {italy_welders_est:>10,} {'€30,000':>12} €{italy_total_welder_labor_bill/1e9:>10.1f}B €{italy_addressable_labor/1e9:>10.1f}B {italy_automation_penetration:>9.1%}")
print(f"{'Global':<10} {global_welders_est:>10,} {'$25,000':>12} ${global_total_labor_bill/1e9:>10.1f}B ${global_addressable_labor/1e9:>10.1f}B {global_automation_penetration:>9.1%}")

print("\n")
print("Notes:")
print("  - US welder count: BLS OES May 2024 SOC 51-4121 (457,300)")
print("  - EU welder count: CEDEFOP/Eurostat 2022 ISCO 721 estimate (22% of 7.4M metal workers)")
print("  - Italy welder count: derived from Italy NACE C25 share (12% EU) × ISCO721 ratio")
print("  - Global count: rough order-of-magnitude; ILO/industry suggest 3–5M")
print("  - Robot installed base: IFR World Robotics 2025 (2024 data); welding share 14.67%")
print("  - Robot-to-welder replacement ratio: 1.75 FTE (industry assumption; 1.5–2.0 range)")
print("  - SME-unserved fraction: 40% US/EU, 50% Italy (higher fragmentation), 40% global")
print("  - Confidence: US data HIGH; EU MEDIUM; Italy LOW (derived); Global LOW (rough est.)")
