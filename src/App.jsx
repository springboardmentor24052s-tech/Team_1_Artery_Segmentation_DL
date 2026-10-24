import { useEffect, useMemo, useState } from "react";
import AppLayout from "./components/AppLayout.jsx";
import { DEMO_CASES, readSavedCases, STORAGE_KEY } from "./data/cases.js";
import { pageFromPath } from "./data/navigation.js";
import DashboardPage from "./pages/DashboardPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ResultsPage from "./pages/ResultsPage.jsx";
import UploadPage from "./pages/UploadPage.jsx";
import UsersPage from "./pages/UsersPage.jsx";

function App() {
  const [page, setPage] = useState(() => pageFromPath(window.location.pathname));
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [localCases, setLocalCases] = useState(readSavedCases);
  const cases = useMemo(() => [...localCases, ...DEMO_CASES], [localCases]);

  useEffect(() => {
    const handlePopState = () => setPage(pageFromPath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigate(nextPage, query = "") {
    const path = `/${nextPage}${query}`;
    window.history.pushState({}, "", path);
    setPage(nextPage);
    setMobileNavOpen(false);
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  function saveCase(record) {
    const updated = [record, ...localCases];
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error("Could not save the case in browser storage.", error);
      return "Could not save this case in browser storage. Check available storage and try again.";
    }
    setLocalCases(updated);
    return "";
  }

  if (page === "login") return <LoginPage navigate={navigate} />;

  const content = {
    dashboard: <DashboardPage cases={cases} navigate={navigate} />,
    upload: <UploadPage cases={cases} onSave={saveCase} />,
    results: <ResultsPage navigate={navigate} />,
    users: <UsersPage />,
  }[page] || <DashboardPage cases={cases} navigate={navigate} />;

  return <AppLayout page={page} navigate={navigate} mobileNavOpen={mobileNavOpen} setMobileNavOpen={setMobileNavOpen}>
    {content}
  </AppLayout>;
}

export default App;
