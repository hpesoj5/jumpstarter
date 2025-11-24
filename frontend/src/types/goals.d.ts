export type FollowUp = {
    status: 'follow_up_required';
    question_to_user: string;
};
  
export type DefinitionsCreate = {
    status: 'definitions_extracted';
    title: string;
    metric: string;
    purpose: string;
    deadline: string; // ISO date string
};
export type Phase = {
    title: string;
    description: string;
    start_date: string;
    end_date: string;
};
export type PhaseGeneration = {
    status: 'phases_generated';
    phases: Phase[];
};

export type DailyCreate = {
    task_description: string;
    start_date: string;  // ISO date string, e.g. "2025-01-01"
    start_time: string;  // ISO time string, e.g. "09:30:00"
    estimated_time_minutes: number;
    phase_title: string;
};
export type DailiesGeneration = {
    status: "generation_in_process" | "dailies_generated";
    dailies: DailyCreate[];
    last_daily_date: string; // ISO date string
};
export type DailiesPost = DailiesGeneration & {
    goal_phases: string[];
    curr_phase: string;
};
  
export type APIResponse =
  | {
      phase_tag: "define_goal";
      ret_obj: FollowUp | DefinitionsCreate;
    }
  | {
      phase_tag: "get_prerequisites";
      ret_obj: FollowUp;
    }
  | {
      phase_tag: "refine_phases";
      ret_obj: PhaseGeneration;
    }
  | {
      phase_tag: "generate_dailies";
      ret_obj: DailiesPost;
    };

export interface APIRequest {
    user_id: int;
    user_input: string;
}

export interface ConfirmRequest {
    user_id: int;
    confirm_obj: DefinitionsCreate | PhaseGeneration | DailiesGeneration;
}