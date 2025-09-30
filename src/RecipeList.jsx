import React from 'react';

// This component displays a single recipe item in the list
function RecipeItem({ recipe, onSelectRecipe }) {
  return (
    <div className="recipe-item">
      <h2>
        <button className="view-steps-btn" onClick={() => onSelectRecipe(recipe.name)}>
          View Steps
        </button>
        {recipe.name}
      </h2>
      <p>{recipe.description}</p>
    </div>
  );
}

// This component displays the entire list of 5 recipes
function RecipeList({ recipes, onSelectRecipe, onBack }) {
  return (
    <div className="recipe-list-container">
       <div className="header">
        <h1>Top Filipino Recipes</h1>
        <button className="back-link" onClick={onBack}>← Back to Camera</button>
      </div>
      {recipes.map((recipe, index) => (
        <RecipeItem key={index} recipe={recipe} onSelectRecipe={onSelectRecipe} />
      ))}
    </div>
  );
}

export default RecipeList;