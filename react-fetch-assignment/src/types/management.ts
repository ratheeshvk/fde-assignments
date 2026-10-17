export interface Management {
    total_encounters: number;
    high_risk: number;
    medium_risk: number;
    low_risk: number;
    care_queue_size: number;
    pending_review: number;
    assigned: number;
    contacted: number;
    follow_up_scheduled: number;
    closed: number;
    high_risk_readmission_rate: number;
}