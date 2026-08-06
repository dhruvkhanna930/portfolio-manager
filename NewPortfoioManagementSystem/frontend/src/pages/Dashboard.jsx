import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import PortfolioSummary from '../components/PortfolioSummary';
import HoldingsTable from '../components/HoldingsTable';
import PortfolioChart from '../components/PortfolioChart';
import '../styles/Dashboard.css';

function Dashboard() {
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API endpoint
      const mockData = {
        totalValue: 125000,
        totalInvested: 100000,
        unrealizedGain: 25000,
        gainPercentage: 25.0,
        holdings: [
          { symbol: 'AAPL', name: 'Apple Inc.', shares: 50, price: 150, value: 7500, change: 2.5 },
          { symbol: 'GOOGL', name: 'Alphabet Inc.', shares: 30, price: 140, value: 4200, change: -1.2 },
          { symbol: 'MSFT', name: 'Microsoft Corp.', shares: 40, price: 350, value: 14000, change: 3.1 },
        ]
      };
      setPortfolioData(mockData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch portfolio data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="dashboard-loading">Loading portfolio...</div>;
  if (error) return <div className="dashboard-error">{error}</div>;

  return (
    <div className="dashboard">
      <Header />
      <main className="dashboard-main">
        <div className="container">
          <div className="dashboard-header">
            <h1>Portfolio Dashboard</h1>
            <button
              onClick={fetchPortfolioData}
              disabled={loading}
              className="refresh-btn"
              title="Refresh portfolio data"
            >
              {loading ? 'Refreshing...' : '🔄 Refresh'}
            </button>
          </div>
          <PortfolioSummary data={portfolioData} />
          <div className="dashboard-grid">
            <div className="dashboard-chart">
              <PortfolioChart holdings={portfolioData.holdings} />
            </div>
            <div className="dashboard-holdings">
              <HoldingsTable holdings={portfolioData.holdings} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
