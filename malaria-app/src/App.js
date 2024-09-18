import React, { useState } from 'react';

function App() {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('No file chosen');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (selectedFile) {
      const fileExtension = selectedFile.name.split('.').pop().toLowerCase();

      if (fileExtension !== 'dcm') {
        setError('Invalid file format. Please upload a DICOM (.dcm) file.');
        setFile(null);
        setFileName('No file chosen');
        return;
      }

      setFile(selectedFile);
      setFileName(selectedFile.name);
      setError('');
    } else {
      setFileName('No file chosen');
      setError('');
    }
  };

  const handleUpload = () => {
    if (!file) {
      setError('Please choose a file before uploading.');
      return;
    }
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);

    fetch('http://127.0.0.1:5000/upload', {
      method: 'POST',
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        analyzeImage(data.filepath);
      })
      .catch((error) => {
        console.error('Error uploading file:', error);
        setLoading(false);
        setError('Error uploading file. Please try again.');
      });
  };

  const analyzeImage = (filepath) => {
    fetch('http://127.0.0.1:5000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ filepath }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.total_cell_count !== undefined) {
          setResults(data);
        } else {
          console.error('Analysis failed:', data.error);
          setError('Analysis failed. Please try again.');
        }
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error analysing image:', error);
        setLoading(false);
        setError('Error analysing image. Please try again.');
      });
  };

  return (
    <div className="App container mt-5">
      <h1 className="text-center mb-4">Malaria Detection App</h1>
      
      <div className="d-flex justify-content-center align-items-center mb-4">
        <div className="me-3">
          <label htmlFor="fileInput" className="btn btn-primary">
            Choose File
          </label>
          <input
            type="file"
            id="fileInput"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <span className="file-name text-secondary ms-2">{fileName}</span>
        </div>
      </div>

      <div className="text-center">
        <button type="button" className="btn btn-success mb-3" onClick={handleUpload}>
          Upload and Analyse
        </button>
      </div>

      {error && (
        <div className="alert alert-danger text-center" role="alert">
          {error}
        </div>
      )}

      {loading && (
        <div className="alert alert-info text-center" role="alert">
          Analysis is loading, please wait...
        </div>
      )}

      {results && (
        <div className="text-center">
          <div className="row justify-content-center mb-4">
            <div className="col-md-3">
              <div className="card border-primary mb-3" style={{ maxWidth: '20rem' }}>
                <div className="card-header">Total Cell Count</div>
                <div className="card-body">
                  <p className="card-text">{results.total_cell_count}</p>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card border-primary mb-3" style={{ maxWidth: '20rem' }}>
                <div className="card-header">Infected Cell Count</div>
                <div className="card-body">
                  <p className="card-text">{results.infected_cell_count}</p>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card border-primary mb-3" style={{ maxWidth: '20rem' }}>
                <div className="card-header">Prediction</div>
                <div className="card-body">
                  <p className="card-text">{results.patient_status}</p>
                </div>
              </div>
            </div>
          </div>
          <h4>Initial Image:</h4>
          <img
            src={`http://127.0.0.1:5000/display_image/${results.initial_image_path.split('/').pop()}`}
            alt="Initial DICOM scan"
            className="img-fluid"
          />
          <h4>Processed Image:</h4>
          <img
            src={`http://127.0.0.1:5000/display_image/${results.processed_image_path.split('/').pop()}`}
            alt="Processed analysis results"
            className="img-fluid"
          />
        </div>
      )}
    </div>
  );
}

export default App;
