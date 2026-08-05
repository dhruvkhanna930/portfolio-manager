import { Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import Styleguide from './pages/Styleguide'
import ComingSoon from './pages/ComingSoon'
import Portfolio from './pages/Portfolio'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<ComingSoon title="Home" />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/stocks" element={<ComingSoon title="Stocks" />} />
        <Route path="/mutual-funds" element={<ComingSoon title="Mutual Funds" />} />
        <Route path="/bonds" element={<ComingSoon title="Bonds" />} />
        <Route path="/styleguide" element={<Styleguide />} />
      </Route>
    </Routes>
  )
}

export default App
