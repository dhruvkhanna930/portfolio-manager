import React from 'react';
import '../styles/PortfolioChart.css';

function PortfolioChart({ holdings }) {
  const totalValue = holdings.reduce((sum, h) => sum + h.value, 0);

  const chartData = holdings.map(h => ({
    symbol: h.symbol,
    percentage: ((h.value / totalValue) * 100).toFixed(1),
    value: h.value,
    color: getColorForIndex(holdings.indexOf(h))
  }));

  function getColorForIndex(index) {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];
    return colors[index % colors.length];
  }

  return (
    <div className="portfolio-chart-container">
      <h3 className="chart-title">Portfolio Allocation</h3>
      <div className="chart-content">
        <div className="pie-chart">
          {chartData.map((item, index) => (
            <div
              key={item.symbol}
              className="chart-segment"
              style={{
                width: item.percentage + '%',
                backgroundColor: item.color
              }}
              title={`${item.symbol}: ${item.percentage}%`}
            ></div>
          ))}
        </div>
        <div className="chart-legend">
          {chartData.map((item) => (
            <div key={item.symbol} className="legend-item">
              <span
                className="legend-color"
                style={{ backgroundColor: item.color }}
              ></span>
              <span className="legend-text">
                {item.symbol}: {item.percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default PortfolioChart;
