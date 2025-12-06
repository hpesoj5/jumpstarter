import React, { useState, useEffect } from "react";
import { DefinitionsCreate } from "@/types/goals.d";
import { Sparkles, Edit, MessageSquare } from "lucide-react";

type DefinitionsFormProps = {
    data: DefinitionsCreate;
    onSubmit: (payload: DefinitionsCreate) => void;
    //onCommentSubmit: (comment: string) => void; // New prop for sending refinement requests
    disabled?: boolean;
};

export default function DefinitionsForm({
    data,
    onSubmit,
    //onCommentSubmit,
    disabled = false,
}: DefinitionsFormProps) {
    const [form, setForm] = useState(data);
    const [loadingTextIndex, setLoadingTextIndex] = useState(0);
    const [ellipsis, setEllipsis] = useState("");

    // const [comment, setComment] = useState("");
    // const [showCommentInput, setShowCommentInput] = useState(false);

    const update = (field: keyof DefinitionsCreate, value: string) => {
        setForm((f) => ({ ...f, [field]: value }));
    };

    const fields: (keyof DefinitionsCreate)[] = ["title", "metric", "purpose", "deadline"];
    const formatLabel = (field: string) => {
        const map: { [key: string]: string } = {
            title: "Goal Title",
            metric: "Key Metric",
            purpose: "Purpose",
            deadline: "Target Deadline",
        };
        return map[field] || field;
    };
    

    const loadingPhrases = [
        "Processing",
        "Researching prerequisites",
        "Reviewing Plan",
        "Generating next step",
    ];

    useEffect(() => {
        if (!disabled) {
            setLoadingTextIndex(0);
            setEllipsis("");
            return;
        }

        const phraseInterval = setInterval(() => {
            setLoadingTextIndex(prevIndex => (prevIndex + 1) % loadingPhrases.length);
        }, 3000);
        const ellipsisInterval = setInterval(() => {
            setEllipsis(prevEllipsis => {
                if (prevEllipsis.length < 3) return prevEllipsis + ".";
                return "";
            });
        }, 500);

        return () => {
            clearInterval(phraseInterval);
            clearInterval(ellipsisInterval);
        };
    }, [disabled]);

    const currentLoadingText = loadingPhrases[loadingTextIndex] + ellipsis;

    // const isCommentReady = comment.trim() !== "" && !disabled;
    const isConfirmReady = !disabled;

    return (
        <div className="w-full mx-auto space-y-8">

            <div className="bg-white p-6 rounded-xl shadow-2xl border border-gray-100 space-y-6">
                <div className="flex flex-col text-xl text-gray-800 items-center gap-2 border-b pb-3">
                    <div className="flex mr-auto pb-3 gap-2">
                        <Edit size={20} className="text-gray-500" />
                        <h3 className="font-bold">Edit Goal Definition</h3>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl shadow-md flex items-start gap-4 w-full">
                        <Sparkles className="w-6 h-6 text-blue-600 flex-shrink-0" />
                        <div>
                            <h2 className="text-lg font-semibold text-blue-800">S.M.A.R.T. Plan</h2>
                            <p className="text-sm text-gray-700 mt-1">
                                Your Goal Assistant has structured your idea into a measurable objective. Please review and make any necessary changes before confirming. <br/>
                                Do ensure your plan is SMART; Specific, Measurable, Achievable, Relevant and Time-bound.
                            </p>
                        </div>
                    </div>
                </div>
                
                
                {fields.map((field) => (
                    <div key={field} className="space-y-1">
                        <label className="block text-sm font-medium text-gray-700">
                            {formatLabel(field)}
                        </label>

                        {field === "purpose" ? (
                            <textarea
                                className="border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg w-full p-3 resize-y min-h-[120px] transition-colors shadow-sm"
                                value={form.purpose || ""}
                                onChange={(e) => update("purpose", e.target.value)}
                                disabled={disabled}
                            />
                        ) : field === "deadline" ? (
                            <input
                                type="date"
                                className="border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg w-full p-3 transition-colors shadow-sm"
                                value={form.deadline ?? ""}
                                onChange={(e) => update("deadline", e.target.value)}
                                disabled={disabled}
                            />
                        ) : (
                            <input
                                type="text"
                                className="border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg w-full p-3 transition-colors shadow-sm"
                                value={form[field] || ""}
                                onChange={(e) => update(field, e.target.value)}
                                disabled={disabled}
                            />
                        )}
                    </div>
                ))}

                <button
                    type="submit"
                    onClick={() => onSubmit(form)}
                    className={`px-6 py-3 rounded-full text-white font-semibold shadow-lg transition-all 
                        ${isConfirmReady
                            ? "bg-green-600 hover:bg-green-700 shadow-green-500/50"
                            : "bg-gray-400 cursor-not-allowed"
                        }`
                    }
                    disabled={disabled}
                >
                    {disabled ? currentLoadingText : "Confirm & Continue"}
                </button>
            </div>

            {/* Action Buttons */}
            {/* <div className="flex justify-between items-center pt-4">
                <button
                    type="button"
                    onClick={() => setShowCommentInput(!showCommentInput)}
                    className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors py-2 px-3 rounded-lg"
                    disabled={disabled}
                >
                    <MessageSquare size={16} />
                    {showCommentInput ? "Hide Refinement Comment" : "Send Feedback to Assistant"}
                </button>
            </div> */}
            
            {/* {showCommentInput && (
                <div className="mt-6 p-4 border-t border-gray-200">
                    <h4 className="text-base font-semibold text-gray-700 mb-3">Refinement Request:</h4>
                    <div className="flex gap-2 items-center">
                        <textarea
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="e.g., 'Please change the goal title to be more specific about the target audience.'"
                            className="border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg p-3 w-full resize-y min-h-[80px] transition-colors text-gray-700 text-sm shadow-sm"
                            disabled={disabled}
                        />
                        <button
                            type="button"
                            onClick={() => onCommentSubmit(comment)}
                            className={`p-3 rounded-full shadow-lg transition-all flex items-center justify-center 
                                ${isCommentReady
                                    ? "bg-blue-600 text-white hover:bg-blue-700 shadow-blue-500/50"
                                    : "bg-gray-200 text-gray-500 cursor-not-allowed"
                                } w-12 h-12 flex-shrink-0`
                            }
                            disabled={!isCommentReady}
                            aria-label="Send Refinement Comment"
                        >
                            <MessageSquare size={20} />
                        </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Submitting a comment will send you back to the Goal Assistant for a refined definition.</p>
                </div>
            )} */}
        </div>
    );
}