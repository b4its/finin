/** Tipe data bersama untuk hasil API Financial Twin. */

export type FlagLevel = 'red' | 'orange' | 'yellow';

export interface Flag {
	level: FlagLevel;
	code: string;
	msg: string;
}

export interface YearPoint {
	year: number;
	net_worth: number;
	net_worth_real: number;
	debt: number;
	cash: number;
	invest: number;
	cashflow: number;
	emergency_months: number;
	dsr: number;
	defaulted: boolean;
}

export interface StressResult {
	shock: string;
	label: string;
	survived: boolean;
	min_cash: number;
	new_debt: number;
	worst_month: number;
	note: string;
}

export interface TwinSummary {
	year: number;
	net_worth: number;
	net_worth_real: number;
	debt: number;
	emergency_months: number;
	avg_dsr: number;
	defaulted: boolean;
}

export interface Twin {
	code: string;
	label: string;
	color: string;
	dash: string;
	icon: string;
	description: string;
	config: Record<string, unknown>;
	yearly_series: YearPoint[];
	summary: Record<string, unknown>;
	milestones?: Record<string, number | null>;
	flags: Flag[];
	stress: StressResult[];
	score: number;
	score_breakdown: Record<string, unknown>;
	deleted_by_hard_rule: boolean;
}

export interface Simulation {
	id: string;
	engine_version: string;
	assumption_code: string;
	assumption_as_of: string;
	preset: string;
	horizon_months: number;
	twins: Twin[];
	robust: boolean;
	robust_reason: string;
	preset_winners: Record<string, string>;
	assumptions: AssumptionsSnapshot;
	market_context: { label: string; source: string }[];
	flags: Flag[];
	best_twin: string;
	sensitivity_drivers: string[];
}

export interface AssumptionsSnapshot {
	code: string;
	as_of: string;
	label: string;
	engine_version: string;
	preset: string;
	values: {
		inflation: number;
		returns: Record<string, number>;
		salary_growth: number;
		s2_salary_premium: number;
		[key: string]: unknown;
	};
	presets: Record<string, Record<string, unknown>>;
	regulatory: Regulatory;
	sources: Record<string, { label: string; url: string; as_of: string; kind: string }>;
	market_context: { label: string; source: string }[];
	overrides?: Record<string, unknown>;
}

export interface Regulatory {
	version: string;
	replaces: string;
	effective_from: string;
	consumer_caps: {
		tenor_max_months: number | null;
		rate_daily_max: number;
		penalty_daily_max: number;
	}[];
	lock_cap_ratio: number;
	dsr_cap: number;
	default_days: number;
}

export interface Recommendation {
	simulation_id: string;
	best_twin: string;
	best_label: string;
	first_step: string;
	rationale: string;
	score_breakdown: Record<string, unknown>;
	source: 'llm' | 'template';
}

export interface NarrativeChunk {
	twin: string;
	horizon: number;
	text: string;
	source: 'llm' | 'template';
}

/* --- input decision shapes (wizard) --- */

export interface LoanSpec {
	kind: string;
	amount: number;
	tenor_months: number;
	rate_daily: number;
	penalty_daily: number | null;
}

export interface SaveSpec {
	monthly: number;
	instrument: string;
}

export interface StudySpec {
	years: number;
	total_cost: number;
	part_time_work: boolean;
	part_time_monthly: number;
	salary_premium: number;
}

export interface WorkSpec {
	upskill_monthly: number;
	skill_premium: number;
	premium_after_months: number;
}

export interface EmergencySpec {
	target_months: number;
	invest_monthly: number;
}

export interface KprSpec {
	property_price: number;
	down_payment_pct: number;
	interest_rate_annual: number;
	tenor_years: number;
	property_appreciation_annual: number;
}

export interface RentSpec {
	rent_monthly: number;
	invest_instrument: string;
}

export interface VehicleLeaseSpec {
	vehicle_price: number;
	down_payment_pct: number;
	interest_rate_annual: number;
	tenor_months: number;
	depreciation_annual: number;
}

export interface VehicleCashSpec {
	used_vehicle_price: number;
	invest_instrument: string;
}

export interface WeddingGrandSpec {
	reception_cost: number;
	savings_used: number;
	loan_amount: number;
	interest_rate_annual: number;
	tenor_months: number;
}

export interface WeddingIntimateSpec {
	intimate_cost: number;
	invest_instrument: string;
}

export interface Decision {
	type: string;
	loan?: LoanSpec;
	save?: SaveSpec;
	study?: StudySpec;
	work?: WorkSpec;
	emergency?: EmergencySpec;
	kpr?: KprSpec;
	rent?: RentSpec;
	vehicle_lease?: VehicleLeaseSpec;
	vehicle_cash?: VehicleCashSpec;
	wedding_grand?: WeddingGrandSpec;
	wedding_intimate?: WeddingIntimateSpec;
}
