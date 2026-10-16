from dataclasses import dataclass


SECONDS_PER_DAY = 86_400
HOURS_PER_YEAR = 8_760
COUNT_ACCELERATOR_OPTIMISTIC = 100_000


@dataclass(frozen=True)
class ScenarioThroughput:
    name: str
    tokens_output_per_second_per_accelerator: float
    note: str


@dataclass(frozen=True)
class ScenarioDemand:
    name: str
    tokens_output_equivalent_per_day: float
    note: str


@dataclass(frozen=True)
class ScenarioPower:
    name: str
    kilowatts_facility_per_accelerator: float
    note: str


def compute_tokens_per_day_total(
    scenario_throughput: ScenarioThroughput,
    utilization_effective: float,
) -> float:
    return (
        scenario_throughput.tokens_output_per_second_per_accelerator
        * COUNT_ACCELERATOR_OPTIMISTIC
        * SECONDS_PER_DAY
        * utilization_effective
    )


def compute_users_served(
    tokens_per_day_total: float,
    scenario_demand: ScenarioDemand,
) -> float:
    return tokens_per_day_total / scenario_demand.tokens_output_equivalent_per_day


def compute_power_megawatts(
    scenario_power: ScenarioPower,
) -> float:
    return (
        COUNT_ACCELERATOR_OPTIMISTIC
        * scenario_power.kilowatts_facility_per_accelerator
        / 1_000
    )


def compute_energy_terawatt_hours_year(
    scenario_power: ScenarioPower,
) -> float:
    return compute_power_megawatts(scenario_power) * HOURS_PER_YEAR / 1_000_000


def format_float_compact(value: float) -> str:
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}T"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:.0f}"


def print_capacity_table(
    scenarios_throughput: list[ScenarioThroughput],
    utilizations_effective: list[float],
) -> None:
    print("| Model and hardware case | Benchmark tokens/s/GPU | 35% effective | 50% effective | 70% effective |")
    print("|---|---:|---:|---:|---:|")
    for scenario_throughput in scenarios_throughput:
        values = [
            format_float_compact(
                compute_tokens_per_day_total(
                    scenario_throughput,
                    utilization_effective,
                )
            )
            for utilization_effective in utilizations_effective
        ]
        print(
            f"| {scenario_throughput.name} | "
            f"{scenario_throughput.tokens_output_per_second_per_accelerator:,.0f} | "
            f"{values[0]} | {values[1]} | {values[2]} |"
        )


def print_users_table(
    scenarios_throughput: list[ScenarioThroughput],
    scenarios_demand: list[ScenarioDemand],
    utilization_effective: float,
) -> None:
    headers_throughput = " | ".join(
        scenario_throughput.name for scenario_throughput in scenarios_throughput
    )
    dividers_throughput = "|".join("---:" for _ in scenarios_throughput)
    print(f"| Demand tier | Demand per active user or seat | {headers_throughput} |")
    print(f"|---|---:|{dividers_throughput}|")
    for scenario_demand in scenarios_demand:
        values = [
            format_float_compact(
                compute_users_served(
                    compute_tokens_per_day_total(
                        scenario_throughput,
                        utilization_effective,
                    ),
                    scenario_demand,
                )
            )
            for scenario_throughput in scenarios_throughput
        ]
        values_formatted = " | ".join(values)
        print(
            f"| {scenario_demand.name} | "
            f"{format_float_compact(scenario_demand.tokens_output_equivalent_per_day)} tok/day | "
            f"{values_formatted} |"
        )


def print_power_table(
    scenarios_power: list[ScenarioPower],
) -> None:
    print("| Facility power case | kW/GPU facility-level | Facility MW for 100k GPUs | TWh/year |")
    print("|---|---:|---:|---:|")
    for scenario_power in scenarios_power:
        print(
            f"| {scenario_power.name} | "
            f"{scenario_power.kilowatts_facility_per_accelerator:.1f} | "
            f"{compute_power_megawatts(scenario_power):.0f} | "
            f"{compute_energy_terawatt_hours_year(scenario_power):.2f} |"
        )


def main() -> None:
    scenarios_throughput = [
        ScenarioThroughput(
            name="B200 70B at moderate interactivity",
            tokens_output_per_second_per_accelerator=6_500,
            note="SemiAnalysis InferenceX Llama 3.3 70B on B200 at about 53 tok/s/user.",
        ),
        ScenarioThroughput(
            name="B200 70B at high interactivity",
            tokens_output_per_second_per_accelerator=3_600,
            note="SemiAnalysis InferenceX Llama 3.3 70B on B200 at about 91 tok/s/user.",
        ),
        ScenarioThroughput(
            name="B200 efficient 120B MoE",
            tokens_output_per_second_per_accelerator=20_400,
            note="SemiAnalysis InferenceX GPT-OSS 120B on B200 at about 112 tok/s/user.",
        ),
        ScenarioThroughput(
            name="GB300 DeepSeek-R1",
            tokens_output_per_second_per_accelerator=2_907,
            note="NVIDIA MLPerf v5.1 per-accelerator DeepSeek-R1 server record; InferenceX ranges widely by interactivity.",
        ),
        ScenarioThroughput(
            name="GB300 dense 405B",
            tokens_output_per_second_per_accelerator=170,
            note="NVIDIA MLPerf v5.1 per-accelerator Llama 3.1 405B server record.",
        ),
    ]

    scenarios_demand = [
        ScenarioDemand(
            name="Casual assistant",
            tokens_output_equivalent_per_day=2_000,
            note="Roughly current consumer use: several prompts/day with short answers.",
        ),
        ScenarioDemand(
            name="Active workplace copilot",
            tokens_output_equivalent_per_day=50_000,
            note="Daily work seat with RAG, drafting, summarization, and code review.",
        ),
        ScenarioDemand(
            name="Agentic worker",
            tokens_output_equivalent_per_day=500_000,
            note="Persistent agent loops, long context, tool use, and intermediate reasoning.",
        ),
        ScenarioDemand(
            name="Heavy developer or researcher",
            tokens_output_equivalent_per_day=5_000_000,
            note="High-volume coding, research, or automation workflows.",
        ),
    ]

    scenarios_power = [
        ScenarioPower(
            name="Hopper dense facility",
            kilowatts_facility_per_accelerator=1.3,
            note="H100/H200 GPU plus host, network, storage, and cooling overhead.",
        ),
        ScenarioPower(
            name="Blackwell rack-scale facility",
            kilowatts_facility_per_accelerator=2.2,
            note="GB200/GB300 NVL72 rack-level power plus PUE and facility overhead.",
        ),
        ScenarioPower(
            name="High-headroom Blackwell campus",
            kilowatts_facility_per_accelerator=3.0,
            note="Conservative facility-level planning allowance with redundancy and non-GPU load.",
        ),
    ]

    utilizations_effective = [0.35, 0.50, 0.70]

    print("## Capacity")
    print_capacity_table(scenarios_throughput, utilizations_effective)
    print()
    print("## User equivalents at 50% effective utilization")
    print_users_table(scenarios_throughput, scenarios_demand, 0.50)
    print()
    print("## Power")
    print_power_table(scenarios_power)


if __name__ == "__main__":
    main()
