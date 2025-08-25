import React from 'react';
     import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
     import Login from './pages/Login';
     import Dashboard from './pages/Dashboard';
     import Patients from './pages/Patients';
     import PatientDetails from './pages/PatientDetails';
     import Bookings from './pages/Bookings';
     import Reports from './pages/Reports';
     import Images from './pages/Images';
     import Messaging from './pages/Messaging';
     import Users from './pages/Users';
     import ExternalReports from './pages/ExternalReports';

     const App = () => {
       return (
         <Router>
           <Routes>
             <Route path="/" element={<Login />} />
             <Route path="/dashboard" element={<Dashboard />} />
             <Route path="/patients" element={<Patients />} />
             <Route path="/patient/:mrn" element={<PatientDetails />} />
             <Route path="/bookings" element={<Bookings />} />
             <Route path="/reports" element={<Reports />} />
             <Route path="/images" element={<Images />} />
             <Route path="/messaging" element={<Messaging />} />
             <Route path="/users" element={<Users />} />
             <Route path="/external-reports" element={<ExternalReports />} />
           </Routes>
         </Router>
       );
     };

     export default App;