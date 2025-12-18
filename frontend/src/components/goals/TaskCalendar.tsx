"use client"
import React, { useState } from "react";
import FullCalendar from "@fullcalendar/react"
import { EventClickArg } from "@fullcalendar/core";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import listPlugin from "@fullcalendar/list";
import interactionPlugin from "@fullcalendar/interaction"; 
import { addMinutes, format, } from "date-fns";
import { Daily, DailyCalendarProps } from '@/api/config';
import { useClickAway } from "@uidotdev/usehooks";

interface FullCalendarEvent {
    title: string;
    start: Date; 
    end: Date;   
    backgroundColor: string;
    borderColor: string;

    extendedProps: {
        phaseTitle: string;
        estimatedTimeMinutes: number;
        taskIndex: number;
        startDate: string; // YYYY-MM-DD
        startTime: string; // HH:MM
        taskDescription: string;
    };
}

interface TaskData {
    phaseTitle: string,
    taskDescription: string,
    startDate: string, // YYYY-MM-DD
    startTime: string, // HH:MM
    estimatedTimeMinutes: number
}

interface TaskModalProps {
    isOpen: boolean,
    initialTaskData: TaskData,
    onClose: () => void,
}

const COLOR_PALETTE = [
    '#A3E635', // Lime Green
    '#4ADE80', // Emerald Green
    '#34D399', // Medium Sea Green
    '#06B6D4', // Cyan
    '#3B82F6', // Blue
    '#8B5CF6', // Violet
    '#EC4899', // Pink
    '#F43F5E', // Rose
    '#F97316', // Orange
    '#FBBF24', // Amber
    '#A8A29E', // Stone Gray
    '#7C3AED', // Deep Purple
];

const convertToGrayscale = (color: string) => {
    const hex = color.replace('#', '');

    if (hex.length !== 6) {
        throw new Error(`Invalid hex color: ${color}`);
    }

    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);

    const gray = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
    const grayHex = gray.toString(16).padStart(2, '0');

    return `#${grayHex}${grayHex}${grayHex}`;
};

type PhaseColorMap = Record<string, string>;
const getPhaseColor = (phaseTitle: string, phaseColorMap: PhaseColorMap) => {
    return phaseColorMap[phaseTitle] || '#e0e0e0'; // Use the map, fall back to gray
};

export const transformDailiesToEvents = (
    dailiesGeneration: DailyCalendarProps,
    phaseColorMap: PhaseColorMap
): FullCalendarEvent[] => {
    return dailiesGeneration.dailies.map((daily: Daily, index: number) => {
        const start = new Date(`${daily.dailies_date}T${daily.start_time}`);
        const end = addMinutes(start, daily.estimated_time_minutes);
        const color = daily.is_completed ? convertToGrayscale(getPhaseColor(daily.phase_title, phaseColorMap)) : getPhaseColor(daily.phase_title, phaseColorMap);
        return {
            title: `${daily.phase_title}: ${daily.task_description}`,
            start: start,
            end: end,
            backgroundColor: color,
            borderColor: color,

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
    phaseTitle: '',
    taskDescription: '',
    startDate: format(new Date(), 'yyyy-MM-dd'),
    startTime: '09:00',
    estimatedTimeMinutes: 60,
};

const TaskModal: React.FC<TaskModalProps> = ({
    isOpen, initialTaskData, onClose
}: TaskModalProps) => {
    const ref = useClickAway(() => {
        onClose();
    }) as React.RefObject<HTMLDivElement | null>;

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg transform transition-all" ref={ref}>
                <div className="p-6 space-y-4">
                    {/* Task Description */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Phase</label>
                        <div
                        className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                            {initialTaskData.phaseTitle}
                        </div>
                    </div>

                    {/* Task Description */}
                    <div>
                        <label htmlFor="taskDescription" className="block text-sm font-medium text-gray-700">Task Description</label>
                        <div
                            className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                            {initialTaskData.taskDescription}
                        </div>
                    </div>

                    <div className="flex space-x-4">
                        {/* Start Date */}
                        <div className="flex-1">
                            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">Date</label>
                            <div
                            className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                            {initialTaskData.startDate}
                        </div>
                        </div>

                        {/* Start Time */}
                        <div className="flex-1">
                            <label htmlFor="startTime" className="block text-sm font-medium text-gray-700">Start Time</label>
                            <div
                            className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                            {initialTaskData.startTime}
                        </div>
                        </div>
                    </div>

                    {/* Estimated Time */}
                    <div>
                        <label htmlFor="estimatedTimeMinutes" className="block text-sm font-medium text-gray-700">Estimated Duration (Minutes)</label>
                        <div
                            className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-3 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                            {initialTaskData.estimatedTimeMinutes}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="pt-4 flex justify-end items-center">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition duration-150"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default function DailiesCalendar(
    { props, disabled = false }: { 
    props: DailyCalendarProps,
    disabled?: boolean
}) {
    // Initial state set using the provided data from props
    const dailiesData: DailyCalendarProps = props;
    const phaseColorMap: PhaseColorMap = {};
    const [modalData, setModalData] = useState<TaskData>(defaultModalData);
    const [isModalOpen, setIsModalOpen] = useState(false);
    dailiesData.goal_phases.forEach((title, index) => {
        phaseColorMap[title] = COLOR_PALETTE[index % COLOR_PALETTE.length];
    });
    const events = transformDailiesToEvents(dailiesData, phaseColorMap);
    const handleEventClick = (info: EventClickArg) => {
        const event = info.event;
        setModalData({
            phaseTitle: event.extendedProps.phaseTitle,
            taskDescription: event.extendedProps.taskDescription,
            startDate: event.extendedProps.startDate,
            startTime: event.extendedProps.startTime.slice(0, 5),
            estimatedTimeMinutes: event.extendedProps.estimatedTimeMinutes,
        });
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setModalData(defaultModalData);
    }
        
    return (
        <div className="bg-white rounded-xl shadow-2xl p-6">
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
                timeZone='UTC'
                events={events}
                // selectable={!disabled}
                eventClick={disabled? undefined: handleEventClick}
                height="auto"

                // Custom content rendering for event content
                eventContent={(eventInfo) => {
                    return (
                        <div 
                            className="p-1 text-xs sm:text-sm h-full flex flex-col justify-start overflow-hidden"
                            style={{
                                backgroundColor: eventInfo.event.backgroundColor,
                                color: 'black'
                            }}
                        >
                            <i className="block font-semibold truncate leading-tight">{eventInfo.event.title}</i>
                            <p className="text-[0.6em] opacity-90 m-0 leading-snug">
                            Phase: {eventInfo.event.extendedProps.phaseTitle} ({
                            eventInfo.event.extendedProps.estimatedTimeMinutes} min)
                            </p>
                        </div>
                    )}
                }
            />

            <TaskModal
                isOpen={isModalOpen}
                initialTaskData={modalData}
                onClose={closeModal}
            />
        </div>
    );
};
