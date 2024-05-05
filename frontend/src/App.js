import React, { useState } from 'react';
import axios from 'axios';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCopy } from '@fortawesome/free-solid-svg-icons';
import 'bulma/css/bulma.min.css';

function App() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [procedures, setProcedures] = useState([]);
  const [selectedProcedures, setSelectedProcedures] = useState(new Set());
  const [sigmaRules, setSigmaRules] = useState([]);


  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5050';

  const extractProcedures = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${backendUrl}/api/extract_procedures`, { 'procedures': input });
      const data = JSON.parse(response.data.procedures);
      setProcedures(data);
      setSelectedProcedures(new Set()); // Reset selections upon new data
    } catch (err) {
      console.error('Failed to extract procedures:', err);
      alert('Failed to extract procedures. Please try again.');
    } finally {
      console.log('Finished extracting procedures.');
      setIsLoading(false);
    }
  };

  const handleProcedureCheck = (index) => {
    // Using a Set for easy add/remove and check for existence
    const newSelections = new Set(selectedProcedures);
    if (newSelections.has(index)) {
      newSelections.delete(index);
    } else {
      newSelections.add(index);
    }
    setSelectedProcedures(newSelections);
  };

  const generateSigmaRules = async () => {
    const rulesToGenerate = [...selectedProcedures].map(index => procedures[index].description);
    const fetchedSigmaRules = await Promise.all(rulesToGenerate.map(async (procedure) => {
      try {
        const response = await axios.post('http://localhost:5050/api/sigma_rule', { 'procedure': procedure });
        return response.data.sigma_rule;
      } catch (err) {
        console.error('Failed to generate Sigma rule for:', procedure, err);
        return `Failed rule generation for: ${procedure}`;
      }
    }));
    setSigmaRules(fetchedSigmaRules);
  };

  return (
    <section className="section">
      <div className="container">
        <h1 className="title">SigGen</h1>
        <div className="field has-addons">
          <div className="control is-expanded">
            <input
              className="input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter Procedure or URL"
              disabled={isLoading} // Disable input when loading
            />
          </div>
          <div className="control">
            <button className="button is-info" onClick={extractProcedures} disabled={isLoading}>
              {isLoading ? 'Extracting...' : 'Extract'}
            </button>
          </div>
        </div>
        {procedures.length > 0 && (
          <>
            <div className="box">
              <table className="table is-striped is-fullwidth">
                <thead>
                  <tr>
                    <th>Select</th> {/* Added heading for select column */}
                    <th>Technique</th>
                    <th>Description</th>
                    <th>Quality Score</th>
                    <th>Analysis</th>
                  </tr>
                </thead>
                <tbody>
                  {procedures.map((proc, index) => (
                    <tr key={index}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedProcedures.has(index)}
                          onChange={() => handleProcedureCheck(index)}
                        />
                      </td>
                      <td>{proc.technique}</td>
                      <td>{proc.description}</td>
                      <td>{proc.quality_score}</td>
                      <td>{proc.analysis}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button className="button is-primary" onClick={generateSigmaRules}>Generate Sigma Rules</button>
          </>
        )}
        {sigmaRules.length > 0 && (
          <div>
            {sigmaRules.map((rule, index) => (
              <div key={index} style={{ position: 'relative' }}> {/* Wrap with a div to position the copy button */}
                <SyntaxHighlighter language="yaml" style={materialDark}>
                  {rule}
                </SyntaxHighlighter>
                <button
                  style={{
                    position: 'absolute',
                    top: '5px', // Adjust these values based on your needs 
                    right: '5px',
                    cursor: 'pointer'
                  }}
                  className="button is-medium" // Adjust button size accordingly
                  onClick={() => navigator.clipboard.writeText(rule)}
                  title="Copy to clipboard"
                >
                  <FontAwesomeIcon icon={faCopy} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default App;