export interface DefinitionsCreate {
    status: 'definitions_extracted';
    goal: string;
    metric: string;
    purpose: string;
    deadline: string; // string used instead of date object
}

export interface FollowUp {
    status: 'follow_up_required';
    question_to_user: string;
}

export interface GoalResponse {
    session_id: string;
    data: DefinitionsCreate | FollowUpDefinition;
}