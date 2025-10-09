import React, { useState } from "react";
import Camera from "./Camera";
import RecipeList from './RecipeList';
import Recipe from './Recipe';
import "./App.css";

function App() {
  const [view, setView] = useState('camera');
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleShowRecipes = async () => {
    setLoading(true);
    setError(null);
    try {
      // FIX: Use the correct API endpoint '/getRecipeByInd'
      // For now, it will use the default ingredients in the API.
       const response = await fetch('http://localhost:5000/api/getRecipeByInd');
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      const data = await response.json();
      
      // FIX: The API returns an object like { recipes: [...] }. We need to get the array from data.recipes.
      if (data.recipes && data.recipes.length > 0) {
        setRecipes(data.recipes);
        setView('list');
      } else {
        throw new Error("No recipes returned. Please try again or check the backend logs.");
      }

    } catch (e) {
      setError('Failed to load recipes. Is the Python API server running?');
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRecipe = (recipeName) => {
    setSelectedRecipe(recipeName);
    setView('steps');
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedRecipe(null);
  };
  
  const handleBackToCamera = () => {
    setView('camera');
    setRecipes([]);
  }

  const renderContent = () => {
    if (loading) {
      return <p className="loading-text">Finding the best recipes for you...</p>;
    }
    
    if (error) {
       return (
        <div style={{textAlign: 'center'}}>
          <p className="error-text">{error}</p>
          <button className="random-button" onClick={() => setView('camera')}>Try Again</button>
        </div>
       );
    }

    switch (view) {
      case 'list':
        return <RecipeList recipes={recipes} onSelectRecipe={handleSelectRecipe} onBack={handleBackToCamera} />;
      case 'steps':
        return <Recipe recipeName={selectedRecipe} onBack={handleBackToList} />;
      case 'camera':
      default:
        return (
          <>
            <h1 style={{ textAlign: "center" }}>Show an Ingredient</h1>
            <Camera />
            <button className="random-button" onClick={handleShowRecipes}>
              Show Recipe
            </button>
          </>
        );
    }
  };

  return <div className="app-container">{renderContent()}</div>;
}

export default App;
