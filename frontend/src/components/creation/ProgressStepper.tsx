const GOAL_STEPS = [
    { id: "define_goal", label: "Define Goal" },
    { id: "get_prerequisites", label: "Clarify Details" },
    { id: "refine_phases", label: "Build Plan" },
    { id: "refine_dailies", label: "Daily Actions" },
];
  
type StepID = typeof GOAL_STEPS[number]["id"];

export default function ProgressStepper(
    { current, onStepClick, }: {
    current: StepID;
    onStepClick?: (step: StepID) => void;
}) {
  return (
    <div className="w-full flex items-center justify-between px-4 py-6">
        {GOAL_STEPS.map((step, index) => {
            const currentIndex = GOAL_STEPS.findIndex(s => s.id === current);

            const isCompleted = index < currentIndex;
            const isCurrent = index === currentIndex;
            const isUpcoming = index > currentIndex;

            return (
                <div
                    key={step.id}
                    className="flex-1 flex flex-col items-center relative"
                >
                    {/* horizontal connector line */}
                    {index > 0 && (
                        <div
                            className={`absolute top-4 left-0 w-full h-[2px] ${
                            isCompleted ? "bg-blue-600" : "bg-gray-300"
                            }`}
                            style={{
                                transform: "translate(-50%, 50%)",
                            }}
                        />
                    )}
      
                    {/* step circle */}
                    <button
                        onClick={() => onStepClick && onStepClick(step.id)}
                        disabled={!onStepClick}
                        className={`
                        relative z-10
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border transition
                        ${isCurrent ? "bg-blue-600 text-white border-blue-600 shadow" : ""}
                        ${isCompleted ? "bg-blue-100 text-blue-700 border-blue-300" : ""}
                        ${isUpcoming ? "bg-gray-100 text-gray-400 border-gray-300" : ""}
                        `}
                    >
                        {index + 1}
                    </button>
      
                    {/* label */}
                    <span
                        className={`text-xs mt-2 text-center w-20 leading-tight ${
                        isCurrent
                            ? "text-blue-700 font-medium"
                            : isCompleted
                            ? "text-gray-500"
                            : "text-gray-400"
                        }`}
                    >
                        {step.label}
                    </span>
                </div>
            );
        })}
    </div>
  );
}
