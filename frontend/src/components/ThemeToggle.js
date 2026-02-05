import React, { useState } from 'react';
import { Sun, Moon, Sparkles, Zap } from 'lucide-react';
import { useTheme, THEME_MODES } from '@/contexts/ThemeContext';

const ThemeToggle = () => {
  const { themeMode, effectiveTheme, cycleTheme, setTheme, isIndependenceDay, isNightTime } = useTheme();
  const [clickCount, setClickCount] = useState(0);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Secret toggle: Triple-click to reveal advanced theme selector
  const handleClick = (e) => {
    if (e.detail === 3) {
      setShowAdvanced(!showAdvanced);
      setClickCount(0);
    } else {
      cycleTheme();
    }
  };
  
  // Theme icon based on effective theme
  const getThemeIcon = () => {
    switch (effectiveTheme) {
      case THEME_MODES.DARK:
        return <Moon className="w-5 h-5" />;
      case THEME_MODES.INDEPENDENCE:
        return <Sparkles className="w-5 h-5 text-green-600" />;
      default:
        return <Sun className="w-5 h-5" />;
    }
  };
  
  // Theme label
  const getThemeLabel = () => {
    switch (themeMode) {
      case THEME_MODES.AUTO:
        return 'Auto';
      case THEME_MODES.LIGHT:
        return 'Jour';
      case THEME_MODES.DARK:
        return 'Nuit';
      case THEME_MODES.INDEPENDENCE:
        return '🇩🇿 5 Juillet';
      default:
        return '';
    }
  };
  
  return (
    <div className="relative">
      <button
        onClick={handleClick}
        className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 independence:bg-green-100 hover:bg-gray-300 dark:hover:bg-gray-600 independence:hover:bg-green-200 transition-all relative group"
        aria-label="Toggle theme"
        title="Cliquez pour changer de thème. Triple-clic pour le mode avancé."
      >
        {getThemeIcon()}
        
        {/* Indicator badge */}
        {themeMode === THEME_MODES.AUTO && (
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full flex items-center justify-center">
            <Zap className="w-2 h-2 text-white" />
          </span>
        )}
        
        {/* Tooltip */}
        <span className="absolute left-1/2 -translate-x-1/2 top-full mt-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
          {getThemeLabel()}
        </span>
      </button>
      
      {/* Advanced Theme Selector (Hidden by default, revealed on triple-click) */}
      {showAdvanced && (
        <div className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 independence:bg-green-50 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-3 min-w-[200px] z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase">
            Mode Thème
          </div>
          
          <div className="space-y-1">
            <button
              onClick={() => { setTheme(THEME_MODES.AUTO); setShowAdvanced(false); }}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                themeMode === THEME_MODES.AUTO
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Auto</span>
              {themeMode === THEME_MODES.AUTO && (
                <span className="ml-auto text-xs text-blue-600 dark:text-blue-400">✓</span>
              )}
            </button>
            
            <button
              onClick={() => { setTheme(THEME_MODES.LIGHT); setShowAdvanced(false); }}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                themeMode === THEME_MODES.LIGHT
                  ? 'bg-yellow-100 text-yellow-900'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Sun className="w-4 h-4" />
              <span>Mode Jour</span>
              {themeMode === THEME_MODES.LIGHT && (
                <span className="ml-auto text-xs text-yellow-600">✓</span>
              )}
            </button>
            
            <button
              onClick={() => { setTheme(THEME_MODES.DARK); setShowAdvanced(false); }}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                themeMode === THEME_MODES.DARK
                  ? 'bg-gray-700 text-white'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Moon className="w-4 h-4" />
              <span>Mode Nuit</span>
              {themeMode === THEME_MODES.DARK && (
                <span className="ml-auto text-xs text-gray-300">✓</span>
              )}
            </button>
            
            <button
              onClick={() => { setTheme(THEME_MODES.INDEPENDENCE); setShowAdvanced(false); }}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                themeMode === THEME_MODES.INDEPENDENCE
                  ? 'bg-green-100 text-green-900'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Sparkles className="w-4 h-4 text-green-600" />
              <span>🇩🇿 5 Juillet</span>
              {themeMode === THEME_MODES.INDEPENDENCE && (
                <span className="ml-auto text-xs text-green-600">✓</span>
              )}
            </button>
          </div>
          
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center justify-between">
              <span>Statut:</span>
              <span className="font-medium">{getThemeLabel()}</span>
            </div>
            {isIndependenceDay && (
              <div className="mt-1 text-green-600 font-medium">
                🎉 Joyeux 5 Juillet !
              </div>
            )}
            {isNightTime && themeMode === THEME_MODES.AUTO && (
              <div className="mt-1 text-blue-600">
                🌙 Mode nuit auto
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ThemeToggle;
