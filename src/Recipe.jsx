import React, { useState, useEffect } from 'react';

// This helper function correctly parses all sections, creating a rich structure for instructions.
function parseRecipeText(text) {
  const structured = {
    name: '',
    servings: '',
    ingredients: [],
    instructions: [],
    notes: [],
  };

  if (!text) return structured;

  const lines = text.split('\n');
  let currentSection = 'name';
  let currentInstruction = null;

  lines.forEach(line => {
    const trimmedLine = line.trim();
    if (!trimmedLine || trimmedLine === '---') return;

    const lineLower = trimmedLine.toLowerCase();

    // Identify and switch sections
    if (lineLower.startsWith('servings:')) {
      currentSection = 'servings';
      structured.servings = trimmedLine.split(':')[1]?.trim() || '';
      return;
    }
    if (lineLower.startsWith('ingredients:')) {
      currentSection = 'ingredients';
      return;
    }
    if (lineLower.startsWith('step-by-step cooking instructions:')) {
      currentSection = 'instructions';
      return;
    }
    if (lineLower.startsWith('🍲 tips & notes:')) {
      currentSection = 'notes';
      return;
    }

    // Add the line to the correct section
    switch (currentSection) {
      case 'name':
        if (!structured.name) structured.name = trimmedLine.replace(/^\d+\.\s*/, '');
        break;
      case 'ingredients':
        structured.ingredients.push(trimmedLine.replace(/^[*-]\s*/, ''));
        break;
      case 'instructions':
        if (/^\d+\.\s*/.test(trimmedLine)) {
          currentInstruction = { title: trimmedLine, details: [] };
          structured.instructions.push(currentInstruction);
        } else if (currentInstruction) {
          currentInstruction.details.push(trimmedLine);
        }
        break;
      case 'notes':
        structured.notes.push(trimmedLine.replace(/^[*-]\s*/, ''));
        break;
      default:
        break;
    }
  });

  return structured;
}

function Recipe({ recipeName, onBack }) {
  const [structuredRecipe, setStructuredRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!recipeName) return;

    const fetchRecipeData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:5000/api/getRecipeByDish?recipe_val=${encodeURIComponent(recipeName)}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.steps) {
          const parsedData = parseRecipeText(data.steps);
          setStructuredRecipe(parsedData);
        } else {
          throw new Error("API did not return valid recipe steps.");
        }
      } catch (e) {
        console.error("Failed to fetch recipe:", e);
        setError('Failed to load recipe steps.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecipeData();
  }, [recipeName]);

  const renderContent = () => {
    if (loading) return <p className="loading-text">Generating your recipe steps...</p>;
    if (error) return <p className="error-text">{error}</p>;
    if (!structuredRecipe) return <p>No recipe data found.</p>;

    return (
      <div className="recipe-details">
        <h3>Ingredients:</h3>
        {/* Renders ingredients as a simple bulleted list */}
        <ul>
          {(structuredRecipe.ingredients || []).map((item, index) => <li key={index}>{item}</li>)}
        </ul>

        <h3>Step-by-Step Cooking Instructions:</h3>
        {/* Renders instructions as a numbered list with titles and paragraphs */}
        <ol>
          {(structuredRecipe.instructions || []).map((step, index) => (
            <li key={index} style={{ marginBottom: '1em' }}>
              <strong>{step.title.replace(/^\d+\.\s*/, '')}</strong>
              <p style={{ margin: '0.5em 0 0 0' }}>{step.details.join(' ')}</p>
            </li>
          ))}
        </ol>
        
        {structuredRecipe.notes && structuredRecipe.notes.length > 0 && (
          <>
            <h3>🍲 Tips & Notes:</h3>
            <ul>
              {(structuredRecipe.notes || []).map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </>
        )}
      </div>
    );
  };

  return (
    <>
      <div className="header">
        <h1>{structuredRecipe ? structuredRecipe.name : recipeName}</h1>
        <button className="back-link" onClick={onBack}>← Back to List</button>
      </div>
      <div className="card">
        {structuredRecipe && <p><strong>Servings:</strong> {structuredRecipe.servings}</p>}
        {renderContent()}
      </div>
    </>
  );
}

export default Recipe;