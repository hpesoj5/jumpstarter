import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.utils import (get_current_user,
                            insert_user, insert_goal, insert_phases, insert_dailies,
                            insert_session, get_user_session, change_user_session,
                            update_session_data, update_session_phase_tag, update_session_goal, update_session_prereq, update_session_phases, update_session_dailies,
                            get_model_latest_response, update_session_chat_history,
                            get_llm_response, generate_dailies, parse_response
                            )
from backend.db import get_db

from backend.schemas import (FollowUp, APIResponse, APIRequest, ConfirmRequest,
                            DefinitionsCreate, 
                            GoalPrerequisites, 
                            PhaseGeneration,
                            DailiesGeneration, DailiesPost,
                            GoalCompleted)

router = APIRouter(prefix="/create", tags=["Creation", "Goals"])

@router.post("/reset", response_model=None)
def load(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    change_user_session(user_id, db)
    return None

@router.post("/load", response_model=APIResponse)
def load(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    last_response = get_model_latest_response(user_id, db)
    if last_response == None:
        default = FollowUp(status='follow_up_required', question_to_user="What would you like to achieve today?")
        return APIResponse(phase_tag="define_goal", ret_obj=default)
    user_db_session = get_user_session(user_id, db)
    if user_db_session.phase_tag == "generate_dailies":
        dailies_obj = DailiesPost.model_validate_json(user_db_session.dailies_obj)
        return APIResponse(phase_tag="generate_dailies", ret_obj=dailies_obj)
    return APIResponse(phase_tag=user_db_session.phase_tag, ret_obj=last_response)

@router.post("/query", response_model=APIResponse)
def query(request: APIRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user_input = request.user_input
    user_db_session = get_user_session(user_id, db)
    response_raw = get_llm_response(user_db_session, user_input, db)
    response_parsed = parse_response(response_raw)
    update_session_chat_history(user_db_session, user_input, response_raw, db)
    db.commit()

    if isinstance(response_parsed, FollowUp): # auto transition
        
        confirm_request = ConfirmRequest(user_id=user_id, confirm_obj=response_parsed)
        return confirm(confirm_request, user_id, db)
    
    if isinstance(response_parsed, GoalPrerequisites): # auto transition
        confirm_request = ConfirmRequest(user_id=user_id, confirm_obj=response_parsed)
        return confirm(confirm_request, user_id, db)
    
    elif isinstance(response_parsed, PhaseGeneration):
        update_session_phase_tag(user_db_session, "refine_phases", db)
    return APIResponse(phase_tag=user_db_session.phase_tag, ret_obj=response_parsed)
    
@router.post("/confirm", response_model=APIResponse) # consider clearing the chat history
def confirm(request: ConfirmRequest, user_id = Depends(get_current_user), db: Session = Depends(get_db)):
    user_db_session = get_user_session(user_id, db)
    confirm_obj = request.confirm_obj
    if isinstance(confirm_obj, DefinitionsCreate):
        update_session_goal(user_db_session, confirm_obj, db)
        update_session_phase_tag(user_db_session, "get_prerequisites", db)
        user_input=f'Based on your expertise on the subject, ask me questions about my current knowledge to help your planning for my goal.'
        query_request=APIRequest(user_input=user_input)
        return query(query_request, user_id, db)
    elif isinstance(confirm_obj, GoalPrerequisites):
        update_session_prereq(user_db_session, confirm_obj, db)
        update_session_phase_tag(user_db_session, "refine_phases", db)
        update_session_data(user_db_session, [], db) # clear chat history
        user_input=f'Generate the most suitable initial plan according to my goal, deadline and limitations.'
        query_request=APIRequest(user_input=user_input)
        return query(query_request, user_id, db)
    elif isinstance(confirm_obj, PhaseGeneration): # and user_db_session.phase_tag != "refine_phases": forgot why i added this condition.
        update_session_phases(user_db_session, confirm_obj, db)
        update_session_phase_tag(user_db_session, "generate_dailies", db)

        phase_titles = [p.title for p in confirm_obj.phases]
        new_dailies = generate_dailies(user_db_session, confirm_obj.phases[0], db)
        dailies_post_obj = DailiesPost(**(new_dailies.model_dump()), goal_phases=phase_titles, curr_phase=confirm_obj.phases[0].title)
        update_session_dailies(user_db_session, dailies_post_obj, db)
        return APIResponse(phase_tag="generate_dailies", ret_obj=dailies_post_obj)
    elif isinstance(confirm_obj, DailiesPost):
        update_session_dailies(user_db_session, confirm_obj, db)
        curr_phase = confirm_obj.curr_phase
        phase_titles = confirm_obj.goal_phases

        if curr_phase == phase_titles[-1]: # last daily is from the final phase -- goal is completed
            goal_json = json.loads(user_db_session.goal_obj)
            prereq_json = json.loads(user_db_session.prereq_obj)
            phases_json = json.loads(user_db_session.phases_obj)
            goal_db = insert_goal(goal_json, prereq_json, user_id, db)
            db_phases_list = insert_phases(phases_json, goal_db.id, db)
            insert_dailies(confirm_obj, db_phases_list, db)
            change_user_session(user_id, db)

            return APIResponse(phase_tag="goal_completed", ret_obj=GoalCompleted(goal_title=goal_json['title'], goal_id=goal_db.id) )
            #return load(user_id, db)
        else: # transition to generating next phase's dailies
            next_phase = phase_titles.index(curr_phase)+1
            
            print(curr_phase, phase_titles[next_phase], phase_titles)
            user_phases = PhaseGeneration.model_validate_json(user_db_session.phases_obj)
            new_dailies = generate_dailies(user_db_session, user_phases.phases[next_phase], db)

            next_dailies_post_obj = DailiesPost(**(new_dailies.model_dump()), goal_phases=phase_titles, curr_phase=phase_titles[next_phase])
            update_session_dailies(user_db_session, next_dailies_post_obj, db)
            return APIResponse(phase_tag="generate_dailies", ret_obj=next_dailies_post_obj)