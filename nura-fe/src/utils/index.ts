export const getTodayKey = () => {
  const today = new Date();
  return `reflection-${today.getFullYear()}-${today.getMonth() + 1
    }-${today.getDate()}`;
};