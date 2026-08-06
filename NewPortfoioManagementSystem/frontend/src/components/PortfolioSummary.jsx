import React from 'react';
import '../styles/PortfolioSummary.css';

function PortfolioSummary({ data }) {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const gainClassName = data.gainPercentage >= 0 ? 'gain-positive' : 'gain-negative';

  return (
    <div className="portfolio-summary">
      <div className="summary-card total-value">
        <h3 className="card-label">Total Portfolio Value</h3>
        <p className="card-value">{formatCurrency(data.totalValue)}</p>
        <p className="card-meta">As of today</p>
      </div>

      <div className="summary-card invested">
        <h3 className="card-label">Total Invested</h3>
        <p className="card-value">{formatCurrency(data.totalInvested)}</p>
        <p className="card-meta">Principal amount</p>
      </div>

      <div className="summary-card gain">
        <h3 className="card-label">Unrealized Gain/Loss</h3>
        <p className={`card-value ${gainClassName}`}>
          {formatCurrency(data.unrealizedGain)}
        </p>
        <p className={`card-meta ${gainClassName}`}>
          {data.gainPercentage >= 0 ? '+' : ''}{data.gainPercentage.toFixed(2)}%
        </p>
      </div>

      <div className="summary-card holdings">
        <h3 className="card-label">Holdings</h3>
        <p className="card-value">3</p>
        <p className="card-meta">Active positions</p>
      </div>
    </div>
  );
}

export default PortfolioSummary;
