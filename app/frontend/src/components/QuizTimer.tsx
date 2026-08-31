import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import { Clock } from "lucide-react";

interface QuizTimerProps {
  isRunning: boolean;
  initialTime?: number;
  className?: string;
  onTimeChange?: (time: number) => void;
}

export interface QuizTimerHandle {
  getTime: () => number;
  reset: (time?: number) => void;
}

export const QuizTimer = forwardRef<QuizTimerHandle, QuizTimerProps>(({ 
  isRunning, 
  initialTime = 0,
  className = "",
  onTimeChange 
}, ref) => {
  const [timeSpent, setTimeSpent] = useState(initialTime);
  const timeRef = useRef(initialTime);

  // Expose the current time without triggering re-renders in the parent
  useImperativeHandle(ref, () => ({
    getTime: () => timeRef.current,
    reset: (time = 0) => {
      setTimeSpent(time);
      timeRef.current = time;
    }
  }));

  // Update initial time if it changes from parent (e.g. resuming)
  useEffect(() => {
    setTimeSpent(initialTime);
    timeRef.current = initialTime;
  }, [initialTime]);

  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    
    if (isRunning) {
      timer = setInterval(() => {
        setTimeSpent(prev => {
          const next = prev + 1;
          timeRef.current = next;
          // Notify parent periodically if needed, to reduce re-renders
          if (onTimeChange && next % 5 === 0) {
             onTimeChange(next);
          }
          return next;
        });
      }, 1000);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isRunning, onTimeChange]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`flex items-center gap-1.5 font-mono ${className}`}>
      <Clock size={16} />
      <span>{formatTime(timeSpent)}</span>
    </div>
  );
});

QuizTimer.displayName = "QuizTimer";
