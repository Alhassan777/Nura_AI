import { motion, useSpring, useTransform } from "framer-motion";
import { useEffect, useState } from "react";

interface AnimatedNumberProps {
  value: number;
  className: string;
  suffix?: string;
}

export const AnimatedNumber = ({
  value,
  className,
  suffix = "",
}: AnimatedNumberProps) => {
  const [previousValue, setPreviousValue] = useState(0);
  const [isInitialized, setIsInitialized] = useState(false);

  const spring = useSpring(previousValue, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });
  const display = useTransform(spring, (current) => Math.round(current));

  useEffect(() => {
    if (!isInitialized) {
      // First time: animate from 0 to current value
      spring.set(0);
      setTimeout(() => {
        spring.set(value);
        setPreviousValue(value);
        setIsInitialized(true);
      }, 100);
    } else if (value !== previousValue) {
      // Subsequent updates: animate from previous to new value
      spring.set(previousValue);
      spring.set(value);
      setPreviousValue(value);
    }
  }, [value, previousValue, isInitialized, spring]);

  return (
    <motion.span className={className}>
      <motion.span>{display}</motion.span>
      {suffix && <span>{suffix}</span>}
    </motion.span>
  );
};

export default AnimatedNumber;
