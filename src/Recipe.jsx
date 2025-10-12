import React, { useState, useEffect } from 'react';

// This helper function correctly parses all sections, creating a rich structure for instructions.
function parseRecipeText(text) {
  const structured = {
    name: '',
    servings: '',
    allergens: '', // New field for allergens
    ingredients: [],
    instructions: [],
    notes: [],
    reference: '', // New field for reference
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
    // New location for Allergens
    if (lineLower.startsWith('allergens:')) {
      currentSection = 'allergens';
      structured.allergens = trimmedLine.split(':')[1]?.trim() || '';
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
    // Capture New section for Reference. It must be treated like servings/allergens.
    if (lineLower.startsWith('reference:')) {
        currentSection = 'reference';
        structured.reference = trimmedLine.split(':')[1]?.trim() || '';
        return;
    }

    // Add the line to the correct section
    switch (currentSection) {
      case 'name':
        // Only capture the first line as the name/description header
        if (!structured.name) structured.name = trimmedLine.replace(/^\d+\.\s*/, '');
        break;
      case 'ingredients':
        structured.ingredients.push(trimmedLine.replace(/^[*-]\s*/, ''));
        break;
      case 'instructions':
        if (/^\d+\.\s*/.test(trimmedLine)) {
          // If it starts with a number, it's a new step title
          currentInstruction = { title: trimmedLine, details: [] };
          structured.instructions.push(currentInstruction);
        } else if (currentInstruction) {
          // Otherwise, it's a detail of the current step
          currentInstruction.details.push(trimmedLine);
        }
        break;
      case 'notes':
        structured.notes.push(trimmedLine.replace(/^[*-]\s*/, ''));
        break;
      // 'servings', 'allergens', and 'reference' are handled by their starting lines
      default:
        break;
    }
  });

  return structured;
}

// Helper to parse the LLM's requested format: URL (Website Title)
// FIX: Simplified to check only for a raw URL
function parseReference(refString) {
    if (!refString) return { url: null, raw: null };

    const trimmedRef = refString.trim();
    
    // Check if the trimmed string starts with a common URL prefix
    if (trimmedRef.startsWith('http')) {
        // Return the whole trimmed string as the URL, ignoring any trailing titles in parenthesis
        // We look for a parenthesis and strip everything after it, to be safe.
        const urlEndIndex = trimmedRef.indexOf('(');
        const url = urlEndIndex !== -1 ? trimmedRef.substring(0, urlEndIndex).trim() : trimmedRef;
        return { url: url, raw: trimmedRef };
    }

    // If not a URL, return the whole string as raw text
    return { url: null, raw: trimmedRef };
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
    
    // Parse the reference string here
    const referenceData = parseReference(structuredRecipe.reference);


    return (
      <div className="recipe-details">

        {/* Servings and Allergens info box */}
        <div className="servings-allergens-info">
            <p><strong>Servings:</strong> {structuredRecipe.servings || 'N/A'}</p>
            <p className="allergens-text"><strong>⚠️ Allergens:</strong> {structuredRecipe.allergens || 'None specified'}</p>
        </div>
        

        <div className="recipe-section-box">
          <h3>Ingredients:</h3>
          <ul>
            {(structuredRecipe.ingredients || []).map((item, index) => <li key={index}>{item}</li>)}
          </ul>
        </div>

        <div className="recipe-section-box">
          <h3>Step-by-Step Cooking Instructions:</h3>
          <ol>
            {(structuredRecipe.instructions || []).map((step, index) => (
              <li key={index} style={{ marginBottom: '1em' }}>
                <strong>{step.title.replace(/^\d+\.\s*/, '')}</strong>
                <p style={{ margin: '0.5em 0 0 0' }}>{step.details.join(' ')}</p>
              </li>
            ))}
          </ol>
        </div>
        
        {structuredRecipe.notes && structuredRecipe.notes.length > 0 && (
          <div className="recipe-section-box">
            <h3>🍲 Tips & Notes:</h3>
            <ul>
              {(structuredRecipe.notes || []).map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </div>
        )}
        
        {/* New Reference Section Rendering */}
        {(referenceData.url || referenceData.raw) && (
            <div className="recipe-section-box reference-section">
                <h3>Reference:</h3>
                <p style={{ margin: 0, fontSize: '0.95em' }}>
                    {/* Render Title and Link if structure is found */}
                    {referenceData.url ? (
                        <a href={referenceData.url} target="_blank" rel="noopener noreferrer" className="reference-link">
                            {/* FIX: Display only the URL string */}
                            {referenceData.url} 
                        </a>
                    ) : (
                        /* Otherwise, render raw text */
                        referenceData.raw
                    )}
                </p>
            </div>
        )}
        
      </div>
    );
  };

  return (
    <>
      <div className="header">
        <h1 className="dish-name-title">{structuredRecipe ? structuredRecipe.name : recipeName}</h1>
        <button className="back-link" onClick={onBack}>← Back to List</button>
      </div>
      <div className="card">
        {renderContent()}
      </div>
    </>
  );
}

export default Recipe;
