import React, { useState } from "react";
import { FollowUp } from "@/types/goals.d";

export default function FollowUpCard(
    { data, onSubmit, disabled=false, } // parameters
: { // type annotation
        data: FollowUp;
        onSubmit: (answer: string) => void;
        disabled?: boolean,
    } 
) {
    const [answer, setAnswer] = useState("");

    return (
    <form className="space-y-4">
        <p className="text-lg font-medium">{data.question_to_user}</p>

        <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            className="border rounded p-2 w-full"
        />

        <button
        type="submit"
            onClick={() => onSubmit(answer)}
            className={`px-4 py-2 rounded text-white 
                        ${disabled ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"}`
                    }
            disabled={disabled}
            >
            {disabled ? "Loading..." : "Submit"}
        </button>
    </form>
    );
}
