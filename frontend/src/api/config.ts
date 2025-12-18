export const API_URL = "http://localhost:8000";

export type TokenPayload = {
    uid?: number;
    username?: string;
    exp?: number; //convert to JS date by calling new Date(exp * 1000)
    iat?: number;
};

export interface Daily {
    id: number,
    task_description: string,
    phase_title: string,
    dailies_date: string,
    start_time: string,
    estimated_time_minutes: number,
    is_completed: boolean,
};

export interface DailyTableProps {
    count: number,
    page: number,
    rows: Daily[],
    rowsPerPage: number,
    completed: boolean,
    // we will be displaying all tasks in a single page in a vertically scrollable table
}

export interface DailyCalendarProps {
    goal_phases: string[],
    dailies: Daily[],
}

export interface Stats {
    remaining_tasks_today: number | null,
    completed_tasks_today: number | null,
    ongoing_goals: number | null,
    completed_goals: number | null,
    tasks_today_list: Daily[],
};

export interface Goal {
    title: string,
    total_dailies: number,
    completed_dailies: number,
    deadline: string,
};    

