import { Button, Field, inputClass } from "../components/ui.jsx";
import "./LoginPage.css";

export default function LoginPage({ navigate }) {
  return <div className="login-page">
    <section className="login-brand-panel"><div className="login-brand"><span className="login-brand__mark">S</span><span>StenoVision</span></div><div className="login-brand-copy"><p>Medical imaging workspace</p><h1>A clearer view of every case.</h1><p>Artery segmentation and stenosis detection using advanced deep learning techniques.</p></div><p className="login-brand-footer">Student research prototype · Local demo</p></section>
    <section className="login-form-panel"><div className="login-form">
      <div className="login-mobile-brand"><p>StenoVision</p><p>Medical Imaging Workspace</p></div>
      <p className="login-welcome">Welcome back</p><h2>Sign in to your account</h2><p className="login-description">Enter your details below to continue.</p>
      <form className="login-fields" onSubmit={(event) => { event.preventDefault(); navigate("dashboard"); }}>
        <Field label="Email address"><input className={inputClass} type="email" placeholder="name@example.com" required /></Field>
        <Field label="Password"><input className={inputClass} type="password" placeholder="Enter password" minLength="4" required /></Field>
        <div className="login-options"><label><input type="checkbox" />Remember me</label><button type="button" onClick={() => window.alert("Password recovery is not implemented in this UI demo.")}>Forgot password?</button></div>
        <Button className="button--full">Sign in</Button>
      </form><p className="login-disclaimer">Demo only; no credentials are stored or sent.</p>
    </div></section>
  </div>;
}
