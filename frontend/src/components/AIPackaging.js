import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Package, Sparkles, TrendingDown, Box, Loader2 } from 'lucide-react';

/**
 * AI Packaging Optimizer (MOCK - Demo UI)
 * 
 * Cyberpunk design with scanning animation
 * Simulates AI-powered 3D bin packing optimization
 */
const AIPackaging = ({ order }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  
  // Product dimensions input
  const [dimensions, setDimensions] = useState({
    length: '',
    width: '',
    height: ''
  });
  
  const isDimensionsValid = dimensions.length && dimensions.width && dimensions.height;
  
  const handleOptimize = async () => {
    if (!isDimensionsValid) return;
    setIsScanning(true);
    setScanProgress(0);
    setResult(null);
    
    // Simulate scanning animation (1.5s)
    const duration = 1500;
    const steps = 30;
    const interval = duration / steps;
    
    let progress = 0;
    const timer = setInterval(() => {
      progress += 100 / steps;
      setScanProgress(Math.min(progress, 100));
      
      if (progress >= 100) {
        clearInterval(timer);
        
        // Generate mock result based on product dimensions
        const productVolume = parseFloat(dimensions.length) * parseFloat(dimensions.width) * parseFloat(dimensions.height);
        
        const boxes = [
          { name: 'S1', dimensions: '15x15x8 cm', volume: 1800, efficiency: 18 },
          { name: 'S2', dimensions: '20x20x10 cm', volume: 4000, efficiency: 22 },
          { name: 'M1', dimensions: '25x25x15 cm', volume: 9375, efficiency: 15 },
          { name: 'M2', dimensions: '30x30x20 cm', volume: 18000, efficiency: 12 },
          { name: 'L1', dimensions: '40x40x25 cm', volume: 40000, efficiency: 8 },
        ];
        
        // Select the smallest box that fits the product
        let selectedBox = boxes[boxes.length - 1]; // Default to largest
        
        for (let i = 0; i < boxes.length; i++) {
          if (boxes[i].volume >= productVolume * 1.1) { // 10% margin
            selectedBox = boxes[i];
            break;
          }
        }
        
        // Calculate real efficiency based on volume usage
        const volumeUsage = (productVolume / selectedBox.volume) * 100;
        const wastedSpace = 100 - volumeUsage;
        const efficiency = Math.min(Math.round(volumeUsage * 0.3), 25); // Max 25% efficiency
        
        setResult({
          ...selectedBox,
          efficiency,
          productDimensions: `${dimensions.length}×${dimensions.width}×${dimensions.height}`,
          volumeUsage: volumeUsage.toFixed(1)
        });
        setIsScanning(false);
      }
    }, interval);
  };
  
  return (
    <Card className="relative overflow-hidden border-2 border-transparent bg-gradient-to-r from-cyan-50 via-purple-50 to-pink-50 dark:from-cyan-950/20 dark:via-purple-950/20 dark:to-pink-950/20">
      {/* Cyberpunk glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-pink-500/10 animate-pulse pointer-events-none" />
      
      <CardContent className="relative p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center shadow-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-purple-600">
                AI Packaging Optimizer
              </h3>
              <p className="text-xs text-gray-500">Powered by 3D Bin Packing Neural Network</p>
            </div>
          </div>
          
        </div>
        
        {/* Product Dimensions Input */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div>
            <label className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1 block">
              Longueur (cm)
            </label>
            <input
              type="number"
              min="1"
              placeholder="ex: 20"
              value={dimensions.length}
              onChange={(e) => setDimensions({...dimensions, length: e.target.value})}
              className="w-full px-3 py-2 rounded-lg border-2 border-cyan-200 dark:border-cyan-700 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-all text-sm"
            />
          </div>
          
          <div>
            <label className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1 block">
              Largeur (cm)
            </label>
            <input
              type="number"
              min="1"
              placeholder="ex: 15"
              value={dimensions.width}
              onChange={(e) => setDimensions({...dimensions, width: e.target.value})}
              className="w-full px-3 py-2 rounded-lg border-2 border-purple-200 dark:border-purple-700 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all text-sm"
            />
          </div>
          
          <div>
            <label className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1 block">
              Hauteur (cm)
            </label>
            <input
              type="number"
              min="1"
              placeholder="ex: 10"
              value={dimensions.height}
              onChange={(e) => setDimensions({...dimensions, height: e.target.value})}
              className="w-full px-3 py-2 rounded-lg border-2 border-pink-200 dark:border-pink-700 focus:border-pink-500 focus:ring-2 focus:ring-pink-500/20 outline-none transition-all text-sm"
            />
          </div>
        </div>
        
        <Button
          onClick={handleOptimize}
          disabled={isScanning || !isDimensionsValid}
          className={`w-full relative overflow-hidden text-white font-semibold shadow-lg border-0 transition-all duration-300 ${
            !isDimensionsValid
              ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
              : 'bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 hover:from-cyan-600 hover:via-purple-600 hover:to-pink-600'
          }`}
        >
          {isScanning ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Scanning...
            </>
          ) : !isDimensionsValid ? (
            <>
              <Sparkles className="w-4 h-4 mr-2 opacity-50" />
              Entrez les dimensions
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              🧠 Optimiser
            </>
          )}
        </Button>
        
        {/* Scanning Animation */}
        {isScanning && (
          <div className="space-y-3 py-4">
            <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 transition-all duration-100 ease-out"
                style={{ width: `${scanProgress}%` }}
              />
            </div>
            
            <div className="grid grid-cols-3 gap-2">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className={`h-16 rounded-lg border-2 flex items-center justify-center transition-all duration-300 ${
                    scanProgress > (i * 16.66) 
                      ? 'border-purple-400 bg-purple-50 dark:bg-purple-900/20' 
                      : 'border-gray-200 bg-gray-50 dark:bg-gray-800'
                  }`}
                >
                  <Box className={`w-6 h-6 transition-colors ${
                    scanProgress > (i * 16.66) ? 'text-purple-500' : 'text-gray-300'
                  }`} />
                </div>
              ))}
            </div>
            
            <p className="text-center text-sm font-medium text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-purple-600 animate-pulse">
              🔍 Analyse des dimensions en cours...
            </p>
          </div>
        )}
        
        {/* Result Display */}
        {result && !isScanning && (
          <div className="mt-4 space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400 font-semibold">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>✅ Optimisation terminée</span>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {/* 3D Box Visualization */}
              <div className="relative h-32 rounded-xl border-2 border-cyan-300 dark:border-cyan-600 bg-gradient-to-br from-cyan-50 to-purple-50 dark:from-cyan-950/30 dark:to-purple-950/30 flex flex-col items-center justify-center overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-purple-500/10" />
                <div className="relative">
                  <div className="w-16 h-16 perspective-1000">
                    <div className="w-full h-full relative transform-style-3d animate-pulse">
                      <Package className="w-16 h-16 text-cyan-600 dark:text-cyan-400" />
                    </div>
                  </div>
                  <div className="mt-2 text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Recommandation</p>
                    <p className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-purple-600">
                      Boîte {result.name}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-300 font-mono">{result.dimensions}</p>
                  </div>
                </div>
              </div>
              
              {/* Efficiency Badge */}
              <div className="relative h-32 rounded-xl border-2 border-green-300 dark:border-green-600 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 flex flex-col items-center justify-center overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10" />
                <div className="relative text-center">
                  <TrendingDown className="w-10 h-10 text-green-600 dark:text-green-400 mx-auto mb-2" />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Espace économisé</p>
                  <p className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-emerald-600">
                    {result.efficiency}%
                  </p>
                  <div className="mt-1 px-3 py-1 bg-green-100 dark:bg-green-900/30 rounded-full inline-block">
                    <p className="text-xs font-semibold text-green-700 dark:text-green-300">
                      💰 Optimal
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="p-3 rounded-lg bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20 border border-blue-200 dark:border-blue-700">
              <p className="text-xs text-blue-700 dark:text-blue-300">
                <strong>💡 Analyse :</strong> Basé sur vos dimensions ({result.productDimensions} cm), l'IA recommande la boîte {result.name}. 
                Taux d'utilisation de l'espace : {result.volumeUsage}%. 
                Cette optimisation réduit les frais de transport aérien de {(result.efficiency * 0.5).toFixed(0)}%.
              </p>
            </div>
          </div>
        )}
        
        {!isScanning && !result && !isDimensionsValid && (
          <div className="mt-4 p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 text-center">
            <Box className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Entrez les dimensions du produit pour obtenir une recommandation AI
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AIPackaging;
