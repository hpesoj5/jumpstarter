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

from backend.schemas import (FollowUp, APIResponse, ConfirmRequest, APIRequest,
                            DefinitionsCreate, 
                            GoalPrerequisites, 
                            PhaseGeneration,
                            DailiesGeneration, DailiesPost,)

router = APIRouter(prefix="/create", tags=["Goals"])

@router.post("/load", response_model=APIResponse)
def load(request: APIRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    print(request)
    if request.user_id == None or request.user_id == -1 or request.user_id != user_id:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        last_response = get_model_latest_response(request.user_id, db)
        if last_response == None:
            default = FollowUp(status='follow_up_required', question_to_user="What would you like to achieve today?")
            return APIResponse(phase_tag="define_goal", ret_obj=default)
        user_db_session = get_user_session(request.user_id, db)
        if user_db_session.phase_tag == "generate_dailies":
            dailies_obj = DailiesGeneration.model_validate_json(user_db_session.dailies_obj)
            curr_phase = dailies_obj.dailies[-1].phase_title
            user_phases = PhaseGeneration.model_validate_json(user_db_session.phases_obj)
            phase_titles = [p.title for p in user_phases.phases]
            ret_obj = DailiesPost(**(dailies_obj.model_dump()), goal_phases=phase_titles, curr_phase=curr_phase)
            return APIResponse(phase_tag="generate_dailies", ret_obj=ret_obj)
        return APIResponse(phase_tag=user_db_session.phase_tag, ret_obj=last_response)

@router.post("/query", response_model=APIResponse)
def query(request: APIRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.user_id == None or request.user_id != user_id:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        user_db_session = get_user_session(request.user_id, db)
        response_raw = get_llm_response(user_db_session, request.user_input, db)
        response_parsed = parse_response(response_raw)
        update_session_chat_history(user_db_session, request.user_input, response_raw, db)
        db.commit()

        if isinstance(response_parsed, GoalPrerequisites): # auto transition
            confirm_request = ConfirmRequest(user_id=request.user_id, confirm_obj=response_parsed)
            return confirm(confirm_request, db)
        
        elif isinstance(response_parsed, PhaseGeneration):
            update_session_phase_tag(user_db_session, "refine_phases", db)
        return APIResponse(phase_tag=user_db_session.phase_tag, ret_obj=response_parsed)
    
@router.post("/confirm", response_model=APIResponse)
def confirm(request: ConfirmRequest, user_id = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.user_id == None or request.user_id != user_id:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        user_db_session = get_user_session(request.user_id, db)
        if isinstance(request.confirm_obj, DefinitionsCreate):
            update_session_goal(user_db_session, request.confirm_obj, db)
            update_session_phase_tag(user_db_session, "get_prerequisites", db)
            transition = APIRequest(user_id=request.user_id, user_input=f'My goal is {request.confirm_obj.model_dump_json()}\nWhat prerequisites do you need from me?')
            return query(transition, db)
        elif isinstance(request.confirm_obj, GoalPrerequisites):
            update_session_prereq(user_db_session, request.confirm_obj, db)
            update_session_phase_tag(user_db_session, "refine_phases", db)
            transition = APIRequest(user_id=request.user_id, user_input=f'My goal is {user_db_session.goal_obj}\nMy prerequisites are {request.confirm_obj.model_dump_json()}\nWhat should the plan look like?')
            return query(transition, db)
        elif isinstance(request.confirm_obj, PhaseGeneration): # and user_db_session.phase_tag != "refine_phases": forgot why i added this condition.
            update_session_phases(user_db_session, request.confirm_obj, db)
            update_session_phase_tag(user_db_session, "generate_dailies", db)

            phase_titles = [p.title for p in request.confirm_obj.phases]
            new_dailies = generate_dailies(user_db_session, request.confirm_obj.phases[0], db)
            update_session_dailies(user_db_session, new_dailies, db)
            ret_obj = DailiesPost(**(new_dailies.model_dump()), goal_phases=phase_titles, curr_phase=request.confirm_obj.phases[0].title)
            return APIResponse(phase_tag="generate_dailies", ret_obj=ret_obj)
        elif isinstance(request.confirm_obj, DailiesGeneration):
            update_session_dailies(user_db_session, request.confirm_obj, db)
            curr_phase = request.confirm_obj.dailies[-1].phase_title
            user_phases = PhaseGeneration.model_validate_json(user_db_session.phases_obj)

            if curr_phase == user_phases.phases[-1].title: # last daily is from the final phase -- goal is completed
                goal_json = json.loads(user_db_session.goal_obj)
                prereq_json = json.loads(user_db_session.prereq_obj)
                phases_json = json.loads(user_db_session.phases_obj)
                goal_db = insert_goal(goal_json, prereq_json, request.user_id, db)
                db_phases_list = insert_phases(phases_json, goal_db.id, db)
                insert_dailies(request.confirm_obj, db_phases_list, db)
                change_user_session(request.user_id, db)
                return load(APIRequest(user_id=request.user_id, user_input=""), db)
            else: # transition to generating next phase's dailies
                phase_titles = [p.title for p in user_phases.phases]
                next_phase = phase_titles.index(curr_phase)+1
                
                new_dailies = generate_dailies(user_db_session, user_phases.phases[next_phase], db)
                update_session_dailies(user_db_session, new_dailies, db)

                ret_obj = DailiesPost(**(new_dailies.model_dump()), goal_phases=phase_titles, curr_phase=phase_titles[next_phase])
                return APIResponse(phase_tag="generate_dailies", ret_obj=ret_obj)