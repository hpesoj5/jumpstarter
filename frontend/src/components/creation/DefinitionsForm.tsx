import React, { useState } from "react";
import { DefinitionsCreate } from "@/types/goals.d";

export default function DefinitionsForm(
    { data, onSubmit, disabled=false, }: {
        data: DefinitionsCreate;
        onSubmit: (payload: DefinitionsCreate) => void;
        disabled?: boolean;
}) {
    const [form, setForm] = useState(data);

    const update = (field: keyof DefinitionsCreate, value: string) => {
        setForm((f) => ({ ...f, [field]: value }));
    };

    return (
        <div className="space-y-4">
            {["title", "metric", "purpose", "deadline"].map((field) => (
                <div key={field}>
                    <label className="block font-medium mb-1">{field}</label>

                    {field === "deadline" ? (
                        <input
                            type="date"
                            className="border rounded w-full p-2"
                            value={form.deadline ?? ""}
                            onChange={(e) =>
                                update("deadline", e.target.value)
                            }
                        />
                    ) : (
                        <input
                            className="border rounded w-full p-2"
                            value={form[field as keyof DefinitionsCreate] || ""}
                            onChange={(e) =>
                                update(field as keyof DefinitionsCreate, e.target.value)
                            }
                        />
                    )}
                </div>
            ))}

            <button
                onClick={() => onSubmit(form)}
                className={`px-4 py-2 rounded text-white 
                        ${disabled ? "bg-gray-400" : "bg-green-600 hover:bg-green-700"}`
                        }
                disabled={disabled}
            >
                {disabled ? "Loading..." : "Confirm"}
            </button>
        </div>
    );
}