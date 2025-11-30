"use client"
import { useEffect, useState } from "react";
import FollowUpCard from "@/components/creation/FollowUpCard";
import DefinitionsForm from "@/components/creation/DefinitionsForm";
import PhaseTimeline from "@/components/creation/PhaseTimeline";
import ProgressStepper from "@/components/creation/ProgressStepper";
import DailiesCalendar from "@/components/creation/TaskCalendar";
import { APIResponse, Phase, PhaseGeneration, DefinitionsCreate } from "@/types/goals.d";
import { loadInitialState, sendUserInput, confirmPhase, submitPhaseComment, } from "@/api/creation";

export default function CreatePage() {
    const [apiresonse, setData] = useState<APIResponse | null>(null);
    const [loading, setLoading] = useState(false);

    // Load initial state from backend
    const fetchData = async (fn: () => Promise<APIResponse>) => {
        setLoading(true);
        try {
            const newResponse = await fn();
            setData(newResponse);
            console.log(newResponse)
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
    fetchData(loadInitialState);
    }, []);

    if (!apiresonse) return <p>Loading...</p>;
    
    const disabled = loading;
    return (
        <div className="w-full flex flex-col gap-8">
            <ProgressStepper
                //"define_goal" "get_prerequisites" "refine_phases" "generate_dailies"
                current={apiresonse.phase_tag}
            />
            { (() => {
            const response_data = apiresonse.ret_obj
            switch (response_data.status) {
                case "follow_up_required":
                return (
                    <FollowUpCard
                        key={response_data.question_to_user}
                        data={response_data}
                        onSubmit={(answer) => fetchData(() => sendUserInput(answer))}
                        disabled={disabled}
                    />
                );

                case "definitions_extracted":
                return (
                    <DefinitionsForm
                        data={response_data}
                        onSubmit={(form: DefinitionsCreate) =>
                            fetchData(() => confirmPhase(form))
                        }
                        disabled={disabled}
                    />
                );

                case "phases_generated":
                return (
                    <PhaseTimeline
                        data={response_data}
                        onConfirm={(phases: Phase[]) => {
                            const newPhase: PhaseGeneration = { status: "phases_generated", phases: phases };
                            fetchData(() => confirmPhase(newPhase));
                        }}
                        onCommentSubmit={(phases: Phase[], comment: string) => {
                            const newPhase: PhaseGeneration = { status: "phases_generated", phases: phases };
                            fetchData(() => submitPhaseComment(newPhase, comment))
                        }}
                        disabled={disabled}
                    />
                );

                case "dailies_generated":
                return (
                    <DailiesCalendar 
                        dailiesPost={response_data} 
                        onConfirm={(dailiesPost) => {
                            fetchData(() => confirmPhase(dailiesPost))
                        }}
                        disabled={disabled}
                    />
                );

                default: return <p>Unknown state</p>;
            }
            })()}
        </div>
    );
}
