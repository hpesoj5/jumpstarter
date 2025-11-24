import React, { useState, useEffect, useRef } from "react";

interface CarouselProps {
    images: string[];
    autoScrollInterval?: number;
}

export const Carousel: React.FC<CarouselProps> = ({
    images,
    autoScrollInterval = 3000, // 3s
}) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const [isHovered, setIsHovered] = useState(false);

    const total = images.length;

    // Calculate indices for the neighboring slides
    const prevIndex = (currentIndex - 1 + total) % total;
    const nextIndex = (currentIndex + 1) % total;

    const goToNext = () => {
        setCurrentIndex((prevIndex) => (prevIndex = (prevIndex + 1) % total));
    };

    const goToIndex = (index: number) => {
        setCurrentIndex(index);
        // Clear interval on manual interaction to reset the auto-scroll timer
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            // Start a new interval
            intervalRef.current = setInterval(goToNext, autoScrollInterval);
        }
    };

    // Auto-scroll logic
    useEffect(() => {
        if (intervalRef.current) clearInterval(intervalRef.current);

        if (!isHovered) {
            intervalRef.current = setInterval(() => {
                goToNext();
            }, autoScrollInterval);
        }

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [currentIndex, autoScrollInterval, total, isHovered]);

    // Function to determine the CSS class and opacity for a given index
    const getImageStyles = (
        index: number
    ): {
        className: string;
        opacity: number;
        cursor: "pointer" | "default";
    } => {
        // We explicitly define the transition property in the class for reliability
        const baseClasses =
            "absolute top-0 left-0 w-full h-full object-cover rounded-lg shadow-xl transition-all duration-500 ease-in-out";

        let className = baseClasses;
        let opacity = 0;
        let cursor: "pointer" | "default" = "default";

        if (index === currentIndex) {
            className += " z-[2] scale-100 translate-x-0";
            opacity = 1;
            cursor = "default";
        } else if (index === prevIndex) {
            className +=
                " z-[1] scale-90 -translate-x-[18%] rotate-[-6deg] hover:scale-[0.92]";
            opacity = 0.6;
            cursor = "pointer";
        } else if (index === nextIndex) {
            className +=
                " z-[1] scale-90 translate-x-[18%] rotate-[6deg] hover:scale-[0.92]";
            opacity = 0.6;
            cursor = "pointer";
        }
        if (opacity === 0) {
            className += " z-[0] scale-70 translate-x-0";
            opacity = 0;
        }

        return { className, opacity, cursor };
    };

    return (
        <div
            className="relative w-full max-w-lg mx-auto rounded-lg aspect-[4/3] perspective-100"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Image Display Area */}
            <div className="relative w-full h-full">
                {images.map((image, index) => {
                    const { className, opacity, cursor } =
                        getImageStyles(index);

                    return (
                        <img
                            key={index}
                            src={image}
                            alt={`Slide ${index}`}
                            className={className}
                            style={{ opacity: opacity, cursor: cursor }} // Apply dynamic opacity and cursor style
                            // Conditional onClick handler only for immediate neighbors
                            onClick={
                                index === prevIndex || index === nextIndex
                                    ? () => goToIndex(index)
                                    : undefined
                            }
                        />
                    );
                })}
            </div>

            {/* --- Dot Navigation --- */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2 z-[4]">
                {images.map((_, index) => (
                    <button
                        key={index}
                        onClick={() => goToIndex(index)}
                        className={`w-3 h-3 rounded-full ${
                            index === currentIndex ? "bg-white" : "bg-gray-400"
                        }`}
                        aria-label={`Go to slide ${index + 1}`}
                    />
                ))}
            </div>
        </div>
    );
};
