import { lazy, Suspense } from 'react'
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
import Analytics from './pages/Analytics'
import Goals from './pages/Goals'


// The report is a separate destination, not part of normal navigation -- keep
// it out of the main bundle.
const Report = lazy(() => import('./pages/Report'))

function App() {
  return (
    <Routes>
      {/* Outside AppLayout on purpose -- the report is a document, so it
          carries no navbar or page chrome (§15.6). */}
      <Route
        path="/report"
        element={
          <Suspense fallback={null}>
            <Report />
          </Suspense>
        }
      />
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
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/styleguide" element={<Styleguide />} />
      </Route>
    </Routes>
  )
}

export default App
