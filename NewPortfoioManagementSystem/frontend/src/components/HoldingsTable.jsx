import React from 'react';
import '../styles/HoldingsTable.css';

function HoldingsTable({ holdings }) {
  const formatCurrency = (value) => {
    return `$${value.toFixed(2)}`;
  };

  return (
    <div className="holdings-table-container">
      <h3 className="table-title">Your Holdings</h3>
      <table className="holdings-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Company</th>
            <th>Shares</th>
            <th>Price</th>
            <th>Value</th>
            <th>Change</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => (
            <tr key={holding.symbol}>
              <td className="symbol">{holding.symbol}</td>
              <td className="name">{holding.name}</td>
              <td className="shares">{holding.shares}</td>
              <td className="price">{formatCurrency(holding.price)}</td>
              <td className="value">{formatCurrency(holding.value)}</td>
              <td className={`change ${holding.change >= 0 ? 'positive' : 'negative'}`}>
                {holding.change >= 0 ? '+' : ''}{holding.change.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default HoldingsTable;
