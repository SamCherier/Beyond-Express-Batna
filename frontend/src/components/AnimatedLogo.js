import React from 'react';
import './AnimatedLogo.css';

const AnimatedLogo = ({ size = 'md' }) => {
  const sizes = {
    sm: 'w-12 h-12',
    md: 'w-20 h-20',
    lg: 'w-32 h-32',
    xl: 'w-48 h-48'
  };

  return (
    <div className={`animated-logo ${sizes[size]} relative`} data-testid="animated-logo">
      <svg
        viewBox="0 0 200 200"
        className="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Background circle with pulse animation */}
        <circle
          cx="100"
          cy="100"
          r="95"
          className="logo-bg"
          fill="#FF5757"
        />
        
        {/* Stylized 'b' letter */}
        <g className="logo-letter">
          <path
            d="M 60 60 L 60 140 Q 60 150 70 150 L 110 150 Q 130 150 130 130 L 130 100 Q 130 80 110 80 L 70 80"
            fill="white"
            strokeWidth="0"
          />
        </g>
        
        {/* Arrow element with slide animation */}
        <g className="logo-arrow">
          <path
            d="M 85 95 L 120 95 L 115 85 L 140 105 L 115 125 L 120 115 L 85 115 Z"
            fill="#FF5757"
            strokeWidth="0"
          />
        </g>
      </svg>
      
      {/* Glow effect */}
      <div className="logo-glow"></div>
    </div>
  );
};

export default AnimatedLogo;