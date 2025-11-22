"use client"
import { useEffect, useState } from "react";
import FollowUpCard from "@/components/creation/FollowUpCard";
import DefinitionsForm from "@/components/creation/DefinitionsForm";
import PhaseTimeline from "@/components/creation/PhaseTimeline";
import ProgressStepper from "@/components/creation/ProgressStepper";
import { APIResponse, PhaseGeneration, DefinitionsCreate } from "@/types/goals.d";
import { loadInitialState, sendUserInput, confirmPhase, submitPhaseComment, } from "@/api/creation";

export default function CreatePage() {
    const [data, setData] = useState<APIResponse | null>(null);
    const [loading, setLoading] = useState(false);

    // Load initial state from backend
    const fetchData = async (fn: () => Promise<APIResponse>) => {
        setLoading(true);
        try {
            const newData = await fn();
            setData(newData);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
    fetchData(loadInitialState);
    }, []);

    if (!data) return <p>Loading...</p>;
    
    const disabled = loading;
    return (
        <div className="w-full flex flex-col gap-8">
            <ProgressStepper
                //"define_goal" "get_prerequisites" "refine_phases" "refine_dailies"
                current="refine_dailies"//{data.phase_tag}
            />
            { (() => {
            switch (data.status) {
                case "follow_up_required":
                return (
                    <FollowUpCard
                        key={data.question_to_user}
                        data={data}
                        onSubmit={(answer) => fetchData(() => sendUserInput(answer))}
                        disabled={disabled}
                    />
                );

                case "definitions_extracted":
                return (
                    <DefinitionsForm
                        data={data}
                        onSubmit={(form: DefinitionsCreate) =>
                            fetchData(() => confirmPhase(form))
                        }
                        disabled={disabled}
                    />
                );

                case "phases_generated":
                return (
                    <PhaseTimeline
                        data={data}
                        onConfirm={(phases: PhaseGeneration["phases"]) => {
                            const newObj: PhaseGeneration = { ...data, phases };
                            fetchData(() => confirmPhase(newObj));
                        }}
                        onCommentSubmit={(comment: string) =>
                            fetchData(() => submitPhaseComment(data as PhaseGeneration, comment))
                        }
                        disabled={disabled}
                    />
                );

                default: return <p>Unknown state</p>;
            }
            })()}
        </div>
    );
}
