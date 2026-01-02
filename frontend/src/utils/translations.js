/**
 * Ukrainian translations for course categories and difficulty levels
 */

export const CATEGORIES = {
  guitar: 'Гітара',
  drums: 'Барабани',
  vocals: 'Вокал',
  keyboards: 'Клавішні',
  theory: 'Теорія музики',
};

export const LEVELS = {
  beginner: 'Початковий',
  intermediate: 'Середній',
  advanced: 'Просунутий',
  master: 'Майстер',
};

/**
 * Get Ukrainian translation for category
 * @param {string} category - Category key (e.g., 'guitar')
 * @returns {string} Ukrainian translation or original value if not found
 */
export const getCategoryLabel = (category) => {
  return CATEGORIES[category] || category;
};

/**
 * Get Ukrainian translation for difficulty level
 * @param {string} level - Level key (e.g., 'beginner')
 * @returns {string} Ukrainian translation or original value if not found
 */
export const getLevelLabel = (level) => {
  return LEVELS[level] || level;
};

