import React, { useState, useEffect } from "react";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors, DragEndEvent, } from "@dnd-kit/core";
import { SortableContext, arrayMove, horizontalListSortingStrategy, useSortable, } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { PhaseGeneration, Phase } from "@/types/goals.d";

// Single sortable phase card
function SortablePhase(
    { phase, idx, updatePhase, addPhase, deletePhase, disabled, errors, }: {
    phase: Phase;
    idx: number;
    updatePhase: (idx: number, field: keyof Phase, value: string) => void;
    addPhase: (idx: number, position: "left" | "right") => void;
    deletePhase: (idx: number) => void;
    disabled?: boolean;
    errors: { [key: number]: string | null };
}) {
    const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
        id: idx,
    });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    const getDuration = (phase: Phase) => {
        if (!phase.start_date || !phase.end_date) return "";
        const start = new Date(phase.start_date);
        const end = new Date(phase.end_date);
        const diff = Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
        return `${diff} days`;
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            className="flex-shrink-0 w-72 border rounded-lg p-4 bg-white shadow relative"
        >
        <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold text-lg">Phase {idx + 1}</h3>
            <button
                onClick={() => deletePhase(idx)}
                disabled={disabled}
                className="text-red-500 px-3 py-1 text-sm rounded hover:bg-red-100"
            >
                Delete
            </button>
        </div>

        <input
            type="text"
            value={phase.title}
            placeholder="Title"
            disabled={disabled}
            onChange={(e) => updatePhase(idx, "title", e.target.value)}
            className="border rounded w-full p-2 mb-1 focus:ring-2 focus:ring-blue-400"
        />
        <textarea
            value={phase.description}
            placeholder="Description"
            disabled={disabled}
            onChange={(e) => updatePhase(idx, "description", e.target.value)}
            className="border rounded w-full p-2 h-48 focus:ring-2 focus:ring-blue-400 resize-none mb-2"
        />

        <div className="flex space-x-2 mb-2">
            <input
                type="date"
                value={phase.start_date}
                disabled={disabled}
                onChange={(e) => updatePhase(idx, "start_date", e.target.value)}
                className="border rounded w-1/2 p-2 focus:ring-2 focus:ring-blue-400"
            />
            <input
                type="date"
                value={phase.end_date}
                disabled={disabled}
                onChange={(e) => updatePhase(idx, "end_date", e.target.value)}
                className="border rounded w-1/2 p-2 focus:ring-2 focus:ring-blue-400"
            />
        </div>

        <p className="text-gray-500 text-sm mb-1">Duration: {getDuration(phase)}</p>

        <div className="flex justify-between">
            <button
                onClick={() => addPhase(idx, "left")}
                disabled={disabled}
                className="text-blue-600 px-3 py-1 text-sm rounded hover:bg-blue-100"
            >
                <span className="hidden md:inline">+ Left</span>
                <span className="inline md:hidden">+ Top</span>
            </button>
            <button
                onClick={() => addPhase(idx, "right")}
                disabled={disabled}
                className="text-blue-600 px-3 py-1 text-sm rounded hover:bg-blue-100"
            >
                <span className="hidden md:inline">+ Right</span>
                <span className="inline md:hidden">+ Bottom</span>
            </button>
        </div>

        {errors[idx] && <p className="text-red-600 text-sm mt-1">{errors[idx]}</p>}
        </div>
    );
}

// Actual component
export default function PhaseTimeline(
    { data, onConfirm, onCommentSubmit, disabled = false, }: {
    data: PhaseGeneration;
    onConfirm: (phases: Phase[]) => void;
    onCommentSubmit: (phases: Phase[], comment: string) => void;
    disabled?: boolean;
}) {
    const [phases, setPhases] = useState<Phase[]>([]);
    const [comment, setComment] = useState("");
    const [errors, setErrors] = useState<{ [key: number]: string | null }>({});

    useEffect(() => {
        setPhases(data.phases.map((p) => ({ ...p })));
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

        if (phase.start_date && phase.end_date) {
            if (new Date(phase.start_date) > new Date(phase.end_date)) {
                error = "Start date must be before end date.";
            }
        }

        if (prev && phase.start_date && prev.end_date) {
            if (new Date(phase.start_date) <= new Date(prev.end_date)) {
                error = `Start date must be after Phase ${idx} end date (${prev.end_date}).`;
            }
        }

        setErrors((e) => ({ ...e, [idx]: error }));
    };

    const addPhase = (idx: number, position: "left" | "right") => {
        const newPhase: Phase = { title: "", description: "", start_date: "", end_date: "" };
        setPhases((prev) => {
            const updated = [...prev];
            updated.splice(position === "left" ? idx : idx + 1, 0, newPhase);
            return updated;
        });
    };

    const deletePhase = (idx: number) => {
        setPhases((prev) => prev.filter((_, i) => i !== idx));
    };

    // drag and drop
    const sensors = useSensors(
        useSensor(PointerSensor, {
                activationConstraint: { distance: 5 },
                // filter interactive elements
                eventFilter: (event: MouseEvent) => {
                const tag = (event.target as HTMLElement).tagName;
                return !["INPUT", "TEXTAREA", "BUTTON", "SELECT"].includes(tag);
            },
        })
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        if (!over) return;
        const oldIndex = Number(active.id);
        const newIndex = Number(over.id);
        setPhases((prev) => arrayMove(prev, oldIndex, newIndex));
    };

    return (
        <div className="space-y-6">
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <SortableContext items={phases.map((_, i) => i)} strategy={horizontalListSortingStrategy}>
                <div className="w-full overflow-x-auto">
                    <div className="flex flex-col md:flex-row md:flex-nowrap space-y-4 md:space-y-0 md:space-x-4">
                        {phases.map((phase, idx) => (
                        <SortablePhase
                            key={idx}
                            phase={phase}
                            idx={idx}
                            updatePhase={updatePhase}
                            addPhase={addPhase}
                            deletePhase={deletePhase}
                            disabled={disabled}
                            errors={errors}
                        />
                        ))}
                    </div>
                </div>
                </SortableContext>
            </DndContext>
            
            <div className="w-full mt-4">
                {/* Comment Box */}
                <textarea
                    className="border rounded w-full p-2 focus:ring-2 focus:ring-blue-400"
                    placeholder="Comment on these phases..."
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    disabled={disabled}
                />

                {/* Action Buttons */}
                <div className="flex flex-col md:flex-row md:space-x-4 space-y-2 md:space-y-0 mt-2">
                    <button
                        onClick={() => onCommentSubmit(phases, comment)}
                        disabled={disabled || !comment.trim()}
                        className={`
                            px-4 py-2 rounded text-white w-full md:w-auto font-medium 
                            ${disabled ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"}
                        `}
                    >
                        {disabled ? "Submitting..." : "Submit Comment"}
                    </button>

                    <button
                    onClick={() => onConfirm(phases)}
                    disabled={disabled}
                    className={`
                        px-4 py-2 rounded text-white w-full md:w-auto font-medium 
                        ${disabled ? "bg-gray-400" : "bg-green-600 hover:bg-green-700"}
                    `}
                    >
                        {disabled ? "Saving..." : "Confirm Phases"}
                    </button>
                </div>

            </div>
        </div>
    );
}