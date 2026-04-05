import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useEffect } from 'react';
import Fingerprint from './pages/Fingerprint';
import Login from './pages/Login';
import Result from './pages/Result';
import Voting from './pages/Voting';

function RequireEpic({ children }) {
  const epic = localStorage.getItem('epic');

  if (!epic) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function App() {
  useEffect(() => {
    // Ensure old vote responses are not reused across fresh booth sessions.
    localStorage.removeItem('voteResult');
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route
          path="/fingerprint"
          element={(
            <RequireEpic>
              <Fingerprint />
            </RequireEpic>
          )}
        />
        <Route
          path="/voting"
          element={(
            <RequireEpic>
              <Voting />
            </RequireEpic>
          )}
        />
        <Route
          path="/result"
          element={(
            <RequireEpic>
              <Result />
            </RequireEpic>
          )}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;