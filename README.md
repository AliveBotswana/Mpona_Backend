WHAT IS NEW: 
- clinic segregation
- specialist able to add comments
- peer to peer messaging between users
- statistics (though i am not sure if this is fully optimised)
- remidio integration etc 

CODE STRUCTURE: Mpona_Backend/

├── .gitignore
├── buildspec.yml
├── Dockerfile
├── package.json
├── package-lock.json
├── tsconfig.json
├── function_app.py
├── src/
│   ├── appStore/
│   │   ├── index.ts
│   │   ├── axiosInstance.ts
│   │   ├── slices/
│   │   │   ├── authSlice.ts
│   ├── components/
│   │   ├── Logo.tsx
│   │   ├── FilePreview.tsx
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Patients.tsx
│   │   ├── PatientDetails.tsx
│   │   ├── Bookings.tsx
│   │   ├── Reports.tsx
│   │   ├── Images.tsx
│   │   ├── Messaging.tsx
│   │   ├── Users.tsx
│   │   ├── ExternalReports.tsx
│   ├── types/
│   │   ├── index.tsx
│   │   ├── Booking.tsx
│   │   ├── Department.tsx
│   │   ├── Doctor.tsx
│   │   ├── Hospital.tsx
│   │   ├── MedCondition.tsx
│   │   ├── Medication.tsx
│   │   ├── Patient.tsx
│   │   ├── PatientVisit.tsx
│   │   ├── Role.tsx
│   │   ├── User.tsx
│   │   ├── Visit.tsx
│   ├── utils/
│   │   ├── index.tsx
│   │   ├── filterBookings.tsx
│   │   ├── filterExpiredBookings.tsx
│   │   ├── filterVisits.tsx
│   │   ├── formatDate.tsx
│   │   ├── removeResolvedBookings.tsx
│   │   ├── useDrap.tsx
│   │   ├── useToggle.tsx
│   ├── App.tsx
│   ├── index.tsx
