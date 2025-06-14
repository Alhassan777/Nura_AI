/**
 * Level system configuration
 * Each level requires more XP than the previous one
 * The formula used is: baseXP * (level - 1) * levelMultiplier
 * This creates an exponential curve where higher levels require more XP
 */
const BASE_XP = 100; // Base XP required for level 1
const LEVEL_MULTIPLIER = 1.5; // Multiplier for each level

/**
 * Calculate the XP required for a specific level
 * @param level The target level
 * @returns The XP required to reach that level
 */
export const getXpForLevel = (level: number): number => {
  if (level < 1) return 0;
  return Math.floor(BASE_XP * (level - 1) * LEVEL_MULTIPLIER);
};

/**
 * Calculate the user's current level based on their total XP
 * @param totalXp The user's total XP
 * @returns The user's current level
 */
export const getLevelFromXp = (totalXp: number): number => {
  if (totalXp < BASE_XP) return 1;

  let level = 1;
  let xpForNextLevel = getXpForLevel(level + 1);

  while (totalXp >= xpForNextLevel) {
    level++;
    xpForNextLevel = getXpForLevel(level + 1);
  }

  return level;
};


/**
 * Calculate XP progress towards next level
 * @param totalXp The user's total XP
 * @returns Object containing current level, XP progress, and XP required for next level
 */
export const getLevelProgress = (totalXp: number) => {
  const currentLevel = getLevelFromXp(totalXp);
  const xpForCurrentLevel = getXpForLevel(currentLevel);
  const xpForNextLevel = getXpForLevel(currentLevel + 1);
  const xpInCurrentLevel = totalXp - xpForCurrentLevel;
  const xpNeededForNextLevel = xpForNextLevel - xpForCurrentLevel;
  const nextLevelXP = getXpForLevel(getLevelFromXp(totalXp) + 1)
  const progressPercentage = Math.floor((totalXp / nextLevelXP) * 100);



  return {
    currentLevel,
    xpInCurrentLevel,
    xpNeededForNextLevel,
    progressPercentage,
    xpForNextLevel,
  };
};

/**
 * Calculate XP reward for completing a reflection
 * @param streak The user's current streak
 * @returns The XP reward amount
 */
export const getReflectionXpReward = (streak: number): number => {
  // Base XP for completing a reflection
  const baseXp = 20;

  // Bonus XP based on streak (capped at 5x)
  const streakMultiplier = Math.min(5, 1 + (streak * 0.1));

  return Math.floor(baseXp * streakMultiplier);
}; 