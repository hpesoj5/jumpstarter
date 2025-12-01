import React from 'react';
import { X, Frown, ArrowRight } from 'lucide-react';

interface AbortModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
}

const AbortModal: React.FC<AbortModalProps> = ({ isOpen, onClose, onConfirm }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-gray-900 bg-opacity-70 flex items-center justify-center p-4" aria-modal="true" role="dialog">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg transform transition-all p-6 relative">
                
                {/* Close Button */}
                <button 
                    onClick={onClose} 
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100 transition"
                    aria-label="Close modal"
                >
                    <X size={20} />
                </button>

                {/* Header */}
                <div className="flex items-center space-x-3 mb-4">
                    <Frown className="text-red-500 w-8 h-8 flex-shrink-0" />
                    <h2 className="text-2xl font-bold text-gray-800">
                        <b>Giving up</b> on your Goal?
                    </h2>
                </div>

                <div className="space-y-4 text-gray-600">
                    <p>
                        Are you certain you want to exit? <br/>
                        All progress in planning this goal will be <b>permanently lost</b> from this session.
                    </p>
                    <p>
                        Taking a break? <br/>
                        You can navigate to other tabs without losing current progress.
                    </p>
                    <div className="p-3 bg-yellow-50 border-l-4 border-yellow-500 rounded-lg text-sm">
                        <p className="font-semibold text-yellow-800">Remember why you started this goal. Don't let a minor hurdle stop your momentum!</p>
                    </div>
                </div>

                {/* Actions */}
                <div className="mt-8 flex justify-end space-x-4">
                    <button
                        onClick={onConfirm}
                        className="px-3 py-3 bg-red-400 rounded-md text-sm font-medium text-white hover:bg-red-300 transition shadow-sm"
                    >
                        Abandon goal
                    </button>
                    <button
                        onClick={onClose}
                        className="px-3 py-3 bg-green-600 rounded-full text-sm font-medium text-white hover:bg-green-700 transition shadow-lg shadow-green-500/50"
                    >
                        <ArrowRight size={16} className="inline mr-1 -mt-0.5" />
                        Continue Goal Setup
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AbortModal;