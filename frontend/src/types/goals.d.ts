export interface DefinitionsCreate {
    status: 'definitions_extracted';
    goal: string;
    metric: string;
    purpose: string;
    deadline: string; // ISO date string
}
export interface FollowUp {
    status: 'follow_up_required';
    question_to_user: string;
}

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
  
export type APIResponse =
    | FollowUp
    | DefinitionsCreate
    | PhaseGeneration;

export interface APIRequest {
    user_id: int;
    user_input: string;
}

export interface ConfirmRequest {
    user_id: int;
    confirm_obj: DefinitionsCreate | PhaseGeneration;
}