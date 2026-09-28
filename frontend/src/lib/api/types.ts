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

export interface Profile {
	age: number;
	income_type: string;
	income_monthly: number;
	income_range?: { min: number; max: number } | null;
	expense_monthly: number;
	dependents_monthly: number;
	savings: number;
	existing_debt?: {
		principal: number;
		monthly_payment: number;
		annual_rate?: number;
		tenor_months?: number;
	};
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

export interface FranchiseSpec {
	franchise_fee: number;
	savings_used: number;
	kur_loan_amount: number;
	kur_interest_rate_annual: number;
	kur_tenor_months: number;
	monthly_net_profit: number;
}

export interface PassiveInvestSpec {
	invest_instrument: string;
}

export interface ChildEducationUnitLinkSpec {
	monthly_premium: number;
	target_years: number;
	acquisition_fee_pct_y1: number;
	acquisition_fee_pct_y2: number;
	acquisition_fee_pct_y3: number;
	invest_instrument: string;
}

export interface ChildEducationDiySpec {
	term_life_premium_monthly: number;
	invest_instrument: string;
}

export interface HajiFurodaSpec {
	total_cost: number;
	savings_used: number;
	financing_amount: number;
	financing_rate_annual: number;
	tenor_months: number;
}

export interface HajiRegulerSpec {
	bpkh_initial_deposit: number;
	invest_instrument: string;
}

export interface CareerCorporateSpec {
	salary_growth_annual: number;
	bonus_months_annual: number;
}

export interface CareerFreelanceSpec {
	revenue_multiplier: number;
	emergency_target_months: number;
	bpjs_mandiri_monthly: number;
}

export interface RentalPropertySpec {
	property_price: number;
	down_payment_pct: number;
	kpr_interest_rate_annual: number;
	kpr_tenor_years: number;
	gross_rental_yield_annual: number;
	occupancy_rate: number;
	operational_cost_pct: number;
	property_appreciation_annual: number;
}

export interface DividendInvestSpec {
	invest_instrument: string;
}

export interface EvVehicleSpec {
	vehicle_price: number;
	government_subsidy: number;
	down_payment_pct: number;
	loan_interest_rate_annual: number;
	loan_tenor_months: number;
	monthly_fuel_cost_savings: number;
	annual_tax_pkb_savings: number;
}

export interface IceVehicleSpec {
	vehicle_price: number;
	down_payment_pct: number;
	loan_interest_rate_annual: number;
	loan_tenor_months: number;
	invest_instrument: string;
}

export interface HealthBPJSSpec {
	class_level: number;
	monthly_premium: number;
	invest_instrument: string;
}

export interface HealthPrivateSpec {
	monthly_premium: number;
	annual_limit: number;
	coverage_ratio_catastrophic: number;
}

export interface PercentileValues {
	p10: number;
	p25: number;
	p50: number;
	p75: number;
	p90: number;
}

export interface MonteCarloYearPercentile {
	year: number;
	nominal: PercentileValues;
	real: PercentileValues;
}

export interface MonteCarloMetrics {
	success_rate_positive_y10: number;
	success_rate_wealth_preservation_y10: number;
	median_net_worth_nominal_y10: number;
	median_net_worth_real_y10: number;
	p10_net_worth_y10: number;
	p90_net_worth_y10: number;
	var_95_nominal_y10: number;
	cvar_95_nominal_y10: number;
	preset_used: string;
	instrument_volatility: number;
	inflation_volatility: number;
}

export interface MonteCarloResult {
	twin_code: string;
	twin_label: string;
	runs: number;
	yearly_percentiles: MonteCarloYearPercentile[];
	metrics: MonteCarloMetrics;
}

/** Persona kembar (twin) yang dipasangkan pada sebuah template keputusan. */
export interface TemplateTwin {
	code: string;
	label: string;
	color: string;
	dash: string;
	icon: string;
}

/** Deskriptor satu field masukan template (dipakai untuk ringkasan kebutuhan data). */
export interface TemplateField {
	key: string;
	label: string;
	type: 'currency' | 'float' | 'int' | 'percent' | 'percent_daily' | 'instrument' | 'bool';
	min?: number;
	max?: number;
}

/** Katalog template keputusan dari endpoint GET /templates. */
export interface DecisionTemplate {
	type: string;
	title: string;
	twin_a: TemplateTwin;
	twin_b: TemplateTwin;
	fields: TemplateField[];
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
	franchise?: FranchiseSpec;
	passive_invest?: PassiveInvestSpec;
	child_education_unitlink?: ChildEducationUnitLinkSpec;
	child_education_diy?: ChildEducationDiySpec;
	haji_furoda?: HajiFurodaSpec;
	haji_reguler?: HajiRegulerSpec;
	career_corporate?: CareerCorporateSpec;
	career_freelance?: CareerFreelanceSpec;
	rental_property?: RentalPropertySpec;
	dividend_invest?: DividendInvestSpec;
	ev_vehicle?: EvVehicleSpec;
	ice_vehicle?: IceVehicleSpec;
	health_bpjs?: HealthBPJSSpec;
	health_private?: HealthPrivateSpec;
}
