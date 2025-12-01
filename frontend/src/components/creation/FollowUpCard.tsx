import React, { useState, useEffect } from "react";
import { FollowUp } from "@/types/goals.d"; // Use relative path for consistency
import { Send } from "lucide-react"; // Use Send for submission, CornerUpLeft for refine

export default function FollowUpCard(
    { data, onSubmit, disabled=false } : 
    { 
        data: FollowUp;
        onSubmit: (answer: string) => void;
        disabled?: boolean;
    } ) 
{
    const [answer, setAnswer] = useState("");
    const [loadingTextIndex, setLoadingTextIndex] = useState(0);
    const [ellipsis, setEllipsis] = useState("");

    const loadingPhrases = [
        " is analyzing your input",
        " is structuring your idea",
        " is reviewing the plan",
    ];

    useEffect(() => {
        if (!disabled) { // Reset state when loading is complete
            setLoadingTextIndex(0);
            setEllipsis("");
            return;
        }

        const phraseInterval = setInterval(() => { // cycle through loadingPhrases
            setLoadingTextIndex(prevIndex => (prevIndex + 1) % loadingPhrases.length);
        }, 5000);

        const ellipsisInterval = setInterval(() => { // Animate Ellipsis
            setEllipsis(prevEllipsis => {
                if (prevEllipsis.length < 3) return prevEllipsis + ".";
                return "";
            });
        }, 500);
        
        return () => { // Cleanup function
            clearInterval(phraseInterval);
            clearInterval(ellipsisInterval);
        };
    }, [disabled]);

    const currentLoadingText = loadingPhrases[loadingTextIndex] + ellipsis;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (answer.trim() && !disabled) {
            onSubmit(answer);
        }
    }
    const isReadyToSubmit = answer.trim() !== "" && !disabled;

    return (
        <div className="w-full mx-auto space-y-6 pt-4">

            {/* Speech Bubble (Right-aligned) */}
            <div className="container flex justify-end">
                <div className="max-w-[90%]">
                    <div className="bg-sky-200/50 text-gray-800 p-4 rounded-xl rounded-br-none shadow-md">
                        <p className="text-lg leading-relaxed">
                            {data.question_to_user}
                        </p>
                    </div>
                    
                    <p className="text-xs text-right text-gray-500 mt-1">
                        Goal Assistant
                        {disabled && ( <span>{currentLoadingText}</span> )}
                    </p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                
                <div className="flex gap-2 items-center">
                    <input
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        placeholder="Type your reply here..."
                        className="border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-3xl p-3 pr-5 pl-5 w-full transition-colors text-gray-700 text-base shadow-sm"
                        disabled={disabled}
                    />

                    <button
                        type="submit"
                        className={`p-3 rounded-full shadow-md transition-all flex items-center justify-center 
                            ${isReadyToSubmit
                                ? "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-sky-700/50"
                                : "bg-gray-200 text-gray-500 cursor-not-allowed"
                            } w-12 h-12 flex-shrink-0`
                        }
                        disabled={!isReadyToSubmit}
                        aria-label="Send Answer"
                    >
                        <Send size={20} />
                    </button>
                </div>
            </form>
        </div>
    );
}