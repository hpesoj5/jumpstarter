"use client"
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import FollowUpCard from "@/components/creation/FollowUpCard";
import DefinitionsForm from "@/components/creation/DefinitionsForm";
import PhaseTimeline from "@/components/creation/PhaseTimeline";
import ProgressStepper from "@/components/creation/ProgressStepper";
import DailiesCalendar from "@/components/creation/TaskCalendar";
import AbortModal from "@/components/creation/AbortModal";
import { APIResponse, Phase, PhaseGeneration, DefinitionsCreate } from "@/types/goals.d";
import { loadInitialState, sendUserInput, confirmPhase, submitPhaseComment, resetCreation } from "@/api/creation";
import { GOAL_CREATED_EVENT } from "@/components/layout/Sidebar"
import { LogOut } from "lucide-react";

export default function CreatePage() {
    const [apiresonse, setData] = useState<APIResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [isAbortModalOpen, setIsAbortModalOpen] = useState(false);
    const router = useRouter();

    const abortSession = async () => {
        await resetCreation();
        setIsAbortModalOpen(false);
        router.push('/create'); 
        fetchData(loadInitialState);
        return;
    };

    // Load initial state from backend
    const fetchData = async (fn: () => Promise<APIResponse>) => {
        setLoading(true);
        try {
            const newResponse = await fn();
            if (newResponse.phase_tag === 'goal_completed') {
                window.dispatchEvent(new Event(GOAL_CREATED_EVENT));
                router.push('/create');  // redirect to new goal when implemented
                fetchData(loadInitialState); // not needed if redirect
                return;
            }
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
        <div className="w-full flex flex-col gap-8 h-full pb-8">
            <ProgressStepper
                //"define_goal" "get_prerequisites" "refine_phases" "generate_dailies"
                current={apiresonse.phase_tag}
            />
            <div className="flex-grow flex items-center justify-center"> { (() => {
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
            })()}</div>

            <button
                onClick={() => setIsAbortModalOpen(true)}
                className="fixed bottom-8 right-8 
                           bg-red-400 text-white 
                           px-3 py-3 rounded-md
                           flex items-center gap-2 
                           hover:bg-red-500 transition-colors 
                           z-40 focus:outline-none focus:ring-4 focus:ring-red-200"
                disabled={loading}
            >
            <LogOut size={20} />
                Give Up
            </button>

            <AbortModal
                isOpen={isAbortModalOpen}
                onClose={() => setIsAbortModalOpen(false)}
                onConfirm={abortSession}
            />
        </div>
    );
}
