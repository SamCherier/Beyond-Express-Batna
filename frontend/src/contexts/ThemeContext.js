import React, { createContext, useContext, useState, useEffect } from 'react';

// Chameleon UI Theme Context
// Gère les thèmes dynamiques : AUTO, LIGHT, DARK, INDEPENDENCE (5 Juillet)

const ThemeContext = createContext();

// Theme modes
export const THEME_MODES = {
  AUTO: 'auto',
  LIGHT: 'light',
  DARK: 'dark',
  INDEPENDENCE: 'independence'  // 5 Juillet (Algerian Independence Day)
};

export const ThemeProvider = ({ children }) => {
  const [themeMode, setThemeMode] = useState(() => {
    // Load saved preference or use AUTO
    const saved = localStorage.getItem('chameleon_theme');
    if (saved && Object.values(THEME_MODES).includes(saved)) {
      return saved;
    }
    return THEME_MODES.AUTO;
  });
  
  const [effectiveTheme, setEffectiveTheme] = useState(THEME_MODES.LIGHT);
  
  // Détecte si c'est le 5 Juillet (Algerian Independence Day)
  const isIndependenceDay = () => {
    const now = new Date();
    return now.getMonth() === 6 && now.getDate() === 5; // July 5
  };
  
  // Détecte si c'est la nuit (20h - 6h)
  const isNightTime = () => {
    const hour = new Date().getHours();
    return hour >= 20 || hour < 6;
  };
  
  // Calcule le thème effectif
  useEffect(() => {
    const calculateTheme = () => {
      if (themeMode === THEME_MODES.AUTO) {
        // Priority: Independence Day > Night > Day
        if (isIndependenceDay()) {
          return THEME_MODES.INDEPENDENCE;
        } else if (isNightTime()) {
          return THEME_MODES.DARK;
        } else {
          return THEME_MODES.LIGHT;
        }
      }
      return themeMode;
    };
    
    const newTheme = calculateTheme();
    setEffectiveTheme(newTheme);
    
    // Apply theme to document root
    const root = document.documentElement;
    
    // Remove all theme classes
    root.classList.remove('dark', 'independence');
    
    // Add appropriate theme class
    if (newTheme === THEME_MODES.DARK) {
      root.classList.add('dark');
    } else if (newTheme === THEME_MODES.INDEPENDENCE) {
      root.classList.add('independence');
    }
    
    // Set data attribute for CSS
    root.setAttribute('data-theme', newTheme);
    
    // Update localStorage
    localStorage.setItem('chameleon_theme', themeMode);
    
  }, [themeMode]);
  
  // Check for auto-theme changes every minute
  useEffect(() => {
    if (themeMode === THEME_MODES.AUTO) {
      const interval = setInterval(() => {
        const newTheme = isIndependenceDay() 
          ? THEME_MODES.INDEPENDENCE 
          : isNightTime() 
            ? THEME_MODES.DARK 
            : THEME_MODES.LIGHT;
        
        if (newTheme !== effectiveTheme) {
          setEffectiveTheme(newTheme);
          
          const root = document.documentElement;
          root.classList.remove('dark', 'independence');
          
          if (newTheme === THEME_MODES.DARK) {
            root.classList.add('dark');
          } else if (newTheme === THEME_MODES.INDEPENDENCE) {
            root.classList.add('independence');
          }
          
          root.setAttribute('data-theme', newTheme);
        }
      }, 60000); // Check every minute
      
      return () => clearInterval(interval);
    }
  }, [themeMode, effectiveTheme]);
  
  const setTheme = (mode) => {
    if (Object.values(THEME_MODES).includes(mode)) {
      setThemeMode(mode);
    }
  };
  
  const cycleTheme = () => {
    // Cycle through: AUTO -> LIGHT -> DARK -> INDEPENDENCE -> AUTO
    const modes = [THEME_MODES.AUTO, THEME_MODES.LIGHT, THEME_MODES.DARK, THEME_MODES.INDEPENDENCE];
    const currentIndex = modes.indexOf(themeMode);
    const nextIndex = (currentIndex + 1) % modes.length;
    setThemeMode(modes[nextIndex]);
  };
  
  // Legacy compatibility
  const toggleTheme = () => {
    if (themeMode === THEME_MODES.LIGHT) {
      setThemeMode(THEME_MODES.DARK);
    } else if (themeMode === THEME_MODES.DARK) {
      setThemeMode(THEME_MODES.LIGHT);
    } else {
      setThemeMode(THEME_MODES.LIGHT);
    }
  };
  
  const value = {
    theme: effectiveTheme,     // Legacy compatibility
    themeMode,                 // Current mode setting (auto, light, dark, independence)
    effectiveTheme,            // Actual applied theme
    setTheme,
    toggleTheme,               // Legacy compatibility
    cycleTheme,
    isIndependenceDay: isIndependenceDay(),
    isNightTime: isNightTime(),
    THEME_MODES
  };
  
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
