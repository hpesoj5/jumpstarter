import React, { useState, useEffect } from "react";
import { PhaseGeneration, Phase } from "@/types/goals.d";

export default function PhaseTimeline(
    { data, onConfirm, onCommentSubmit, disabled=false, }: {
    data: PhaseGeneration;
    onConfirm: (phases: Phase[]) => void;
    onCommentSubmit: (comment: string) => void;
    disabled?: boolean;
}) {
    const [phases, setPhases] = useState<Phase[]>(data.phases);
    const [errors, setErrors] = useState<{ [key: number]: string | null }>({});
    const [comment, setComment] = useState("");

    useEffect(() => {
        setPhases(data.phases.map(p => ({ ...p }))); // deep copy
        setComment("");
        setErrors({});
    }, [data]);

    const updatePhase = (idx: number, field: keyof Phase, value: string) => {
        setPhases((prev) => {
            const updated = prev.map((p, i) =>
                i === idx ? { ...p, [field]: value } : p
            );
            validateDates(updated, idx);
            return updated;
        });
    };

    const validateDates = (updated: Phase[], idx: number) => {
        const phase = updated[idx];
        const prev = updated[idx - 1];
        let error: string | null = null;

        // Check start < end
        if (phase.start_date && phase.end_date) {
            if (new Date(phase.start_date) > new Date(phase.end_date)) {
                error = "Start date must be before end date.";
            }
        }

        // Check start > previous end
        if (prev) {
            if (
                phase.start_date &&
                prev.end_date &&
                new Date(phase.start_date) <= new Date(prev.end_date)
            ) {
                error = `Start date must be after Phase ${idx} end date (${prev.end_date}).`;
            }
        }

        setErrors((e) => ({ ...e, [idx]: error }));
    };

    return (
        <div className="space-y-6">
            <div className="space-y-4">
                {phases.map((phase, i) => (
                    <div key={i} className="border rounded p-4 space-y-3">
                        <h3 className="font-bold">Phase {i + 1}</h3>

                        <div>
                            <label className="block font-medium mb-1">Title</label>
                            <input
                                className="border rounded w-full p-2"
                                type="text"
                                value={phase.title}
                                onChange={(e) =>
                                    updatePhase(i, "title", e.target.value)
                                }
                            />
                        </div>

                        <div>
                            <label className="block font-medium mb-1">Description</label>
                            <textarea
                                className="border rounded w-full p-2"
                                value={phase.description}
                                onChange={(e) =>
                                    updatePhase(i, "description", e.target.value)
                                }
                            />
                        </div>

                        <div>
                            <label className="block font-medium mb-1">Start Date</label>
                            <input
                                type="date"
                                className="border rounded w-full p-2"
                                value={phase.start_date}
                                onChange={(e) =>
                                    updatePhase(i, "start_date", e.target.value)
                                }
                            />
                        </div>

                        <div>
                            <label className="block font-medium mb-1">End Date</label>
                            <input
                                type="date"
                                className="border rounded w-full p-2"
                                value={phase.end_date}
                                onChange={(e) =>
                                    updatePhase(i, "end_date", e.target.value)
                                }
                            />
                        </div>

                        {errors[i] && (
                            <p className="text-red-600 text-sm">{errors[i]}</p>
                        )}
                    </div>
                ))}
            </div>

            <textarea
                className="border rounded w-full p-2"
                placeholder="Comment on these phases..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
            />
            <button
                onClick={() => onCommentSubmit(comment)}
                className={`px-4 py-2 rounded text-white 
                        ${disabled ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"}`
                        }
                disabled={disabled || !comment}
            >
                {disabled ? "Loading..." : "Submit Comment"}
            </button>

            <button
                onClick={() => onConfirm(phases)}
                className={`px-4 py-2 rounded text-white 
                            ${disabled ? "bg-gray-400" : "bg-green-600 hover:bg-green-700"}`
                            }
                disabled={disabled}
            >
                {disabled ? "Loading..." : "Confirm Phases"}
            </button>
        </div>
    );
}