import { Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import Styleguide from './pages/Styleguide'
import Calculators from './pages/Calculators'
import Home from './pages/Home'
import Portfolio from './pages/Portfolio'
import Transactions from './pages/Transactions'
import AssetTypePage from './pages/AssetTypePage'
import AssetDetail from './pages/AssetDetail'
import Sips from './pages/Sips'
import News from './pages/News'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route
          path="/stocks"
          element={
            <AssetTypePage assetType="STOCK" title="Stocks" description="Your equity holdings." />
          }
        />
        <Route
          path="/mutual-funds"
          element={
            <AssetTypePage
              assetType="MUTUAL_FUND"
              title="Mutual Funds"
              description="Your mutual fund holdings."
            />
          }
        />
        <Route
          path="/bonds"
          element={
            <AssetTypePage
              assetType="BOND"
              title="Bonds"
              description="Your bond holdings, manually priced."
              canBuy={false}
            />
          }
        />
        <Route path="/asset/:assetId" element={<AssetDetail />} />
        <Route path="/calculators" element={<Calculators />} />
        <Route path="/sips" element={<Sips />} />
        <Route path="/news" element={<News />} />
        <Route path="/styleguide" element={<Styleguide />} />
      </Route>
    </Routes>
  )
}

export default App
