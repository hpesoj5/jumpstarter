"use client";
import React, { useState } from 'react';
import { GoalResponse, DefinitionsCreate, FollowUp } from '@/types/goals';

const API_URL = 'http://localhost:8000'; 

export default function GoalSetterForm() {
    const [userInput, setUserInput] = useState('');
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [response, setResponse] = useState<GoalResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const isFollowUp = response?.data.status === 'follow_up_required';
    const isComplete = response?.data.status === 'data_extracted';
    const currentQuestion = isFollowUp
    ? (response.data as FollowUp).question_to_user
    : 'I want to ';

    const handleGoalSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!userInput.trim() || isLoading) return;

        setIsLoading(true);

        const payload = {
            user_input: userInput,
            session_id: sessionId, 
        };
        
        try {
            const res = await fetch(`${API_URL}/goals/define`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || `HTTP error! status: ${res.status}`);
            }

            const newResponse: GoalResponse = await res.json();
            // Update state: Set the new session ID and the API response data
            setResponse(newResponse);
            setSessionId(newResponse.session_id);
            setUserInput(''); // Clear the input field

        } catch (error) {
            console.error('Goal setting failed:', error);
            alert('An error occurred during goal processing.');
        } finally {
            setIsLoading(false);
        }
    };

    if (isComplete) {
        // Render the final, structured goal
        const finalGoal = response.data as DefinitionsCreate;
        return (
            <div className="p-6 bg-green-50 rounded-lg shadow-md">
            <h2 className="text-xl font-bold text-green-700 mb-4">✅ Goal Defined!</h2>
            <p><strong>Goal:</strong> {finalGoal.goal}</p>
            <p><strong>Metric:</strong> {finalGoal.metric}</p>
            <p><strong>Purpose:</strong> {finalGoal.purpose}</p>
            <p><strong>Deadline:</strong> {finalGoal.deadline}</p>
            <button 
                onClick={() => { setResponse(null); setSessionId(null); }}
                className="mt-4 bg-gray-500 text-white px-4 py-2 rounded"
            >
                Define New Goal
            </button>
            </div>
        );
    }

    return (
    <form onSubmit={handleGoalSubmit} className="max-w-md w-full">
        <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">
            {sessionId ? 'Response:' : 'Your Goal:'}
        </label>
        <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500 mb-4">
            <p className="text-blue-800">{currentQuestion}</p>
        </div>
        <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder={isFollowUp ? "Type your answer here..." : "e.g., I want to run a marathon next year"}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
        />
        </div>
        <button
        type="submit"
        className="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold hover:bg-indigo-700 transition duration-150"
        disabled={isLoading}
        >
        {isLoading ? 'Processing...' : (sessionId ? 'Submit Clarification' : 'Define Goal')}
        </button>
    </form>
    );
}