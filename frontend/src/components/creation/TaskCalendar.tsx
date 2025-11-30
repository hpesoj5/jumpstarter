import React, { useMemo, useState, useCallback, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import { EventClickArg, } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin, { DateClickArg } from '@fullcalendar/interaction'; 
import { addMinutes, format } from "date-fns";
import { DailyCreate, DailiesPost, DailiesGeneration } from "@/types/goals"

interface FullCalendarEvent {
    title: string;
    start: Date; 
    end: Date;   

    extendedProps: {
        phaseTitle: string;
        estimatedTimeMinutes: number;
        taskIndex: number;
        startDate: string; // YYYY-MM-DD
        startTime: string; // HH:MM
        taskDescription: string;
    };
}

// --- TaskModal Props (Defining the data structure for the modal form) ---

interface TaskData {
    taskIndex?: number; // Used for identifying which task to edit/delete
    phaseTitle: string;
    taskDescription: string;
    startDate: string; // YYYY-MM-DD
    startTime: string; // HH:MM
    estimatedTimeMinutes: number;
}

interface TaskModalProps {
    isOpen: boolean;
    mode: 'add' | 'edit';
    initialTaskData: TaskData;
    modalPhases: string[];
    onClose: () => void;
    onSave: (data: TaskData) => void; 
    onDelete?: (taskIndex: number) => void; // needs idx to delete
}

export const transformDailiesToEvents = (
    dailiesGeneration: DailiesGeneration,
): FullCalendarEvent[] => {
    return dailiesGeneration.dailies.map((daily: DailyCreate, index: number) => {
        const start = new Date(`${daily.dailies_date}T${daily.start_time}`);
        const end = addMinutes(start, daily.estimated_time_minutes);

        return {
            title: `${daily.phase_title}: ${daily.task_description}`,
            start: start,
            end: end,
            extendedProps: {
                phaseTitle: daily.phase_title,
                estimatedTimeMinutes: daily.estimated_time_minutes,
                taskIndex: index,
                startDate: daily.dailies_date,
                startTime: daily.start_time,
                taskDescription: daily.task_description,
            },
        };
    });
};

const defaultModalData: TaskData = {
    taskIndex: undefined,
    phaseTitle: '',
    taskDescription: '',
    startDate: format(new Date(), 'yyyy-MM-dd'),
    startTime: '09:00',
    estimatedTimeMinutes: 60,
};

// --- TaskModal Component ---

const TaskModal: React.FC<TaskModalProps> = ({ 
    isOpen, mode, initialTaskData, modalPhases, onClose, onSave, onDelete,
}) => {
    const [formData, setFormData] = useState<TaskData>(initialTaskData);

    useEffect(() => {
        setFormData(initialTaskData);
    }, [initialTaskData, isOpen]);

    if (!isOpen) return null;

    const isEditMode = mode === 'edit';
    const title = isEditMode ? 'Edit/Delete Daily Task' : 'Add New Daily Task';

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ 
            ...prev, 
            [name]: name === 'estimatedTimeMinutes' ? parseInt(value) || 0 : value 
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(formData);
        onClose();
    };

    const handleDelete = () => {
        if (typeof formData.taskIndex === 'number' && onDelete) {
            console.log(`[UI Action] Preparing to delete task Index: ${formData.taskIndex}`);
            onDelete(formData.taskIndex);
            onClose();
        }
    };

    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg transform transition-all">
                <div className="p-6 border-b border-gray-200">
                    <h3 className="text-2xl font-bold text-gray-800">{title}</h3>
                </div>

                {/* Task Description */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Phase</label>
                        <select
                            name="phaseTitle"
                            value={formData.phaseTitle}
                            onChange={handleChange}
                            required
                            className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                        {modalPhases.map((phase) => (
                            <option key={phase} value={phase}>{phase}</option>
                        ))}
                    </select>
                    </div>

                    {/* Task Description */}
                    <div>
                        <label htmlFor="taskDescription" className="block text-sm font-medium text-gray-700">Task Description</label>
                        <textarea
                            id="taskDescription"
                            name="taskDescription"
                            rows={3}
                            value={formData.taskDescription}
                            onChange={handleChange}
                            required
                            className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="e.g., Complete chapter 3 analysis for report"
                        />
                    </div>

                    <div className="flex space-x-4">
                        {/* Start Date */}
                        <div className="flex-1">
                            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">Date</label>
                            <input
                                id="startDate"
                                type="date"
                                name="startDate"
                                value={formData.startDate}
                                onChange={handleChange}
                                required
                                className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                            />
                        </div>

                        {/* Start Time */}
                        <div className="flex-1">
                            <label htmlFor="startTime" className="block text-sm font-medium text-gray-700">Start Time</label>
                            <input
                                id="startTime"
                                type="time"
                                name="startTime"
                                value={formData.startTime}
                                onChange={handleChange}
                                required
                                className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                            />
                        </div>
                    </div>

                    {/* Estimated Time */}
                    <div>
                        <label htmlFor="estimatedTimeMinutes" className="block text-sm font-medium text-gray-700">Estimated Duration (Minutes)</label>
                        <input
                            id="estimatedTimeMinutes"
                            type="number"
                            name="estimatedTimeMinutes"
                            min="5"
                            step="5"
                            value={formData.estimatedTimeMinutes}
                            onChange={handleChange}
                            required
                            className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                    </div>

                    {/* Action Buttons */}
                    <div className="pt-4 flex justify-between items-center">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition duration-150"
                        >
                            Cancel
                        </button>
                        
                        <div className="space-x-3">
                            {isEditMode && typeof formData.taskIndex === 'number' && (
                                <button
                                    type="button"
                                    onClick={handleDelete}
                                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg shadow-md hover:bg-red-700 transition duration-150"
                                >
                                    Delete
                                </button>
                            )}
                            <button
                                type="submit"
                                className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg shadow-md hover:bg-indigo-700 transition duration-150"
                            >
                                {isEditMode ? 'Save Changes' : 'Add Task'}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
};

// --- DailiesCalendar Component ---

export default function DailiesCalendar(
    { dailiesPost, onConfirm, disabled = false }: { 
    dailiesPost: DailiesPost,
    onConfirm: (dailies: DailiesPost) => void,
    disabled?: boolean
}) {
    // Initial state set using the provided data from props
    const [dailiesData, setDailiesData] = useState<DailiesPost>(dailiesPost); 
    const [modalData, setModalData] = useState<TaskData>(defaultModalData);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalMode, setModalMode] = useState<'add' | 'edit'>('add');
    
    useEffect(() => {
        setDailiesData(dailiesPost);
    }, [dailiesPost]);

    const events = useMemo(
        () => transformDailiesToEvents(dailiesData),
        [dailiesData],
    );

    const currentPhaseIndex = dailiesData.goal_phases.indexOf(dailiesData.curr_phase);
    const allowedPhases = currentPhaseIndex >= 0
        ? dailiesData.goal_phases.slice(0, currentPhaseIndex + 1)
        : dailiesData.goal_phases;

    // Handler for clicking an empty time slot (ADD mode)
    const handleDateClick = useCallback((info: DateClickArg) => {
        // FullCalendar provides dateStr in YYYY-MM-DD[T]HH:MM:SS format
        const datePart = info.dateStr.split('T')[0]; 
        const timePart = info.dateStr.includes('T') ? format(info.date, 'HH:mm') : '09:00'; // Set default time if only date is clicked
        
        setModalData({
            ...defaultModalData,
            phaseTitle: dailiesData.curr_phase, // Phase is set to curr_phase
            startDate: datePart,
            startTime: timePart,
        });
        setModalMode('add');
        setIsModalOpen(true);
    }, [dailiesData.curr_phase]);

    // Handler for clicking an existing event (edit/delete)
    const handleEventClick = useCallback((info: EventClickArg) => {
        const event = info.event;

        // Use extendedProps to get the original data saved during transformation
        setModalData({
            taskIndex: event.extendedProps.taskIndex,
            phaseTitle: event.extendedProps.phaseTitle,
            taskDescription: event.extendedProps.taskDescription,
            startDate: event.extendedProps.startDate,
            startTime: event.extendedProps.startTime.slice(0, 5),
            estimatedTimeMinutes: event.extendedProps.estimatedTimeMinutes,
        });
        setModalMode('edit');
        setIsModalOpen(true);
    }, []);

    const closeModal = () => {
        setIsModalOpen(false);
        setModalData(defaultModalData);
    };

    // save new or updated task data.
    const handleSave = useCallback((data: TaskData) => {
        let taskToSave = data;
        let newDailies = [...dailiesData.dailies];
        
        // add Operation
        if (typeof data.taskIndex !== 'number') {
            const newTask: DailyCreate = {
                phase_title: taskToSave.phaseTitle,
                dailies_date: taskToSave.startDate,
                start_time: taskToSave.startTime,
                estimated_time_minutes: taskToSave.estimatedTimeMinutes,
                task_description: taskToSave.taskDescription,
            };

            newDailies.push(newTask);
        } 
        // update Operation (Index provided)
        else {
            const taskIndex = data.taskIndex;
            if (taskIndex >= 0 && taskIndex < newDailies.length) {
                newDailies[taskIndex] = {
                    phase_title: taskToSave.phaseTitle,
                    dailies_date: taskToSave.startDate,
                    start_time: taskToSave.startTime,
                    estimated_time_minutes: taskToSave.estimatedTimeMinutes,
                    task_description: taskToSave.taskDescription,
                };
            }
        }

        setDailiesData(prev => ({
            ...prev,
            dailies: newDailies
        }));
    }, [dailiesData.dailies]);

    // Handles deleting a task based on its array index
    const handleDelete = useCallback((taskIndex: number) => {
        const newDailies = dailiesData.dailies.filter((_, index) => index !== taskIndex);
        setDailiesData(prev => ({
            ...prev,
            dailies: newDailies
        }));
    }, [dailiesData.dailies]);

    return (
        <div className="p-4 bg-gray-50 min-h-screen">
            <div className="bg-white rounded-xl shadow-2xl max-w-4xl mx-auto my-8 p-6">
                <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 border-b pb-2">Daily Task Manager</h1>
                <FullCalendar
                    plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin]}
                    initialView="dayGridMonth"
                    headerToolbar={{
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,timeGridWeek,timeGridDay,listAll',
                    }}
                    views={{
                        listAll: {
                            type: 'listYear',
                            buttonText: 'list',
                            duration: { years: 10 },
                            listDayFormat: { year: 'numeric', month: 'long', day: 'numeric' },
                            listDaySideFormat: { weekday: 'long' }
                        },
                    }}
                    events={events}
                    editable={!disabled}
                    selectable={!disabled}
                    
                    dateClick={disabled? undefined : handleDateClick}
                    eventClick={disabled? undefined : handleEventClick}

                    height="auto"

                    // Custom content rendering for event content
                    eventContent={(eventInfo) => (
                        <div className="p-1 text-xs sm:text-sm overflow-hidden text-white">
                            <b className="block font-semibold">{eventInfo.timeText}</b>
                            <i className="block truncate">{eventInfo.event.title}</i>
                            <p className="text-[0.6em] opacity-80 m-0">
                            Phase: {eventInfo.event.extendedProps.phaseTitle} ({
                            eventInfo.event.extendedProps.estimatedTimeMinutes} min)
                            </p>
                        </div>
                    )}
                />

                <button
                    onClick={() => onConfirm(dailiesData)}
                    disabled={disabled}
                    className={`
                        px-4 py-2 rounded text-white w-full md:w-auto font-medium 
                        ${disabled ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"}
                    `}
                >
                    {disabled ? "Generating Next Phase..." : "Finalise Phase Dailies"}
                </button>

                <TaskModal 
                    isOpen={isModalOpen}
                    mode={modalMode}
                    initialTaskData={modalData}
                    modalPhases={allowedPhases}
                    onClose={closeModal}
                    onSave={handleSave}
                    onDelete={handleDelete}
                />
            </div>
        </div>
    );
};