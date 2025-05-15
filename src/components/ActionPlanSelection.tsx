'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { motion, AnimatePresence } from 'framer-motion';

const MotionCard = motion(Card);
const MotionButton = motion(Button);

interface ActionPlanSelectionProps {
  onSelect: (planType: string) => void;
  isLoading: boolean;
  plans: Record<string, string>; // Maps plan type to plan content
}

const ActionPlanSelection: React.FC<ActionPlanSelectionProps> = ({
  onSelect,
  isLoading,
  plans
}) => {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  const handleSelect = (planType: string) => {
    setSelectedPlan(planType);
    onSelect(planType);
  };

  const planTypes = [
    { id: 'action', label: 'Action Plan', description: 'Concrete next moves to take', color: 'from-blue-400 to-indigo-500' },
    { id: 'awareness', label: 'Ongoing Awareness', description: 'A distilled mantra or insight to revisit', color: 'from-amber-400 to-orange-500' },
    { id: 'reminder', label: 'Gentle Reminder', description: 'A future nudge to check on your progress', color: 'from-emerald-400 to-teal-500' },
    { id: 'release', label: 'Release & Let Go', description: 'Acknowledge and set this down', color: 'from-rose-400 to-pink-500' }
  ];

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0, transition: { type: "spring", stiffness: 300 } }
  };

  return (
    <MotionCard 
      className="w-full max-w-lg mx-auto backdrop-blur-sm bg-background/80 dark:bg-card/90 border-neutral-200/20 dark:border-neutral-800/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      whileHover={{ 
        boxShadow: "0 8px 30px rgba(0, 0, 0, 0.12)",
      }}
    >
      <CardHeader className="bg-gradient-to-r from-background/80 to-background via-primary/5 dark:from-card/90 dark:to-card/90 dark:via-primary/10">
        <CardTitle className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80">
          Next Steps
        </CardTitle>
        <CardDescription>
          How would you like to carry this forward?
        </CardDescription>
      </CardHeader>

      <CardContent>
        <motion.div 
          className="grid grid-cols-1 gap-3"
          variants={container}
          initial="hidden"
          animate="show"
        >
          {planTypes.map((plan) => (
            <motion.div key={plan.id} variants={item}>
              <MotionButton
                variant={selectedPlan === plan.id ? "secondary" : "outline"}
                className={`h-auto py-3 px-4 justify-start text-left w-full overflow-hidden relative group ${
                  selectedPlan === plan.id ? 'border-none' : ''
                }`}
                onClick={() => handleSelect(plan.id)}
                disabled={isLoading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {selectedPlan === plan.id && (
                  <motion.div 
                    className={`absolute inset-0 bg-gradient-to-r ${plan.color} opacity-10 dark:opacity-20`}
                    initial={{ x: "-100%" }}
                    animate={{ x: 0 }}
                    transition={{ duration: 0.5 }}
                  />
                )}
                <div className="flex items-center justify-between w-full z-10">
                  <div>
                    <div className={`font-medium ${selectedPlan === plan.id ? `text-transparent bg-clip-text bg-gradient-to-r ${plan.color}` : ''}`}>
                      {plan.label}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {plan.description}
                    </div>
                  </div>
                  {plans[plan.id] && (
                    <Badge variant="secondary" className="ml-2 bg-green-100 text-green-800 hover:bg-green-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700">
                      Generated
                    </Badge>
                  )}
                </div>
              </MotionButton>
            </motion.div>
          ))}
        </motion.div>
      </CardContent>

      {/* Display selected plan content */}
      <AnimatePresence>
        {selectedPlan && plans[selectedPlan] && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <CardFooter className="flex flex-col items-start bg-muted/20 dark:bg-muted/5 border-t border-border/30">
              <h4 className="font-medium text-foreground mb-2">
                Your {planTypes.find(p => p.id === selectedPlan)?.label}
              </h4>
              <motion.p 
                className="text-muted-foreground whitespace-pre-line"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                {plans[selectedPlan]}
              </motion.p>
            </CardFooter>
          </motion.div>
        )}
      </AnimatePresence>

      {isLoading && (
        <CardFooter className="justify-center py-4">
          <motion.div 
            className="flex items-center gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-l-2 border-primary"></div>
            <p className="text-sm text-muted-foreground">Generating your plan...</p>
          </motion.div>
        </CardFooter>
      )}
    </MotionCard>
  );
};

export default ActionPlanSelection; 